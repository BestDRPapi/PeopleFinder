"""
Main PeopleFinder application for searching people across BlueIris cameras.
"""

import argparse
import configparser
import logging
import sys
import time
from typing import List, Dict, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import json

from blueiris_api import BlueIrisAPI
from face_detector import FaceDetector, MockFaceDetector, FACE_RECOGNITION_AVAILABLE

class PeopleFinder:
    """Main application class for finding people in BlueIris cameras."""
    
    def __init__(self, config_file: str = "config.ini"):
        """
        Initialize PeopleFinder application.
        
        Args:
            config_file: Path to configuration file
        """
        self.config = configparser.ConfigParser()
        self.config.read(config_file)
        
        # Setup logging
        self._setup_logging()
        
        # Initialize logger after logging setup
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.blueiris_api = self._init_blueiris_api()
        self.face_detector = self._init_face_detector()
        
    def _setup_logging(self):
        """Setup logging configuration."""
        log_level = self.config.get('logging', 'level', fallback='INFO')
        log_file = self.config.get('logging', 'file', fallback='')
        
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file) if log_file else logging.StreamHandler(),
                logging.StreamHandler()  # Always log to console as well
            ]
        )
        
    def _init_blueiris_api(self) -> BlueIrisAPI:
        """Initialize BlueIris API client."""
        server_url = self.config.get('blueiris', 'server_url', fallback='http://localhost:81')
        username = self.config.get('blueiris', 'username', fallback='admin')
        password = self.config.get('blueiris', 'password', fallback='')
        timeout = self.config.getint('blueiris', 'connection_timeout', fallback=10)
        
        return BlueIrisAPI(server_url, username, password, timeout)
        
    def _init_face_detector(self) -> 'FaceDetector':
        """Initialize face detector."""
        tolerance = self.config.getfloat('face_recognition', 'tolerance', fallback=0.6)
        scale_factor = self.config.getfloat('face_recognition', 'scale_factor', fallback=0.25)
        
        if FACE_RECOGNITION_AVAILABLE:
            return FaceDetector(tolerance, scale_factor)
        else:
            # Use logger from module level since instance logger not yet set
            logger = logging.getLogger(__name__)
            logger.warning("Face recognition libraries not available, using mock detector")
            return MockFaceDetector(tolerance, scale_factor)
        
    def search_person_in_camera(self, reference_encoding, camera_info: Dict) -> Dict:
        """
        Search for person in a single camera.
        
        Args:
            reference_encoding: Reference face encoding to search for
            camera_info: Camera information dictionary
            
        Returns:
            Dictionary with search results for this camera
        """
        camera_name = camera_info.get('optionValue', camera_info.get('name', 'Unknown'))
        
        result = {
            'camera_name': camera_name,
            'camera_info': camera_info,
            'person_found': False,
            'face_locations': [],
            'face_distances': [],
            'error': None,
            'timestamp': time.time()
        }
        
        try:
            self.logger.debug(f"Checking camera: {camera_name}")
            
            # Get image from camera
            image_bytes = self.blueiris_api.get_camera_image(camera_name)
            
            if not image_bytes:
                result['error'] = "Failed to get image from camera"
                return result
                
            # Search for person in image
            person_found, face_locations = self.face_detector.is_person_in_image(reference_encoding, image_bytes)
            face_distances = self.face_detector.get_face_distance(reference_encoding, image_bytes)
            
            result.update({
                'person_found': person_found,
                'face_locations': face_locations,
                'face_distances': face_distances
            })
            
            if person_found:
                self.logger.info(f"✓ Person found in camera: {camera_name}")
            else:
                self.logger.debug(f"✗ Person not found in camera: {camera_name}")
                
        except Exception as e:
            error_msg = f"Error searching camera {camera_name}: {e}"
            self.logger.error(error_msg)
            result['error'] = str(e)
            
        return result
        
    def search_person_all_cameras(self, reference_image_path: str, max_workers: int = 5) -> List[Dict]:
        """
        Search for person across all active cameras.
        
        Args:
            reference_image_path: Path to reference image of person to find
            max_workers: Maximum number of concurrent camera checks
            
        Returns:
            List of search results for each camera
        """
        self.logger.info(f"Starting person search with reference image: {reference_image_path}")
        
        # Load reference image
        reference_encoding = self.face_detector.load_reference_image(reference_image_path)
        if reference_encoding is None:
            self.logger.error("Failed to load or process reference image")
            return []
            
        # Get active cameras
        self.logger.info("Getting list of active cameras...")
        active_cameras = self.blueiris_api.get_active_cameras()
        
        if not active_cameras:
            self.logger.error("No active cameras found")
            return []
            
        max_cameras = self.config.getint('blueiris', 'max_cameras', fallback=64)
        cameras_to_check = active_cameras[:max_cameras]
        
        self.logger.info(f"Searching across {len(cameras_to_check)} active cameras...")
        
        # Search cameras concurrently
        results = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all camera check tasks
            future_to_camera = {
                executor.submit(self.search_person_in_camera, reference_encoding, camera): camera
                for camera in cameras_to_check
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_camera):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    camera = future_to_camera[future]
                    camera_name = camera.get('optionValue', camera.get('name', 'Unknown'))
                    self.logger.error(f"Error processing camera {camera_name}: {e}")
                    
        # Sort results by camera name
        results.sort(key=lambda x: x['camera_name'])
        
        return results
        
    def print_search_results(self, results: List[Dict]):
        """
        Print search results in a formatted way.
        
        Args:
            results: List of search results from search_person_all_cameras
        """
        if not results:
            print("No search results to display.")
            return
            
        print(f"\n{'='*60}")
        print("PEOPLE FINDER SEARCH RESULTS")
        print(f"{'='*60}")
        
        found_cameras = []
        not_found_cameras = []
        error_cameras = []
        
        for result in results:
            if result['error']:
                error_cameras.append(result)
            elif result['person_found']:
                found_cameras.append(result)
            else:
                not_found_cameras.append(result)
                
        # Print summary
        print(f"\nSUMMARY:")
        print(f"  Total cameras checked: {len(results)}")
        print(f"  Person found in: {len(found_cameras)} cameras")
        print(f"  Person not found in: {len(not_found_cameras)} cameras")
        print(f"  Errors: {len(error_cameras)} cameras")
        
        # Print detailed results for cameras where person was found
        if found_cameras:
            print(f"\n🎯 PERSON FOUND IN THESE LOCATIONS:")
            print("-" * 40)
            for result in found_cameras:
                camera_name = result['camera_name']
                face_count = len(result['face_locations'])
                min_distance = min(result['face_distances']) if result['face_distances'] else 'N/A'
                
                print(f"  📹 Camera: {camera_name}")
                print(f"     Faces detected: {face_count}")
                print(f"     Best match distance: {min_distance:.3f}" if isinstance(min_distance, float) else f"     Best match distance: {min_distance}")
                
                # Print face locations
                for i, (top, right, bottom, left) in enumerate(result['face_locations']):
                    print(f"     Face {i+1} location: ({left}, {top}) to ({right}, {bottom})")
                print()
                
        # Print errors if any
        if error_cameras:
            print(f"\n❌ CAMERAS WITH ERRORS:")
            print("-" * 40)
            for result in error_cameras:
                print(f"  📹 Camera: {result['camera_name']}")
                print(f"     Error: {result['error']}")
                print()
                
    def save_results_json(self, results: List[Dict], output_file: str):
        """
        Save search results to JSON file.
        
        Args:
            results: Search results
            output_file: Output file path
        """
        try:
            # Convert numpy arrays to lists for JSON serialization
            json_results = []
            for result in results:
                json_result = result.copy()
                # Convert face_distances to regular list
                if 'face_distances' in json_result:
                    json_result['face_distances'] = [float(d) for d in json_result['face_distances']]
                json_results.append(json_result)
                
            with open(output_file, 'w') as f:
                json.dump(json_results, f, indent=2, default=str)
                
            self.logger.info(f"Results saved to: {output_file}")
            
        except Exception as e:
            self.logger.error(f"Error saving results to JSON: {e}")
            
    def cleanup(self):
        """Cleanup resources."""
        try:
            self.blueiris_api.logout()
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Find a person across BlueIris cameras using face recognition")
    parser.add_argument("reference_image", help="Path to reference image of person to find")
    parser.add_argument("-c", "--config", default="config.ini", help="Configuration file path")
    parser.add_argument("-o", "--output", help="Output JSON file for results")
    parser.add_argument("-w", "--workers", type=int, default=5, help="Maximum concurrent camera workers")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Initialize application
    try:
        app = PeopleFinder(args.config)
        
        if args.verbose:
            logging.getLogger().setLevel(logging.DEBUG)
            
        # Test connection to BlueIris
        if not app.blueiris_api.login():
            print("❌ Failed to connect to BlueIris server. Please check configuration.")
            sys.exit(1)
            
        print("✅ Connected to BlueIris server")
        
        # Perform search
        results = app.search_person_all_cameras(args.reference_image, args.workers)
        
        # Display results
        app.print_search_results(results)
        
        # Save results if requested
        if args.output:
            app.save_results_json(results, args.output)
            
        # Check if person was found anywhere
        person_found_anywhere = any(result['person_found'] for result in results)
        
        if person_found_anywhere:
            print("\n🎉 Person located successfully!")
            sys.exit(0)
        else:
            print("\n😞 Person not found in any active cameras.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⏹️  Search interrupted by user")
        sys.exit(130)
    except Exception as e:
        logging.error(f"Application error: {e}")
        sys.exit(1)
    finally:
        try:
            app.cleanup()
        except:
            pass

if __name__ == "__main__":
    main()
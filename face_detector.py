"""
Face detection and recognition module using OpenCV and face_recognition library.
"""

import logging
from typing import List, Tuple, Optional
import io

# Try to import optional dependencies
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    
try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False
    
try:
    import face_recognition
    FACE_RECOGNITION_AVAILABLE = True
except ImportError:
    FACE_RECOGNITION_AVAILABLE = False
    
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

class FaceDetector:
    """Face detection and recognition handler."""
    
    def __init__(self, tolerance: float = 0.6, scale_factor: float = 0.25):
        """
        Initialize face detector.
        
        Args:
            tolerance: Face recognition tolerance (lower = more strict)
            scale_factor: Scale factor for image processing (smaller = faster)
        """
        self.tolerance = tolerance
        self.scale_factor = scale_factor
        self.logger = logging.getLogger(__name__)
        
        # Check dependencies
        missing_deps = []
        if not NUMPY_AVAILABLE:
            missing_deps.append("numpy")
        if not OPENCV_AVAILABLE:
            missing_deps.append("opencv-python")
        if not FACE_RECOGNITION_AVAILABLE:
            missing_deps.append("face-recognition")
        if not PIL_AVAILABLE:
            missing_deps.append("pillow")
            
        if missing_deps:
            self.logger.warning(f"Missing optional dependencies: {', '.join(missing_deps)}")
            self.logger.warning("Some features may not be available. Install with: pip install " + " ".join(missing_deps))
            
    def check_dependencies(self) -> bool:
        """Check if all required dependencies are available."""
        return NUMPY_AVAILABLE and OPENCV_AVAILABLE and FACE_RECOGNITION_AVAILABLE and PIL_AVAILABLE
        
    def load_reference_image(self, image_path: str) -> Optional['np.ndarray']:
        """
        Load and encode reference image for person to find.
        
        Args:
            image_path: Path to reference image file
            
        Returns:
            Face encoding array or None if no face found
        """
        if not self.check_dependencies():
            self.logger.error("Required dependencies not available for face recognition")
            return None
            
        try:
            # Load image
            image = face_recognition.load_image_file(image_path)
            
            # Find face encodings
            face_encodings = face_recognition.face_encodings(image)
            
            if len(face_encodings) == 0:
                self.logger.error(f"No face found in reference image: {image_path}")
                return None
            elif len(face_encodings) > 1:
                self.logger.warning(f"Multiple faces found in reference image, using first one: {image_path}")
                
            self.logger.info(f"Successfully loaded reference face from: {image_path}")
            return face_encodings[0]
            
        except Exception as e:
            self.logger.error(f"Error loading reference image {image_path}: {e}")
            return None
            
    def load_reference_from_bytes(self, image_bytes: bytes) -> Optional['np.ndarray']:
        """
        Load and encode reference image from bytes.
        
        Args:
            image_bytes: Image data as bytes
            
        Returns:
            Face encoding array or None if no face found
        """
        if not self.check_dependencies():
            self.logger.error("Required dependencies not available for face recognition")
            return None
            
        try:
            # Convert bytes to PIL Image
            image_pil = Image.open(io.BytesIO(image_bytes))
            
            # Convert PIL to numpy array (RGB format for face_recognition)
            image = np.array(image_pil)
            
            # Handle different image formats
            if len(image.shape) == 3 and image.shape[2] == 4:  # RGBA
                image = cv2.cvtColor(image, cv2.COLOR_RGBA2RGB)
            elif len(image.shape) == 3 and image.shape[2] == 3:  # Already RGB
                pass
            elif len(image.shape) == 2:  # Grayscale
                image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
            else:
                self.logger.error("Unsupported image format")
                return None
                
            # Find face encodings
            face_encodings = face_recognition.face_encodings(image)
            
            if len(face_encodings) == 0:
                self.logger.error("No face found in reference image bytes")
                return None
            elif len(face_encodings) > 1:
                self.logger.warning("Multiple faces found in reference image, using first one")
                
            self.logger.info("Successfully loaded reference face from bytes")
            return face_encodings[0]
            
        except Exception as e:
            self.logger.error(f"Error loading reference image from bytes: {e}")
            return None
            
    def find_faces_in_image(self, image_bytes: bytes) -> List[Tuple['np.ndarray', Tuple[int, int, int, int]]]:
        """
        Find all faces in an image and return their encodings and locations.
        
        Args:
            image_bytes: Image data as bytes
            
        Returns:
            List of tuples containing (face_encoding, (top, right, bottom, left))
        """
        if not self.check_dependencies():
            self.logger.error("Required dependencies not available for face recognition")
            return []
            
        try:
            # Convert bytes to PIL Image
            image_pil = Image.open(io.BytesIO(image_bytes))
            
            # Convert to numpy array
            image = np.array(image_pil)
            
            # Handle different image formats
            if len(image.shape) == 3 and image.shape[2] == 4:  # RGBA
                image = cv2.cvtColor(image, cv2.COLOR_RGBA2RGB)
            elif len(image.shape) == 3 and image.shape[2] == 3:  # Already RGB
                pass
            elif len(image.shape) == 2:  # Grayscale
                image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
            else:
                return []
                
            # Scale down image for faster processing
            if self.scale_factor != 1.0:
                small_image = cv2.resize(image, (0, 0), fx=self.scale_factor, fy=self.scale_factor)
            else:
                small_image = image
                
            # Find face locations and encodings
            face_locations = face_recognition.face_locations(small_image)
            face_encodings = face_recognition.face_encodings(small_image, face_locations)
            
            # Scale back face locations if we scaled the image
            if self.scale_factor != 1.0:
                face_locations = [(
                    int(top / self.scale_factor),
                    int(right / self.scale_factor),
                    int(bottom / self.scale_factor),
                    int(left / self.scale_factor)
                ) for (top, right, bottom, left) in face_locations]
                
            return list(zip(face_encodings, face_locations))
            
        except Exception as e:
            self.logger.error(f"Error finding faces in image: {e}")
            return []
            
    def is_person_in_image(self, reference_encoding: 'np.ndarray', image_bytes: bytes) -> Tuple[bool, List[Tuple[int, int, int, int]]]:
        """
        Check if the reference person is present in the given image.
        
        Args:
            reference_encoding: Reference face encoding to search for
            image_bytes: Image data as bytes to search in
            
        Returns:
            Tuple of (person_found, list_of_matching_face_locations)
        """
        if not self.check_dependencies():
            self.logger.error("Required dependencies not available for face recognition")
            return False, []
            
        try:
            faces_data = self.find_faces_in_image(image_bytes)
            
            if not faces_data:
                return False, []
                
            matching_locations = []
            
            for face_encoding, face_location in faces_data:
                # Compare faces
                matches = face_recognition.compare_faces([reference_encoding], face_encoding, tolerance=self.tolerance)
                
                if matches[0]:  # Face matches
                    matching_locations.append(face_location)
                    
            person_found = len(matching_locations) > 0
            
            if person_found:
                self.logger.info(f"Person found! Detected {len(matching_locations)} matching face(s)")
            
            return person_found, matching_locations
            
        except Exception as e:
            self.logger.error(f"Error checking if person is in image: {e}")
            return False, []
            
    def get_face_distance(self, reference_encoding: 'np.ndarray', image_bytes: bytes) -> List[float]:
        """
        Get face distances for all faces in image compared to reference.
        Lower distance means better match.
        
        Args:
            reference_encoding: Reference face encoding
            image_bytes: Image data as bytes
            
        Returns:
            List of face distances
        """
        if not self.check_dependencies():
            self.logger.error("Required dependencies not available for face recognition")
            return []
            
        try:
            faces_data = self.find_faces_in_image(image_bytes)
            
            if not faces_data:
                return []
                
            distances = []
            
            for face_encoding, _ in faces_data:
                distance = face_recognition.face_distance([reference_encoding], face_encoding)[0]
                distances.append(distance)
                
            return distances
            
        except Exception as e:
            self.logger.error(f"Error calculating face distances: {e}")
            return []


class MockFaceDetector:
    """Mock face detector for testing without dependencies."""
    
    def __init__(self, tolerance: float = 0.6, scale_factor: float = 0.25):
        self.tolerance = tolerance
        self.scale_factor = scale_factor
        self.logger = logging.getLogger(__name__)
        self.logger.info("Using mock face detector - install opencv-python and face-recognition for real functionality")
        
    def check_dependencies(self) -> bool:
        return False
        
    def load_reference_image(self, image_path: str):
        self.logger.info(f"Mock: Would load reference image from {image_path}")
        return "mock_encoding"
        
    def load_reference_from_bytes(self, image_bytes: bytes):
        self.logger.info("Mock: Would load reference image from bytes")
        return "mock_encoding"
        
    def find_faces_in_image(self, image_bytes: bytes):
        self.logger.info("Mock: Would find faces in image")
        return [("mock_encoding", (100, 200, 150, 150))]
        
    def is_person_in_image(self, reference_encoding, image_bytes: bytes):
        self.logger.info("Mock: Would check if person is in image")
        # Simulate finding person sometimes
        import random
        found = random.choice([True, False])
        locations = [(100, 200, 150, 150)] if found else []
        return found, locations
        
    def get_face_distance(self, reference_encoding, image_bytes: bytes):
        self.logger.info("Mock: Would calculate face distances")
        return [0.4] if reference_encoding else []
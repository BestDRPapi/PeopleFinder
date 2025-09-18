#!/usr/bin/env python3
"""
Example usage of PeopleFinder application.
This script demonstrates how to use the PeopleFinder programmatically.
"""

import sys
import os
from people_finder import PeopleFinder

def main():
    """Example of programmatic usage."""
    
    # Check if reference image is provided
    if len(sys.argv) < 2:
        print("Usage: python example_usage.py <reference_image_path>")
        print("Example: python example_usage.py photos/john_doe.jpg")
        sys.exit(1)
        
    reference_image = sys.argv[1]
    
    # Check if reference image exists
    if not os.path.exists(reference_image):
        print(f"Error: Reference image not found: {reference_image}")
        sys.exit(1)
        
    try:
        # Initialize PeopleFinder
        print("Initializing PeopleFinder...")
        finder = PeopleFinder("config.ini")
        
        # Test connection
        print("Connecting to BlueIris server...")
        if not finder.blueiris_api.login():
            print("❌ Failed to connect to BlueIris. Check your configuration.")
            sys.exit(1)
            
        print("✅ Connected successfully!")
        
        # Get camera list for informational purposes
        cameras = finder.blueiris_api.get_active_cameras()
        print(f"📹 Found {len(cameras)} active cameras")
        
        # Search for person
        print(f"🔍 Searching for person in reference image: {reference_image}")
        results = finder.search_person_all_cameras(reference_image, max_workers=3)
        
        # Process results
        found_locations = []
        for result in results:
            if result['person_found'] and not result['error']:
                found_locations.append(result['camera_name'])
                
        # Display results
        if found_locations:
            print(f"\n🎯 Person found in {len(found_locations)} location(s):")
            for location in found_locations:
                print(f"  - {location}")
        else:
            print("\n😞 Person not found in any cameras")
            
        # Save detailed results
        output_file = "search_results.json"
        finder.save_results_json(results, output_file)
        print(f"📄 Detailed results saved to: {output_file}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    finally:
        # Cleanup
        try:
            finder.cleanup()
        except:
            pass

if __name__ == "__main__":
    main()
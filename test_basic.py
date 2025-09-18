#!/usr/bin/env python3
"""
Basic tests for PeopleFinder modules.
These tests check that modules can be imported and basic functionality works.
"""

import sys
import os
import tempfile
import unittest
from unittest.mock import Mock, patch, MagicMock

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from blueiris_api import BlueIrisAPI
    from face_detector import FaceDetector, MockFaceDetector
    from people_finder import PeopleFinder
except ImportError as e:
    print(f"Import error: {e}")
    print("Some modules may not be available due to missing dependencies")
    sys.exit(1)

class TestBlueIrisAPI(unittest.TestCase):
    """Test BlueIris API functionality."""
    
    def setUp(self):
        self.api = BlueIrisAPI("http://localhost:81", "test", "test")
        
    def test_initialization(self):
        """Test API initialization."""
        self.assertEqual(self.api.server_url, "http://localhost:81")
        self.assertEqual(self.api.username, "test")
        self.assertEqual(self.api.password, "test")
        self.assertIsNone(self.api.session_id)
        
    @patch('requests.post')
    def test_make_request(self, mock_post):
        """Test API request making."""
        mock_response = Mock()
        mock_response.json.return_value = {"result": "success"}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        result = self.api._make_request("test_cmd", param1="value1")
        
        self.assertEqual(result["result"], "success")
        mock_post.assert_called_once()

class TestFaceDetector(unittest.TestCase):
    """Test Face Detector functionality."""
    
    def setUp(self):
        self.detector = FaceDetector(tolerance=0.6, scale_factor=0.25)
        
    def test_initialization(self):
        """Test detector initialization."""
        self.assertEqual(self.detector.tolerance, 0.6)
        self.assertEqual(self.detector.scale_factor, 0.25)
        
    def test_load_nonexistent_image(self):
        """Test loading nonexistent image."""
        result = self.detector.load_reference_image("nonexistent.jpg")
        self.assertIsNone(result)

class TestPeopleFinder(unittest.TestCase):
    """Test PeopleFinder main application."""
    
    def setUp(self):
        # Create a temporary config file
        self.config_content = """
[blueiris]
server_url = http://localhost:81
username = test
password = test
max_cameras = 64
connection_timeout = 10

[face_recognition]
tolerance = 0.6
scale_factor = 0.25

[logging]
level = INFO
file = 
"""
        self.temp_config = tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False)
        self.temp_config.write(self.config_content)
        self.temp_config.close()
        
    def tearDown(self):
        os.unlink(self.temp_config.name)
        
    def test_initialization(self):
        """Test PeopleFinder initialization."""
        try:
            finder = PeopleFinder(self.temp_config.name)
            self.assertIsNotNone(finder.blueiris_api)
            self.assertIsNotNone(finder.face_detector)
        except Exception as e:
            self.fail(f"PeopleFinder initialization failed: {e}")

def test_imports():
    """Test that all required packages can be imported."""
    
    # Test required packages
    try:
        import requests
        print("✅ requests imported successfully")
    except ImportError:
        print("❌ requests not available - install with: pip install requests")
        return False
    
    # Test optional packages
    optional_success = True
    
    try:
        import cv2
        print("✅ OpenCV imported successfully")
    except ImportError:
        print("⚠️  OpenCV not available - install with: pip install opencv-python")
        optional_success = False
        
    try:
        import face_recognition
        print("✅ face_recognition imported successfully")
    except ImportError:
        print("⚠️  face_recognition not available - install with: pip install face-recognition")
        optional_success = False
        
    try:
        import numpy
        print("✅ numpy imported successfully")
    except ImportError:
        print("⚠️  numpy not available - install with: pip install numpy")
        optional_success = False
        
    if not optional_success:
        print("\n⚠️  Some optional packages are missing.")
        print("The application will work with limited functionality (mock face detection).")
        print("For full functionality, install: pip install opencv-python face-recognition numpy pillow")
        
    return True

def main():
    """Run basic tests."""
    print("Testing PeopleFinder modules...")
    print("=" * 50)
    
    # Test imports first
    if not test_imports():
        print("\n❌ Required packages are missing!")
        print("Install missing packages with: pip install requests")
        return False
        
    print("\n" + "=" * 50)
    print("Running unit tests...")
    
    # Run unit tests
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestBlueIrisAPI))
    suite.addTests(loader.loadTestsFromTestCase(TestFaceDetector))
    suite.addTests(loader.loadTestsFromTestCase(TestPeopleFinder))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    if result.wasSuccessful():
        print("\n🎉 All tests passed!")
        print("\nNext steps:")
        print("1. Configure config.ini with your BlueIris server details")
        print("2. Run: python people_finder.py path/to/reference_image.jpg")
        return True
    else:
        print("\n❌ Some tests failed!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
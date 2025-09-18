"""
BlueIris API client for camera management and image capture.
"""

import requests
import json
import logging
from typing import List, Dict, Optional, Tuple
import hashlib
import time

class BlueIrisAPI:
    """Client for BlueIris API to interact with cameras."""
    
    def __init__(self, server_url: str, username: str, password: str, timeout: int = 10):
        """
        Initialize BlueIris API client.
        
        Args:
            server_url: BlueIris server URL (e.g., "http://localhost:81")
            username: BlueIris username
            password: BlueIris password
            timeout: Connection timeout in seconds
        """
        self.server_url = server_url.rstrip('/')
        self.username = username
        self.password = password
        self.timeout = timeout
        self.session_id = None
        self.logger = logging.getLogger(__name__)
        
    def _make_request(self, cmd: str, **params) -> Dict:
        """
        Make a request to BlueIris API.
        
        Args:
            cmd: Command to execute
            **params: Additional parameters
            
        Returns:
            API response as dictionary
        """
        url = f"{self.server_url}/json"
        
        data = {
            "cmd": cmd,
            **params
        }
        
        if self.session_id:
            data["session"] = self.session_id
            
        try:
            response = requests.post(
                url, 
                json=data, 
                timeout=self.timeout,
                headers={'Content-Type': 'application/json'}
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"API request failed: {e}")
            raise
            
    def login(self) -> bool:
        """
        Login to BlueIris server.
        
        Returns:
            True if login successful, False otherwise
        """
        try:
            # First, get session info
            response = self._make_request("login")
            
            if response.get("result") != "success":
                self.logger.error("Failed to get session info")
                return False
                
            session = response.get("session")
            if not session:
                self.logger.error("No session ID received")
                return False
                
            # Create password hash
            password_hash = hashlib.md5(f"{self.username}:{session}:{self.password}".encode()).hexdigest()
            
            # Login with credentials
            login_response = self._make_request(
                "login",
                session=session,
                response=password_hash
            )
            
            if login_response.get("result") == "success":
                self.session_id = session
                self.logger.info("Successfully logged in to BlueIris")
                return True
            else:
                self.logger.error(f"Login failed: {login_response.get('data', {}).get('reason', 'Unknown error')}")
                return False
                
        except Exception as e:
            self.logger.error(f"Login error: {e}")
            return False
            
    def get_camera_list(self) -> List[Dict]:
        """
        Get list of available cameras.
        
        Returns:
            List of camera information dictionaries
        """
        if not self.session_id:
            if not self.login():
                return []
                
        try:
            response = self._make_request("camlist")
            
            if response.get("result") == "success":
                cameras = response.get("data", [])
                self.logger.info(f"Found {len(cameras)} cameras")
                return cameras
            else:
                self.logger.error("Failed to get camera list")
                return []
                
        except Exception as e:
            self.logger.error(f"Error getting camera list: {e}")
            return []
            
    def get_camera_image(self, camera_name: str) -> Optional[bytes]:
        """
        Get current image from a camera.
        
        Args:
            camera_name: Name of the camera
            
        Returns:
            Image data as bytes, or None if failed
        """
        try:
            url = f"{self.server_url}/image/{camera_name}"
            
            # Add session authentication if available
            params = {}
            if self.session_id:
                params['session'] = self.session_id
                
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            if response.headers.get('content-type', '').startswith('image/'):
                return response.content
            else:
                self.logger.warning(f"Non-image response for camera {camera_name}")
                return None
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to get image from camera {camera_name}: {e}")
            return None
            
    def get_active_cameras(self) -> List[Dict]:
        """
        Get list of active cameras only.
        
        Returns:
            List of active camera information dictionaries
        """
        all_cameras = self.get_camera_list()
        active_cameras = []
        
        for camera in all_cameras:
            # Check if camera is active/enabled
            if camera.get("active", False) or camera.get("enabled", False):
                active_cameras.append(camera)
                
        self.logger.info(f"Found {len(active_cameras)} active cameras out of {len(all_cameras)} total")
        return active_cameras
        
    def logout(self):
        """Logout from BlueIris server."""
        if self.session_id:
            try:
                self._make_request("logout")
                self.session_id = None
                self.logger.info("Logged out from BlueIris")
            except Exception as e:
                self.logger.error(f"Error during logout: {e}")
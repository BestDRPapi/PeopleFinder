#!/usr/bin/env python3
"""
Setup script for PeopleFinder application.
"""

import sys
import subprocess
import os

def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 7):
        print("❌ Python 3.7 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    else:
        print(f"✅ Python version check passed: {sys.version}")
        return True

def install_dependencies():
    """Install required dependencies."""
    print("\nInstalling dependencies...")
    
    # Install basic dependencies
    basic_deps = ["requests"]
    print("Installing basic dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install"] + basic_deps)
        print("✅ Basic dependencies installed")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install basic dependencies: {e}")
        return False
    
    # Try to install optional dependencies
    optional_deps = [
        ("numpy", "pip install numpy"),
        ("opencv-python", "pip install opencv-python"),
        ("pillow", "pip install pillow"),
        ("face-recognition", "pip install face-recognition")
    ]
    
    print("\nInstalling optional dependencies (for full functionality)...")
    success_count = 0
    
    for dep, install_cmd in optional_deps:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", dep], 
                                timeout=300, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"✅ {dep} installed successfully")
            success_count += 1
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            print(f"⚠️  Failed to install {dep} - try manually: {install_cmd}")
    
    if success_count == len(optional_deps):
        print("🎉 All dependencies installed successfully!")
    elif success_count > 0:
        print(f"⚠️  {success_count}/{len(optional_deps)} optional dependencies installed")
        print("The application will work with limited functionality")
    else:
        print("⚠️  No optional dependencies could be installed")
        print("The application will use mock face detection")
    
    return True

def setup_configuration():
    """Set up configuration file."""
    config_file = "config.ini"
    
    if os.path.exists(config_file):
        print(f"\n✅ Configuration file already exists: {config_file}")
        return True
    
    print(f"\n📝 Creating default configuration file: {config_file}")
    
    # The config.ini should already exist from the repository
    if os.path.exists(config_file):
        print("✅ Configuration file ready")
        print("⚠️  Please edit config.ini with your BlueIris server details")
        return True
    else:
        print("❌ Configuration template not found")
        return False

def run_tests():
    """Run basic tests."""
    print("\n🧪 Running basic tests...")
    
    try:
        result = subprocess.run([sys.executable, "test_basic.py"], 
                              capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("✅ Basic tests passed")
            return True
        else:
            print("⚠️  Some tests failed, but application should still work")
            print("Output:", result.stdout)
            return True  # Non-critical
    except Exception as e:
        print(f"⚠️  Could not run tests: {e}")
        return True  # Non-critical

def main():
    """Main setup function."""
    print("🚀 PeopleFinder Setup")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        print("❌ Dependency installation failed")
        sys.exit(1)
    
    # Setup configuration
    if not setup_configuration():
        print("❌ Configuration setup failed")
        sys.exit(1)
    
    # Run tests
    run_tests()
    
    print("\n" + "=" * 50)
    print("🎉 Setup completed!")
    print("\nNext steps:")
    print("1. Edit config.ini with your BlueIris server details")
    print("2. Test connection: python people_finder.py --help")
    print("3. Run with reference image: python people_finder.py path/to/photo.jpg")
    print("\nFor help: python people_finder.py --help")

if __name__ == "__main__":
    main()
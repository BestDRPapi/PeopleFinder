# PeopleFinder

A Python application that searches for a specific person across all active BlueIris surveillance cameras using face recognition technology. This tool helps locate where in a building a person is by analyzing camera feeds in real-time.

## Features

- 🎯 **Face Recognition**: Uses advanced face recognition to identify people across multiple cameras
- 📹 **BlueIris Integration**: Connects to BlueIris surveillance system (supports up to 64 cameras)
- ⚡ **Concurrent Processing**: Checks multiple cameras simultaneously for faster results
- 🎛️ **Configurable**: Customizable face recognition tolerance and processing parameters
- 📊 **Detailed Results**: Provides face locations, confidence scores, and comprehensive reporting
- 💾 **Export Results**: Save search results to JSON format for further analysis
- 🎪 **User-Friendly**: Command-line interface with clear visual feedback

## Requirements

- Python 3.7+
- BlueIris surveillance system
- Reference image of the person to find
- Network access to BlueIris server

## Installation

1. Clone this repository:
```bash
git clone https://github.com/BestDRPapi/PeopleFinder.git
cd PeopleFinder
```

2. Install required Python packages:
```bash
pip install -r requirements.txt
```

3. Configure the application by editing `config.ini`:
```ini
[blueiris]
server_url = http://your-blueiris-server:81
username = your_username
password = your_password
max_cameras = 64
connection_timeout = 10

[face_recognition]
tolerance = 0.6
scale_factor = 0.25

[logging]
level = INFO
file = people_finder.log
```

## Usage

### Command Line Interface

Basic usage:
```bash
python people_finder.py path/to/reference_image.jpg
```

Advanced usage with options:
```bash
python people_finder.py reference_photo.jpg -c custom_config.ini -o results.json -w 8 -v
```

Options:
- `-c, --config`: Configuration file path (default: config.ini)
- `-o, --output`: Save results to JSON file
- `-w, --workers`: Maximum concurrent camera workers (default: 5)
- `-v, --verbose`: Enable verbose logging

### Programmatic Usage

```python
from people_finder import PeopleFinder

# Initialize
finder = PeopleFinder("config.ini")

# Connect to BlueIris
if finder.blueiris_api.login():
    # Search for person
    results = finder.search_person_all_cameras("reference_image.jpg")
    
    # Process results
    for result in results:
        if result['person_found']:
            print(f"Person found in camera: {result['camera_name']}")
    
    # Cleanup
    finder.cleanup()
```

## Configuration

### BlueIris Settings
- `server_url`: BlueIris web server URL (typically http://ip:81)
- `username`: BlueIris username
- `password`: BlueIris password
- `max_cameras`: Maximum number of cameras to check
- `connection_timeout`: Timeout for camera connections

### Face Recognition Settings
- `tolerance`: Recognition tolerance (0.0-1.0, lower = more strict)
- `scale_factor`: Image processing scale (smaller = faster but less accurate)

### Logging Settings
- `level`: Log level (DEBUG, INFO, WARNING, ERROR)
- `file`: Log file path (empty for console only)

## Output

The application provides:

1. **Console Output**: Real-time search progress and results
2. **JSON Export**: Detailed results with face locations and confidence scores
3. **Logging**: Comprehensive logging for debugging and monitoring

Example output:
```
✅ Connected to BlueIris server
📹 Found 12 active cameras
🔍 Searching across 12 active cameras...

🎯 PERSON FOUND IN THESE LOCATIONS:
📹 Camera: Front_Entrance
   Faces detected: 1
   Best match distance: 0.234

📹 Camera: Lobby_Main
   Faces detected: 1
   Best match distance: 0.187

🎉 Person located successfully!
```

## Architecture

The application consists of three main modules:

1. **`blueiris_api.py`**: BlueIris API client for camera management
2. **`face_detector.py`**: Face detection and recognition using OpenCV and face_recognition
3. **`people_finder.py`**: Main application orchestrating the search process

## Troubleshooting

### Common Issues

1. **Connection Failed**: Check BlueIris server URL, credentials, and network connectivity
2. **No Face Found**: Ensure reference image contains a clear, front-facing face
3. **Slow Performance**: Reduce `scale_factor` or `max_cameras` in configuration
4. **False Positives**: Decrease `tolerance` value for stricter matching

### Debug Mode

Enable verbose logging to see detailed processing information:
```bash
python people_finder.py reference.jpg -v
```

## Security Considerations

- Store BlueIris credentials securely
- Use HTTPS for BlueIris connections when possible
- Implement proper access controls for the application
- Regular security updates for dependencies

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is provided as-is for surveillance and security purposes. Please ensure compliance with local privacy laws and regulations when using face recognition technology.

## Support

For issues and questions, please open a GitHub issue with:
- Python version
- BlueIris version
- Configuration (without credentials)
- Error messages or unexpected behavior

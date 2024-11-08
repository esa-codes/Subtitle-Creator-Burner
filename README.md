# Subtitle Creator & Burner

A powerful Python application for creating, translating, and burning subtitles into videos using OpenAI's Whisper model for speech recognition. This application provides a user-friendly GUI interface built with PyQt6 for easy interaction with the subtitle creation and burning process.

## Features

- **Automated Subtitle Creation**: Uses OpenAI's Whisper model to automatically generate subtitles from video files
- **Multiple Language Support**: Supports multiple languages for both subtitle creation and translation
- **Subtitle Translation**: Integrated translation capabilities using Google Translate
- **Subtitle Burning**: Permanently embed subtitles into videos with customizable formatting
- **Multiple Whisper Models**: Support for various Whisper model sizes:
  - Tiny (150MB) - Fastest, least accurate
  - Base (400MB) - Fast, decent accuracy
  - Small (1GB) - Balanced speed/accuracy
  - Medium (3GB) - Slower, more accurate
  - Large (6GB) - Slowest, most accurate
- **Customizable Subtitle Appearance**: Control font size, family, color, and outline
- **Video Quality Settings**: Adjustable video encoding settings for output quality
- **Progress Tracking**: Real-time progress updates for all operations
- **Settings Persistence**: Automatically saves and loads your preferred settings

## Requirements

- Python 3.8+
- FFmpeg installed and accessible in system PATH
- Required Python packages (install via pip):
  ```
  PyQt6
  openai-whisper
  deep-translator
  humanize
  ```
  
## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/esa-codes/Subtitle-Creator-Burner.git
   cd Subtitle-Creator-Burner
   ```

2. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

3. Install FFmpeg:
   - **Windows**: Download from [FFmpeg website](https://ffmpeg.org/) and add to PATH
   - **Linux**: `sudo apt-get install ffmpeg`
   - **macOS**: `brew install ffmpeg`

3. Install FFmpeg:
   - **Windows**: Download from [FFmpeg website](https://ffmpeg.org/) and add to PATH
   - **Linux**: `sudo apt-get install ffmpeg`
   - **macOS**: `brew install ffmpeg`

## Usage

1. Launch the application:
   ```bash
   python main.py
   ```

2. Using the GUI:

   a. **File Selection**:
   - Click "Browse" to select your video file
   - The SRT path will be automatically set to match the video filename

   b. **Model Settings**:
   - Select the desired Whisper model size
   - Choose the source language or use "auto" for automatic detection
   - Download the model if not already present

   c. **Font Settings**:
   - Adjust font size (16-48)
   - Select font family
   - Choose font color and outline color

   d. **Translation** (optional):
   - Select source and target languages
   - Click "Translate SRT" to create a translated version

   e. **Video Settings**:
   - Adjust quality (CRF: 18-28, lower is better)
   - Select encoding preset (affects processing speed)

   f. **Processing**:
   - Click "Start Processing" to begin
   - Monitor progress through the progress bar and status messages

## Core Components

### Model Info (model_info.py)
Manages information about available Whisper models and supported languages. Includes model sizes, descriptions, and language codes.

### Processor (processor.py)
Handles the core functionality:
- Audio extraction from video
- Whisper model management and transcription
- Subtitle file creation and burning
- Settings management

### Translator (translator.py)
Provides translation capabilities:
- Uses Google Translate API
- Supports multiple language pairs
- Maintains SRT formatting during translation

### GUI (main_window.py)
Implements the graphical interface:
- File selection dialogs
- Model and language selection
- Font and video settings
- Progress tracking
- Error handling and user notifications

## Cache and Settings

The application maintains two main directories:
- `~/.cache/whisper/`: Stores downloaded Whisper models
- `~/.subtitle_app/`: Stores user settings and preferences

## Troubleshooting

1. **FFmpeg Not Found**:
   - Ensure FFmpeg is properly installed
   - Verify FFmpeg is in system PATH
   - Try running `ffmpeg -version` in terminal

2. **Model Download Issues**:
   - Check internet connection
   - Verify sufficient disk space
   - Try downloading a smaller model first

3. **Processing Errors**:
   - Check video file format compatibility
   - Ensure sufficient system resources
   - Check log file for detailed error messages

4. **Translation Errors**:
   - Verify internet connection
   - Check language code compatibility
   - Ensure source language detection is accurate

## Technical Details

### Video Processing
- Uses FFmpeg for video and audio manipulation
- Supports multiple video formats (mp4, avi, mkv, mov, etc.)
- Configurable encoding parameters for quality control

### Subtitle Processing
- SRT format support
- Timestamp synchronization
- Multi-language character support
- Configurable font settings

### Performance Considerations
- Model size affects processing speed and accuracy
- Video encoding preset impacts processing time
- Translation requires internet connectivity
- Disk space needed for model storage

## Contributing

Contributions are welcome! Please feel free to submit pull requests, create issues, or suggest improvements.

## License

GNU GENERAL PUBLIC LICENSE
                       Version 3, 29 June 2007

Copyright (C) 2024 [Your Name/Organization]

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
             
This software uses OpenAI's Whisper model, which has its own license terms
that must be respected in addition to this license.

1. You must cause any work that you distribute or publish, that in whole or in
   part contains or is derived from the Program or any part thereof, to be
   licensed as a whole at no charge to all third parties under the terms of
   this License.

2. If you modify this Program, or any covered work, you must cause the modified
   files to carry prominent notices stating that you changed the files and the
   date of any change.

3. You must retain, in the Source form of any Derivative Works that you
   distribute, all copyright, patent, trademark, and attribution notices from
   the Source form of the Program.

For the complete terms of the GNU General Public License version 3, see:
<https://www.gnu.org/licenses/gpl-3.0.html>

## Credits

- OpenAI Whisper for speech recognition
- FFmpeg for video processing
- PyQt6 for GUI implementation
- Google Translate for translation services

## Future Improvements

- Additional subtitle format support (SSA/ASS)
- Batch processing capabilities
- Advanced subtitle editing features
- Custom model training support
- Additional translation services
- Network model caching
- GPU acceleration support

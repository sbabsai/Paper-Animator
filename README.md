# Paper Animator

A production-ready tool to convert PDF text into animated videos with professional visual effects. This application allows you to search for text within PDF documents and generate animations where each occurrence of the text is highlighted and presented in a video sequence.

## Features

- **PDF Text Search**: Automatically finds all occurrences of specific text across multiple PDF files.
- **Real-Time Preview**: Live preview window updates automatically as you change settings.
- **Visual Effects**:
  - Realistic Text Highlighting
  - Chromatic Aberration
  - Paper Texture Overlay
  - Adjustable Blur Effects (Gaussian, Vertical, Radial)
  - Dark/Light Theme support
- **Audio Integration**: Sync sound effects to word transitions.
- **Video Export**: Renders high-quality MP4 videos with synchronized audio.
- **Modern GUI**: Responsive, dark-themed interface with animated backgrounds.
- **CLI Mode**: Command-line interface for quick batch processing.
- **Quick Command**: Save settings for rapid re-use via CLI.

## Installation

### Prerequisites

- Python 3.8 or higher
- FFmpeg (required by MoviePy for video rendering)

### Install FFmpeg

**Windows:**
```bash
# Download from https://ffmpeg.org/download.html
# Add to PATH or place in project directory
```

**macOS:**
```bash
brew install ffmpeg
```

**Linux:**
```bash
sudo apt-get install ffmpeg
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

Or install manually:
```bash
pip install customtkinter PyMuPDF numpy Pillow moviepy pygame
```

## Usage

### GUI Mode (Default)

Launch the graphical interface:
```bash
python main.py
```

**Workflow:**
1. **Select PDFs**: Click "📁 Browse PDF Files" to choose documents.
2. **Enter Text**: Type the word or phrase to highlight.
3. **Live Preview**: A preview window opens automatically and updates in real-time as you adjust settings.
4. **Configure Effects**: Toggle Dark Theme, Text Highlight, Chromatic Aberration, Paper Texture, and Blur effects.
5. **Set Orientation**: Choose between 16:9 (landscape) or 9:16 (portrait).
6. **Adjust Speed**: Use the "Words Per Second" (WPS) slider to control animation speed.
7. **Add Audio (Optional)**: Select an audio file to play on each word transition.
8. **Save Settings**: Click "⚡ Save to Quick Command" to save current settings for CLI use.
9. **Export**: Click "💾 Save Video (MP4)" to render the final video.

### CLI Mode

For quick command-line processing without the GUI:

```bash
python main.py --cli
# or
python main.py -c
# or
python main.py cli
```

**CLI Workflow:**
1. Run the command above
2. Review the displayed settings (loaded from `quickcommand.txt`)
3. Enter the PDF file path when prompted
4. Enter output path (or press Enter for default)
5. Enter search text (or press Enter to use saved default)
6. The video will be generated and saved automatically

### Quick Command System

Save your frequently used settings for rapid CLI processing:

1. **In GUI**: Configure your preferred settings (effects, speed, blur type, etc.)
2. **Click**: "⚡ Save to Quick Command" button
3. **File Created**: `quickcommand.txt` is generated with your settings
4. **Use in CLI**: Run `python main.py --cli` to use these saved settings

**Example `quickcommand.txt`:**
```
# Paper Animator Quick Command Settings
search_text=Hello World
dark_theme=False
highlight=True
chromatic=False
paper=False
orientation=16:9
blur_type=None
blur_intensity=Low
size_multiplier=1.0
wps=1.5
audio_path=C:/audio/click.wav
```

## Configuration

The application saves your preferences automatically:

- **GUI Settings**: Stored in your home directory at `.paper_animator/config.json`
  - Window geometry
  - Recent PDF files
  - Default visual settings
  - Last used text and audio

- **Quick Command Settings**: Stored in `quickcommand.txt` in the project directory
  - Optimized for CLI batch processing
  - Can be manually edited

## Window Management

- **Main Window**: Can be resized freely - UI scales dynamically
- **Preview Window**: Opens automatically, can be snapped alongside main window
- **Windows Snap Support**: Use `Win + Left/Right` to arrange windows side-by-side

## Performance Tips

- **Preview Speed**: The live preview uses lower resolution (960x540) for faster updates
- **Final Export**: Full resolution (1920x1080 or 1080x1920) is used for saved videos
- **First PDF Only**: Preview processes only the first PDF for speed; export uses all selected PDFs
- **Frame Caching**: Recently generated previews are cached for instant switching
- **Cancellation**: Changing settings cancels ongoing preview generation immediately

## Troubleshooting

### Common Issues

**Missing FFmpeg:**
```
If video saving fails, ensure FFmpeg is installed and added to your system PATH.
Download: https://ffmpeg.org/download.html
```

**Audio Not Playing in Preview:**
- Check system volume and audio device settings
- Ensure audio file format is supported (.mp3, .wav, .aac)

**Slow Preview Generation:**
- High blur settings may slow down generation
- Large PDFs with many text occurrences take longer
- Consider reducing blur intensity for faster previews

**Preview Window Not Opening:**
- Click "🎬 Open Live Preview" button to reopen if closed
- Check that PDFs are selected and search text is entered

### Debug Mode

Run with verbose output:
```bash
python main.py --debug
```

## Project Structure

```
paper-animator/
├── main.py              # Entry point - GUI/CLI launcher
├── gui_controller.py    # Main GUI controller
├── cli_mode.py          # Command-line interface
├── pdf_processor.py     # PDF text extraction and frame generation
├── video_renderer.py    # MP4 video encoding
├── effects_processor.py # Visual effects (blur, texture, etc.)
├── config_manager.py    # Settings persistence
├── requirements.txt     # Python dependencies
├── quickcommand.txt     # Quick command settings (auto-generated)
└── README.md           # This file
```

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Win + Left/Right` | Snap windows side-by-side |
| `Ctrl + C` | Copy text from input fields |
| `Ctrl + V` | Paste text to input fields |

## License

This project is licensed for production use.

## Changelog

### v2.0.0
- Added real-time preview window with automatic updates
- Added CLI mode for command-line processing
- Added Quick Command system for saved presets
- Improved UI responsiveness with dynamic scaling
- Optimized preview performance with caching
- Removed manual UI size selector (now auto-scales)
- Added frame pre-resizing for smoother playback
- Added cancellation support for preview generation

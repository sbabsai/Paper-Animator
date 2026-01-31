# Paper Animator

A production-ready tool to convert PDF text into animated videos with professional visual effects. This application allows you to search for text within PDF documents and generate animations where each occurrence of the text is highlighted and presented in a video sequence.

## Features

- **PDF Text Search**: Automatically finds all occurrences of specific text across multiple PDF files.
- **Visual Effects**:
  - Realistic Text Highlighting
  - Chromatic Aberration
  - Paper Texture Overlay
  - Adjustable Blur Effects (Gaussian, Vertical, Radial)
  - Dark/Light Theme support
- **Audio Integration**: Sync sound effects to word transitions.
- **Video Export**: Renders high-quality MP4 videos with synchronized audio.
- **Modern GUI**: Responsive, dark-themed interface with real-time preview.

## Installation

### Prerequisites

- Python 3.8 or higher
- FFmpeg (required by MoviePy for video rendering)

### Install Dependencies

Run the following command to install the required Python packages:

```bash
pip install -r requirements.txt
```

If you do not have a `requirements.txt` file, install the core dependencies manually:

```bash
pip install customtkinter PyMuPDF numpy Pillow moviepy pygame
```

## Usage

1.  **Run the Application**:
    ```bash
    python main.py
    ```

2.  **Select PDFs**: Click "Browse PDF Files" to choose the documents you want to process.
3.  **Enter Text**: Type the word or phrase you want to highlight in the "Text to Find" box.
4.  **Configure Effects**: Adjust visual settings like Dark Theme, Blur, and Paper Texture.
5.  **Set Speed**: Use the slider to set the "Words Per Second" (WPS) speed.
6.  **Add Audio (Optional)**: Select an audio file to play on each word transition.
7.  **Preview**: Click "Generate Preview" to see the result with sound.
8.  **Save**: Click "Save Video (MP4)" to export your animation.

## Configuration

The application automatically saves your preferences (window size, last used text, visual settings) in a configuration file located in your home directory (`.paper_animator/config.json`).

## Troubleshooting

- **Missing FFmpeg**: If video saving fails, ensure FFmpeg is installed and added to your system PATH.
- **Audio Issues**: If audio doesn't play in preview, check your system volume and audio device settings.
- **Performance**: High blur settings on large images may slow down generation.

## License

This project is licensed for production use.

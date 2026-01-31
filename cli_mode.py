"""
CLI Mode for Paper Animator - Run without UI
"""
import os
import sys
from pathlib import Path


class QuickCommandConfig:
    """Handles quick command configuration"""
    
    CONFIG_FILE = "quickcommand.txt"
    
    DEFAULT_CONFIG = {
        'search_text': '',
        'dark_theme': False,
        'highlight': True,
        'chromatic': False,
        'paper': False,
        'orientation': '16:9',
        'blur_type': 'None',
        'blur_intensity': 'Low',
        'size_multiplier': 1.0,
        'wps': 1.5,
        'audio_path': ''
    }
    
    @classmethod
    def load(cls):
        """Load quick command config from file"""
        config = cls.DEFAULT_CONFIG.copy()
        
        if os.path.exists(cls.CONFIG_FILE):
            try:
                with open(cls.CONFIG_FILE, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith('#') or '=' not in line:
                            continue
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        # Convert types
                        if key in ['dark_theme', 'highlight', 'chromatic', 'paper']:
                            config[key] = value.lower() == 'true'
                        elif key in ['size_multiplier', 'wps']:
                            try:
                                config[key] = float(value)
                            except:
                                pass
                        else:
                            config[key] = value
            except Exception as e:
                print(f"Warning: Could not load config: {e}")
        
        return config
    
    @classmethod
    def save(cls, settings):
        """Save settings to quick command config file"""
        try:
            with open(cls.CONFIG_FILE, 'w', encoding='utf-8') as f:
                f.write("# Paper Animator Quick Command Settings\n")
                f.write("# This file is auto-generated. Edit with caution.\n\n")
                
                for key, value in settings.items():
                    f.write(f"{key}={value}\n")
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False
    
    @classmethod
    def save_from_gui(cls, gui_settings):
        """Convert GUI settings format to quick command format"""
        config = {
            'search_text': gui_settings.get('last_used_text', ''),
            'dark_theme': gui_settings.get('default_dark_theme', False),
            'highlight': gui_settings.get('default_highlight', True),
            'chromatic': gui_settings.get('default_chromatic', False),
            'paper': gui_settings.get('default_paper', False),
            'orientation': gui_settings.get('default_orientation', '16:9'),
            'blur_type': gui_settings.get('default_blur_type', 'None'),
            'blur_intensity': gui_settings.get('default_blur_intensity', 'Low'),
            'size_multiplier': gui_settings.get('highlight_size_multiplier', 1.0),
            'wps': gui_settings.get('default_wps', 1.5),
            'audio_path': gui_settings.get('default_audio', '')
        }
        return cls.save(config)


def run_cli_mode():
    """Run Paper Animator in CLI mode"""
    print("=" * 60)
    print("  Paper Animator - CLI Mode")
    print("=" * 60)
    print()
    
    # Load quick command settings
    config = QuickCommandConfig.load()
    
    # Show current settings
    print("Current Quick Command Settings:")
    print("-" * 40)
    print(f"  Search Text:      {config['search_text'] or '(not set)'}")
    print(f"  Dark Theme:       {config['dark_theme']}")
    print(f"  Text Highlight:   {config['highlight']}")
    print(f"  Chromatic Ab:     {config['chromatic']}")
    print(f"  Paper Texture:    {config['paper']}")
    print(f"  Orientation:      {config['orientation']}")
    print(f"  Blur Type:        {config['blur_type']}")
    print(f"  Blur Intensity:   {config['blur_intensity']}")
    print(f"  Highlight Size:   {config['size_multiplier']}x")
    print(f"  Speed (WPS):      {config['wps']}")
    print(f"  Audio File:       {config['audio_path'] or '(none)'}")
    print()
    
    # Get PDF file path
    pdf_path = input("Enter PDF file path: ").strip().strip('"')
    
    if not pdf_path:
        print("Error: No PDF file specified.")
        return
    
    if not os.path.exists(pdf_path):
        print(f"Error: File not found: {pdf_path}")
        return
    
    if not pdf_path.lower().endswith('.pdf'):
        print("Error: File must be a PDF.")
        return
    
    # Get output path
    default_output = str(Path(pdf_path).with_suffix('.mp4'))
    output_path = input(f"Enter output path [{default_output}]: ").strip().strip('"')
    
    if not output_path:
        output_path = default_output
    
    # Get search text (use default if available)
    default_text = config['search_text']
    if default_text:
        search_text = input(f"Enter text to search [{default_text}]: ").strip()
        if not search_text:
            search_text = default_text
    else:
        search_text = input("Enter text to search: ").strip()
    
    if not search_text:
        print("Error: No search text specified.")
        return
    
    print()
    print("Processing...")
    print("-" * 40)
    
    # Import and run
    try:
        from pdf_processor import PDFProcessor
        from video_renderer import VideoRenderer
        from effects_processor import EffectsProcessor
        from PIL import Image
        import pygame
        
        # Prepare settings
        settings = {
            'dark_theme': config['dark_theme'],
            'highlight': config['highlight'],
            'chromatic': config['chromatic'],
            'paper': config['paper'],
            'orientation': config['orientation'],
            'blur_type': config['blur_type'],
            'blur_intensity': config['blur_intensity'],
            'size_multiplier': config['size_multiplier']
        }
        
        # Process PDF
        processor = PDFProcessor()
        frames = processor.get_frames([pdf_path], search_text, settings, 
                                      lambda msg: print(f"  {msg}"))
        
        if not frames:
            print("\nError: No matches found.")
            return
        
        print(f"\nGenerated {len(frames)} frames.")
        print("Rendering video...")
        
        # Render video
        renderer = VideoRenderer()
        audio_path = config['audio_path'] if config['audio_path'] and os.path.exists(config['audio_path']) else None
        
        success = renderer.save_video(
            frames, output_path, 
            audio_path=audio_path,
            wps=config['wps']
        )
        
        if success:
            print(f"\n✅ Success! Video saved to: {output_path}")
        else:
            print("\n❌ Error: Video rendering failed.")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_cli_mode()

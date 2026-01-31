#!/usr/bin/env python3
"""
Paper Animator - PDF to Video Converter

A tool to convert PDF text into animated videos with visual effects.
Supports text highlighting, chromatic aberration, paper texture, and various blur effects.

Usage:
    python main.py

Author: Your Name
Version: 2.0.0 - Cinematic Edition
"""

import sys
import customtkinter as ctk
from tkinter import messagebox
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui_controller import GUIController


def check_dependencies():
    """Check if all required dependencies are available"""
    required_modules = [
        ('fitz', 'PyMuPDF'),
        ('numpy', 'NumPy'),
        ('PIL', 'Pillow'),
        ('moviepy', 'MoviePy'),
        ('pygame', 'Pygame'),
        ('customtkinter', 'CustomTkinter')
    ]
    
    missing_modules = []
    
    for module, display_name in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing_modules.append(display_name)
    
    if missing_modules:
        error_msg = (
            "Missing required dependencies:\n\n" +
            "\n".join(f"• {module}" for module in missing_modules) + 
            "\n\nPlease install missing modules using:\n" +
            "pip install " + " ".join([
                "PyMuPDF", "numpy", "Pillow", "moviepy", "pygame", "customtkinter"
            ])
        )
        print(error_msg)
        return False
    
    return True


def setup_logging():
    """Setup basic logging configuration"""
    import logging
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logging.getLogger(__name__)


def main():
    """Main entry point for the application"""
    logger = setup_logging()
    
    if not check_dependencies():
        input("Press Enter to exit...")
        sys.exit(1)
    
    try:
        root = ctk.CTk()
        
        try:
            pass
        except:
            pass
        
        app = GUIController(root)
        
        def on_closing():
            """Handle application closing"""
            try:
                app.save_current_settings()
            except:
                pass
            
            try:
                app.animation_running = False
            except:
                pass
            
            try:
                import pygame
                pygame.mixer.quit()
            except:
                pass
            
            root.destroy()
        
        root.protocol("WM_DELETE_WINDOW", on_closing)
        
        logger.info("Starting Paper Animator - Cinematic Edition...")
        root.mainloop()
        
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
    except Exception as e:
        error_msg = f"An unexpected error occurred: {str(e)}"
        logger.error(error_msg)
        
        try:
            messagebox.showerror("Application Error", error_msg)
        except:
            print(error_msg)
        
        sys.exit(1)


if __name__ == "__main__":
    main()

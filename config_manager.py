import json
import os
from pathlib import Path
from typing import Dict, Any


class ConfigManager:
    """Manages application configuration and user preferences"""
    
    def __init__(self, config_dir: str = None):
        """Initialize configuration manager"""
        if config_dir is None:
            config_dir = Path.home() / ".paper_animator"
        
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        
        self.config_file = self.config_dir / "config.json"
        self.default_config = {
            "audio_default_path": "",
            "last_used_text": "Phinma",
            "default_orientation": "16:9",
            "default_wps": 1.5,
            "default_dark_theme": False,
            "default_highlight": True,
            "default_chromatic": False,
            "default_paper": False,
            "default_blur_type": "None",
            "default_blur_intensity": "Low",
            "highlight_size_multiplier": 1.0,
            "recent_pdf_files": [],
            "window_geometry": "650x950",
            "recent_output_files": []
        }
        
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file or return defaults"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                merged_config = self.default_config.copy()
                merged_config.update(config)
                return merged_config
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading config: {e}. Using defaults.")
                return self.default_config.copy()
        else:
            return self.default_config.copy()
    
    def save_config(self) -> bool:
        """Save current configuration to file"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            return True
        except IOError as e:
            print(f"Error saving config: {e}")
            return False
    
    def get(self, key: str, default=None):
        """Get configuration value"""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any):
        """Set configuration value and save"""
        self.config[key] = value
        self.save_config()
    
    def update_settings(self, settings: Dict[str, Any]):
        """Update multiple settings at once"""
        self.config.update(settings)
        self.save_config()
    
    def add_recent_pdf(self, pdf_path: str):
        """Add PDF to recent files list"""
        recent_pdfs = self.config.get("recent_pdf_files", [])
        
        if pdf_path in recent_pdfs:
            recent_pdfs.remove(pdf_path)
        
        recent_pdfs.insert(0, pdf_path)
        
        recent_pdfs = recent_pdfs[:10]
        
        self.config["recent_pdf_files"] = recent_pdfs
        self.save_config()
    
    def get_recent_pdfs(self) -> list:
        """Get list of recently used PDF files"""
        return self.config.get("recent_pdf_files", [])
    
    def add_recent_output(self, output_path: str):
        """Add output file to recent files list"""
        recent_outputs = self.config.get("recent_output_files", [])
        
        if output_path in recent_outputs:
            recent_outputs.remove(output_path)
        
        recent_outputs.insert(0, output_path)
        
        recent_outputs = recent_outputs[:5]
        
        self.config["recent_output_files"] = recent_outputs
        self.save_config()
    
    def get_recent_outputs(self) -> list:
        """Get list of recently saved output files"""
        return self.config.get("recent_output_files", [])
    
    def get_default_audio_path(self) -> str:
        """Get default audio path (empty if not set)"""
        return self.config.get("audio_default_path", "")
    
    def set_default_audio_path(self, path: str):
        """Set default audio path"""
        self.config["audio_default_path"] = path
        self.save_config()
    
    def reset_to_defaults(self):
        """Reset configuration to default values"""
        self.config = self.default_config.copy()
        self.save_config()
    
    def export_config(self, export_path: str) -> bool:
        """Export configuration to specified file"""
        try:
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            return True
        except IOError as e:
            print(f"Error exporting config: {e}")
            return False
    
    def import_config(self, import_path: str) -> bool:
        """Import configuration from specified file"""
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                imported_config = json.load(f)
            
            merged_config = self.default_config.copy()
            merged_config.update(imported_config)
            
            self.config = merged_config
            self.save_config()
            return True
        except (IOError, json.JSONDecodeError) as e:
            print(f"Error importing config: {e}")
            return False
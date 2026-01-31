import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import time
import os
import math
import random
from PIL import Image, ImageTk
import pygame
from typing import Optional, List, Tuple

from pdf_processor import PDFProcessor
from video_renderer import VideoRenderer
from config_manager import ConfigManager


class AnimatedGradientBlob:
    """Represents an animated gradient blob for the background"""
    
    def __init__(self, canvas: ctk.CTkCanvas, x: float, y: float, radius: float, color: str, speed_x: float, speed_y: float):
        self.canvas = canvas
        self.x = x
        self.y = y
        self.radius = radius
        self.base_radius = radius
        self.color = color
        self.speed_x = speed_x
        self.speed_y = speed_y
        self.phase = random.uniform(0, 2 * math.pi)
        self.blob_id = None
        self.alpha = 0.1
        
    def create(self):
        """Create the blob on canvas"""
        self.blob_id = self.canvas.create_oval(
            self.x - self.radius, self.y - self.radius,
            self.x + self.radius, self.y + self.radius,
            fill=self.color, outline=""
        )
        
    def update(self, dt: float, canvas_width: int, canvas_height: int):
        """Update blob position and animation"""
        self.x += self.speed_x * dt
        self.y += self.speed_y * dt
        
        if self.x - self.radius < 0 or self.x + self.radius > canvas_width:
            self.speed_x *= -1
        if self.y - self.radius < 0 or self.y + self.radius > canvas_height:
            self.speed_y *= -1
            
        self.x = max(self.radius, min(canvas_width - self.radius, self.x))
        self.y = max(self.radius, min(canvas_height - self.radius, self.y))
        
        self.phase += dt * 0.5
        breathing = math.sin(self.phase) * 0.1 + 1.0
        self.radius = self.base_radius * breathing
        
        if self.blob_id:
            self.canvas.coords(
                self.blob_id,
                self.x - self.radius, self.y - self.radius,
                self.x + self.radius, self.y + self.radius
            )


class SpotlightEffect:
    """Handles mouse tracking spotlight effect"""
    
    def __init__(self, canvas: ctk.CTkCanvas):
        self.canvas = canvas
        self.mouse_x = 0
        self.mouse_y = 0
        self.spotlight_id = None
        self.gradient_id = None
        self.is_visible = False
        
    def create(self):
        """Create spotlight effect"""
        self.spotlight_id = self.canvas.create_oval(0, 0, 0, 0, fill="", outline="")
        self.gradient_id = self.canvas.create_oval(0, 0, 0, 0, fill="", outline="")
        
    def update_position(self, x: float, y: float):
        """Update spotlight position"""
        self.mouse_x = x
        self.mouse_y = y
        self.is_visible = True
        
        radius = 150
        self.canvas.coords(
            self.spotlight_id,
            x - radius, y - radius,
            x + radius, y + radius
        )
        
        gradient_radius = radius * 2
        self.canvas.coords(
            self.gradient_id,
            x - gradient_radius, y - gradient_radius,
            x + gradient_radius, y + gradient_radius
        )
        
    def hide(self):
        """Hide spotlight effect"""
        self.is_visible = False
        if self.spotlight_id:
            self.canvas.coords(self.spotlight_id, 0, 0, 0, 0)
        if self.gradient_id:
            self.canvas.coords(self.gradient_id, 0, 0, 0, 0)


class ModernButton(ctk.CTkButton):
    """Custom button with enhanced hover effects"""
    
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('corner_radius', 12)
        kwargs.setdefault('font', ctk.CTkFont(size=14, weight="bold"))
        kwargs.setdefault('height', 45)
        
        super().__init__(*args, **kwargs)
        
        self.original_fg_color = self.cget("fg_color")
        self.original_hover_color = self.cget("hover_color")
        
    def bind_hover_effects(self):
        """Add custom hover effects"""
        def on_enter(event):
            self.configure(
                fg_color=self.original_fg_color,
                hover_color=self.original_hover_color,
                transform="scale(1.02)"
            )
            
        def on_leave(event):
            self.configure(
                fg_color=self.original_fg_color,
                hover_color=self.original_hover_color,
                transform="scale(1.0)"
            )
            
        self.bind("<Enter>", on_enter)
        self.bind("<Leave>", on_leave)


class GlassPanel(ctk.CTkFrame):
    """Modern glassmorphism panel"""
    
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('corner_radius', 20)
        kwargs.setdefault('border_width', 0)
        kwargs.setdefault('fg_color', ("#1a1a1a", "#0f0f0f"))
        kwargs.setdefault('bg_color', "transparent")
        
        super().__init__(*args, **kwargs)
        
        self.configure(border_color=("#404040", "#404040"))
        self.configure(border_width=1)


class GUIController:
    """Main GUI controller for the Paper Animator application with modern design"""
    
    def __init__(self, root: ctk.CTk):
        self.root = root
        self.root.title("Paper Animator")
        
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")
        
        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()
        
        self.config_manager = ConfigManager()
        self.pdf_processor = PDFProcessor()
        self.video_renderer = VideoRenderer()
        
        self.pdf_files = []
        self.generated_frames = []
        self.preview_running = False
        self.current_frame_idx = 0
        self.preview_sound = None
        
        self.blobs = []
        self.spotlight = None
        self.animation_running = False
        self.last_frame_time = time.time()
        
        pygame.mixer.init()
        
        self._setup_responsive_sizing()
        
        self._setup_root_window()
        
        self._create_background()
        self._create_main_container()
        self._create_ui_content()
        
        self._start_animations()
        
        self._load_saved_settings()
        
    def _setup_responsive_sizing(self):
        """Set up responsive sizing system"""
        self.ui_size = self.config_manager.get("ui_size", "Medium")
        
        if self.ui_size == "High":
            width_percent = 0.85
            height_percent = 0.90
        elif self.ui_size == "Medium":
            width_percent = 0.70
            height_percent = 0.80
        else:
            width_percent = 0.55
            height_percent = 0.70
            
        max_width = min(int(self.screen_width * width_percent), self.screen_width - 100)
        max_height = min(int(self.screen_height * height_percent), self.screen_height - 100)
        
        self.window_width = max(600, min(max_width, 1200))
        self.window_height = max(500, min(max_height, 900))
        
        x = (self.screen_width - self.window_width) // 2
        y = (self.screen_height - self.window_height) // 2
        self.root.geometry(f"{self.window_width}x{self.window_height}+{x}+{y}")
        
    def _setup_root_window(self):
        """Configure root window properties"""
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)
        
        self.root.configure(fg_color="#0a0a0a")
        
        self.root.bind("<Motion>", self._on_mouse_move)
        self.root.bind("<Leave>", self._on_mouse_leave)
        
    def _create_background(self):
        """Create animated background with gradient blobs"""
        self.bg_canvas = ctk.CTkCanvas(
            self.root,
            bg="#0a0a0a",
            highlightthickness=0,
            relief="flat"
        )
        self.bg_canvas.grid(row=0, column=0, sticky="nsew")
        
        self._create_gradient_blobs()
        
        self.spotlight = SpotlightEffect(self.bg_canvas)
        self.spotlight.create()
        
    def _create_gradient_blobs(self):
        """Create animated gradient blobs"""
        colors = [
            "#1e3a8a",
            "#7c3aed",
            "#dc2626",
            "#059669",
            "#d97706",
        ]
        
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        
        num_blobs = random.randint(6, 8)
        for i in range(num_blobs):
            x = random.uniform(0, width)
            y = random.uniform(0, height)
            radius = random.uniform(80, 150)
            color = random.choice(colors)
            speed_x = random.uniform(-30, 30)
            speed_y = random.uniform(-30, 30)
            
            blob = AnimatedGradientBlob(
                self.bg_canvas, x, y, radius, color, speed_x, speed_y
            )
            blob.create()
            self.blobs.append(blob)
            
    def _create_main_container(self):
        """Create main container with modern styling"""
        self.main_container = GlassPanel(self.root)
        
        padding = max(10, min(30, self.window_width // 30))
        self.main_container.grid(row=0, column=0, padx=padding, pady=padding, sticky="nsew")
        
        self.main_container.grid_columnconfigure(0, weight=1)
        
    def _create_ui_content(self):
        """Create all UI content"""
        self._create_ui_size_selector()
        
        self._create_title()
        
        self._create_file_selection()
        
        self._create_text_input()
        
        self._create_visual_settings()
        
        self._create_speed_control()
        
        self._create_audio_settings()
        
        self._create_action_buttons()
        
        self._create_status_bar()
        
    def _create_ui_size_selector(self):
        """Create UI size selector section"""
        section_frame = GlassPanel(self.main_container)
        section_frame.grid(row=0, column=0, padx=20, pady=10, sticky="ew")
        section_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(
            section_frame,
            text="🖥️ 0. UI Size",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#ffffff"
        ).grid(row=0, column=0, columnspan=2, pady=(10, 5), sticky="w", padx=15)
        
        ctk.CTkLabel(
            section_frame, text="Interface Size:",
            font=ctk.CTkFont(size=12), text_color="#a0a0a0"
        ).grid(row=1, column=0, sticky="w", padx=15, pady=(0, 10))
        
        self.var_ui_size = ctk.StringVar(value=self.ui_size)
        self.combo_ui_size = ctk.CTkComboBox(
            section_frame, values=["Small", "Medium", "High"], variable=self.var_ui_size,
            font=ctk.CTkFont(size=12), height=35, corner_radius=8,
            border_width=1, border_color="#404040", fg_color="#1a1a1a",
            command=self._on_ui_size_change
        )
        self.combo_ui_size.grid(row=1, column=1, sticky="w", padx=15, pady=(0, 10))
        
        ctk.CTkLabel(
            section_frame,
            text="Small: Compact | Medium: Balanced | High: Full screen experience",
            font=ctk.CTkFont(size=10),
            text_color="#666666"
        ).grid(row=2, column=0, columnspan=2, pady=(0, 10), sticky="w", padx=15)
        
    def _on_ui_size_change(self, value):
        """Handle UI size change"""
        self.ui_size = value
        self.config_manager.set("ui_size", value)
        
        old_width = self.window_width
        old_height = self.window_height
        
        geometry = self.root.geometry()
        if '+' in geometry:
            parts = geometry.split('+')
            old_x = int(parts[1])
            old_y = int(parts[2])
        else:
            old_x = (self.screen_width - old_width) // 2
            old_y = (self.screen_height - old_height) // 2
        
        self._setup_responsive_sizing()
        
        x = (self.screen_width - self.window_width) // 2
        y = (self.screen_height - self.window_height) // 2
        self.root.geometry(f"{self.window_width}x{self.window_height}+{x}+{y}")
        
        self._update_ui_padding()
        
    def _update_ui_padding(self):
        """Update UI padding based on new window size"""
        padding = max(10, min(30, self.window_width // 30))
        self.main_container.grid_configure(padx=padding, pady=padding)
        
        for child in self.main_container.winfo_children():
            if hasattr(child, 'grid_info'):
                info = child.grid_info()
                if 'row' in info and info['row'] > 0:
                    try:
                        child.grid_configure(padx=padding, pady=5)
                    except:
                        pass
        
    def _create_title(self):
        """Create application title"""
        title_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        title_frame.grid(row=1, column=0, padx=20, pady=(20, 15), sticky="ew")
        title_frame.grid_columnconfigure(0, weight=1)
        
        title_size = max(24, min(36, self.window_width // 25))
        subtitle_size = max(12, min(18, self.window_width // 40))
        
        self.title_label = ctk.CTkLabel(
            title_frame,
            text="🎬 Paper Animator",
            font=ctk.CTkFont(size=title_size, weight="bold"),
            text_color="#ffffff"
        )
        self.title_label.grid(row=0, column=0, pady=(0, 5))
        
        self.subtitle_label = ctk.CTkLabel(
            title_frame,
            text="PDF Text Animation Studio",
            font=ctk.CTkFont(size=subtitle_size),
            text_color="#a0a0a0"
        )
        self.subtitle_label.grid(row=1, column=0)
        
    def _create_file_selection(self):
        """Create file selection section"""
        section_frame = GlassPanel(self.main_container)
        section_frame.grid(row=2, column=0, padx=20, pady=8, sticky="ew")
        section_frame.grid_columnconfigure(1, weight=1)
        
        section_title_size = max(14, min(20, self.window_width // 40))
        label_size = max(10, min(14, self.window_width // 60))
        
        ctk.CTkLabel(
            section_frame,
            text="📁 1. Select PDFs",
            font=ctk.CTkFont(size=section_title_size, weight="bold"),
            text_color="#ffffff"
        ).grid(row=0, column=0, columnspan=2, pady=(12, 8), sticky="w", padx=15)
        
        button_height = max(35, min(50, self.window_height // 20))
        self.btn_files = ModernButton(
            section_frame,
            text="Browse PDF Files",
            command=self.select_pdfs,
            fg_color="#3b82f6",
            hover_color="#2563eb",
            height=button_height
        )
        self.btn_files.grid(row=1, column=0, padx=15, pady=10, sticky="w")
        
        self.lbl_file_count = ctk.CTkLabel(
            section_frame,
            text="No files selected",
            font=ctk.CTkFont(size=label_size),
            text_color="#a0a0a0"
        )
        self.lbl_file_count.grid(row=1, column=1, padx=15, pady=10, sticky="w")
        
    def _create_text_input(self):
        """Create text input section"""
        section_frame = GlassPanel(self.main_container)
        section_frame.grid(row=3, column=0, padx=20, pady=8, sticky="ew")
        section_frame.grid_columnconfigure(0, weight=1)
        
        section_title_size = max(14, min(20, self.window_width // 40))
        entry_size = max(10, min(14, self.window_width // 60))
        
        ctk.CTkLabel(
            section_frame,
            text="🔍 2. Text to Find",
            font=ctk.CTkFont(size=section_title_size, weight="bold"),
            text_color="#ffffff"
        ).grid(row=0, column=0, pady=(12, 8), sticky="w", padx=15)
        
        entry_height = max(35, min(50, self.window_height // 20))
        self.entry_text = ctk.CTkEntry(
            section_frame,
            placeholder_text="Enter text to highlight...",
            font=ctk.CTkFont(size=entry_size),
            height=entry_height,
            corner_radius=12,
            border_width=2,
            border_color="#404040",
            fg_color="#1a1a1a"
        )
        self.entry_text.grid(row=1, column=0, padx=15, pady=(0, 10), sticky="ew")
        
        default_text = self.config_manager.get("last_used_text", "Phinma")
        if default_text:
            self.entry_text.insert(0, default_text)
            
    def _create_visual_settings(self):
        """Create visual settings section"""
        section_frame = GlassPanel(self.main_container)
        section_frame.grid(row=4, column=0, padx=20, pady=8, sticky="ew")
        section_frame.grid_columnconfigure(1, weight=1)
        
        section_title_size = max(14, min(20, self.window_width // 40))
        label_size = max(10, min(14, self.window_width // 60))
        combo_height = max(30, min(45, self.window_height // 22))
        slider_height = max(15, min(25, self.window_height // 40))
        
        ctk.CTkLabel(
            section_frame,
            text="🎨 3. Visual Settings",
            font=ctk.CTkFont(size=section_title_size, weight="bold"),
            text_color="#ffffff"
        ).grid(row=0, column=0, columnspan=2, pady=(12, 10), sticky="w", padx=15)
        
        self.var_dark = ctk.BooleanVar(value=self.config_manager.get("default_dark_theme", False))
        self.var_highlight = ctk.BooleanVar(value=self.config_manager.get("default_highlight", True))
        self.var_chromatic = ctk.BooleanVar(value=self.config_manager.get("default_chromatic", False))
        self.var_paper = ctk.BooleanVar(value=self.config_manager.get("default_paper", False))
        self.var_orientation = ctk.StringVar(value=self.config_manager.get("default_orientation", "16:9"))
        
        self.var_highlight_size = ctk.DoubleVar(value=self.config_manager.get("highlight_size_multiplier", 1.0))
        
        row = 1
        col = 0
        
        ctk.CTkCheckBox(
            section_frame, text="🌙 Dark Theme", variable=self.var_dark,
            font=ctk.CTkFont(size=label_size), checkbox_width=20, checkbox_height=20
        ).grid(row=row, column=col, sticky="w", padx=15, pady=3)
        
        col += 1
        ctk.CTkCheckBox(
            section_frame, text="✨ Text Highlight", variable=self.var_highlight,
            font=ctk.CTkFont(size=label_size), checkbox_width=20, checkbox_height=20
        ).grid(row=row, column=col, sticky="w", padx=15, pady=3)
        
        row += 1
        col = 0
        ctk.CTkCheckBox(
            section_frame, text="🌈 Chromatic Aberration", variable=self.var_chromatic,
            font=ctk.CTkFont(size=label_size), checkbox_width=20, checkbox_height=20
        ).grid(row=row, column=col, sticky="w", padx=15, pady=3)
        
        col += 1
        ctk.CTkCheckBox(
            section_frame, text="📄 Paper Texture", variable=self.var_paper,
            font=ctk.CTkFont(size=label_size), checkbox_width=20, checkbox_height=20
        ).grid(row=row, column=col, sticky="w", padx=15, pady=3)
        
        row += 1
        col = 0
        ctk.CTkLabel(
            section_frame, text="📐 Orientation:",
            font=ctk.CTkFont(size=label_size), text_color="#ffffff"
        ).grid(row=row, column=col, sticky="w", padx=15, pady=(8, 3))
        
        col += 1
        self.combo_orientation = ctk.CTkComboBox(
            section_frame, values=["16:9", "9:16"], variable=self.var_orientation,
            font=ctk.CTkFont(size=label_size), height=combo_height, corner_radius=8,
            border_width=1, border_color="#404040", fg_color="#1a1a1a"
        )
        self.combo_orientation.grid(row=row, column=col, sticky="w", padx=15, pady=(8, 3))
        
        row += 1
        col = 0
        ctk.CTkLabel(
            section_frame, text="🌫️ Blur Type:",
            font=ctk.CTkFont(size=label_size), text_color="#ffffff"
        ).grid(row=row, column=col, sticky="w", padx=15, pady=8)
        
        col += 1
        self.var_blur_type = ctk.StringVar(value=self.config_manager.get("default_blur_type", "None"))
        self.combo_blur_type = ctk.CTkComboBox(
            section_frame, values=["None", "Gaussian", "Vertical", "Radial (Center Clear)"],
            variable=self.var_blur_type, font=ctk.CTkFont(size=label_size), height=combo_height,
            corner_radius=8, border_width=1, border_color="#404040", fg_color="#1a1a1a"
        )
        self.combo_blur_type.grid(row=row, column=col, sticky="w", padx=15, pady=8)
        
        row += 1
        col = 0
        ctk.CTkLabel(
            section_frame, text="⚡ Blur Intensity:",
            font=ctk.CTkFont(size=label_size), text_color="#ffffff"
        ).grid(row=row, column=col, sticky="w", padx=15, pady=(3, 8))
        
        col += 1
        self.var_blur_intensity = ctk.StringVar(value=self.config_manager.get("default_blur_intensity", "Low"))
        self.combo_blur_intensity = ctk.CTkComboBox(
            section_frame, values=["Low", "Medium", "High"], variable=self.var_blur_intensity,
            font=ctk.CTkFont(size=label_size), height=combo_height, corner_radius=8,
            border_width=1, border_color="#404040", fg_color="#1a1a1a"
        )
        self.combo_blur_intensity.grid(row=row, column=col, sticky="w", padx=15, pady=(3, 8))
        
        row += 1
        col = 0
        ctk.CTkLabel(
            section_frame, text="🔍 Highlight Size (TEST):",
            font=ctk.CTkFont(size=label_size), text_color="#ffffff"
        ).grid(row=row, column=col, sticky="w", padx=15, pady=(8, 3))
        
        col += 1
        slider_frame = ctk.CTkFrame(section_frame, fg_color="transparent")
        slider_frame.grid(row=row, column=col, sticky="ew", padx=15, pady=(8, 3))
        slider_frame.grid_columnconfigure(0, weight=1)
        
        self.scale_highlight_size = ctk.CTkSlider(
            slider_frame, from_=1.0, to=5.0, variable=self.var_highlight_size,
            height=slider_height, corner_radius=8, progress_color="#3b82f6", button_color="#3b82f6"
        )
        self.scale_highlight_size.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        
        self.entry_highlight_size = ctk.CTkEntry(
            slider_frame, textvariable=self.var_highlight_size, width=50,
            height=max(25, min(35, self.window_height // 25)), corner_radius=6, font=ctk.CTkFont(size=10)
        )
        self.entry_highlight_size.grid(row=0, column=1)
        
    def _create_speed_control(self):
        """Create speed control section"""
        section_frame = GlassPanel(self.main_container)
        section_frame.grid(row=5, column=0, padx=20, pady=8, sticky="ew")
        section_frame.grid_columnconfigure(0, weight=1)
        
        section_title_size = max(14, min(20, self.window_width // 40))
        label_size = max(10, min(14, self.window_width // 60))
        slider_height = max(15, min(25, self.window_height // 40))
        
        ctk.CTkLabel(
            section_frame,
            text="⚡ 4. Speed Control",
            font=ctk.CTkFont(size=section_title_size, weight="bold"),
            text_color="#ffffff"
        ).grid(row=0, column=0, pady=(12, 10), sticky="w", padx=15)
        
        self.var_wps = ctk.DoubleVar(value=self.config_manager.get("default_wps", 1.5))
        
        slider_frame = ctk.CTkFrame(section_frame, fg_color="transparent")
        slider_frame.grid(row=1, column=0, padx=15, pady=(0, 10), sticky="ew")
        slider_frame.grid_columnconfigure(0, weight=1)
        
        self.scale_wps = ctk.CTkSlider(
            slider_frame, from_=0.5, to=50.0, variable=self.var_wps,
            height=slider_height, corner_radius=8, progress_color="#10b981", button_color="#10b981"
        )
        self.scale_wps.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        
        speed_frame = ctk.CTkFrame(slider_frame, fg_color="transparent")
        speed_frame.grid(row=0, column=1)
        
        entry_height = max(30, min(45, self.window_height // 22))
        self.entry_wps = ctk.CTkEntry(
            speed_frame, textvariable=self.var_wps, width=70, height=entry_height,
            corner_radius=6, font=ctk.CTkFont(size=label_size, weight="bold")
        )
        self.entry_wps.grid(row=0, column=0, padx=(0, 5))
        
        ctk.CTkLabel(
            speed_frame, text="wps", font=ctk.CTkFont(size=label_size, weight="bold"),
            text_color="#10b981"
        ).grid(row=0, column=1)
        
    def _create_audio_settings(self):
        """Create audio settings section"""
        section_frame = GlassPanel(self.main_container)
        section_frame.grid(row=6, column=0, padx=20, pady=8, sticky="ew")
        section_frame.grid_columnconfigure(0, weight=1)
        
        section_title_size = max(14, min(20, self.window_width // 40))
        label_size = max(10, min(14, self.window_width // 60))
        
        ctk.CTkLabel(
            section_frame,
            text="🔊 5. Audio Settings",
            font=ctk.CTkFont(size=section_title_size, weight="bold"),
            text_color="#ffffff"
        ).grid(row=0, column=0, pady=(12, 10), sticky="w", padx=15)
        
        audio_frame = ctk.CTkFrame(section_frame, fg_color="transparent")
        audio_frame.grid(row=1, column=0, padx=15, pady=(0, 10), sticky="ew")
        audio_frame.grid_columnconfigure(0, weight=1)
        
        entry_height = max(35, min(50, self.window_height // 20))
        self.entry_audio = ctk.CTkEntry(
            audio_frame, placeholder_text="Select audio file...",
            font=ctk.CTkFont(size=label_size), height=entry_height, corner_radius=8,
            border_width=1, border_color="#404040", fg_color="#1a1a1a"
        )
        self.entry_audio.grid(row=0, column=0, padx=(0, 10), sticky="ew")
        
        button_width = max(80, min(120, self.window_width // 8))
        self.btn_audio = ModernButton(
            audio_frame, text="Browse", command=self.select_audio,
            fg_color="#8b5cf6", hover_color="#7c3aed", width=button_width
        )
        self.btn_audio.grid(row=0, column=1)
        
        default_audio = self.config_manager.get_default_audio_path()
        if default_audio and os.path.exists(default_audio):
            self.entry_audio.insert(0, default_audio)
            
        ctk.CTkLabel(
            section_frame,
            text="🔔 Plays on every word transition",
            font=ctk.CTkFont(size=max(8, min(12, self.window_width // 70))),
            text_color="#888888"
        ).grid(row=2, column=0, padx=15, pady=(0, 10), sticky="w")
        
    def _create_action_buttons(self):
        """Create action buttons section"""
        section_frame = GlassPanel(self.main_container)
        section_frame.grid(row=7, column=0, padx=20, pady=15, sticky="ew")
        section_frame.grid_columnconfigure(0, weight=1)
        
        button_height = max(40, min(60, self.window_height // 18))
        button_font_size = max(12, min(16, self.window_width // 50))
        
        self.btn_preview = ModernButton(
            section_frame,
            text="🎬 Generate Preview (WITH SOUND)",
            command=self.start_preview_generation,
            fg_color="#f59e0b",
            hover_color="#d97706",
            font=ctk.CTkFont(size=button_font_size, weight="bold"),
            height=button_height
        )
        self.btn_preview.grid(row=0, column=0, padx=15, pady=(15, 8), sticky="ew")
        
        self.btn_save = ModernButton(
            section_frame,
            text="💾 Save Video (MP4)",
            command=self.save_to_file,
            fg_color="#10b981",
            hover_color="#059669",
            font=ctk.CTkFont(size=button_font_size, weight="bold"),
            height=button_height,
            state="disabled"
        )
        self.btn_save.grid(row=1, column=0, padx=15, pady=(8, 15), sticky="ew")
        
    def _create_status_bar(self):
        """Create status bar"""
        status_frame = GlassPanel(self.main_container, height=max(35, min(50, self.window_height // 20)))
        status_frame.grid(row=8, column=0, padx=20, pady=(0, 15), sticky="ew")
        status_frame.grid_columnconfigure(0, weight=1)
        
        status_font_size = max(10, min(14, self.window_width // 60))
        
        self.lbl_status = ctk.CTkLabel(
            status_frame,
            text="🎯 Ready to create animations",
            font=ctk.CTkFont(size=status_font_size),
            text_color="#a0a0a0"
        )
        self.lbl_status.grid(row=0, column=0, padx=15, pady=10, sticky="w")
        
    def _start_animations(self):
        """Start background animations"""
        self.animation_running = True
        self._animate()
        
    def _animate(self):
        """Main animation loop"""
        if not self.animation_running:
            return
            
        current_time = time.time()
        dt = current_time - self.last_frame_time
        self.last_frame_time = current_time
        
        canvas_width = self.root.winfo_width()
        canvas_height = self.root.winfo_height()
        
        for blob in self.blobs:
            blob.update(dt, canvas_width, canvas_height)
            
        self.root.after(16, self._animate)
        
    def _on_mouse_move(self, event):
        """Handle mouse movement for spotlight effect"""
        if self.spotlight:
            canvas_x = event.x
            canvas_y = event.y
            self.spotlight.update_position(canvas_x, canvas_y)
            
    def _on_mouse_leave(self, event):
        """Handle mouse leaving the window"""
        if self.spotlight:
            self.spotlight.hide()
            
    def _load_saved_settings(self):
        """Load settings from configuration"""
        geometry = self.config_manager.get("window_geometry")
        ui_size = self.config_manager.get("ui_size", "Medium")
        
        if geometry and ui_size == self.ui_size:
            try:
                self.root.geometry(geometry)
            except:
                pass
                
        recent_pdfs = self.config_manager.get_recent_pdfs()
        if recent_pdfs:
            existing_pdfs = [pdf for pdf in recent_pdfs if os.path.exists(pdf)]
            if existing_pdfs:
                self.pdf_files = existing_pdfs[:5]
                self.lbl_file_count.configure(text=f"📁 {len(self.pdf_files)} recent files loaded")
                
    def select_pdfs(self):
        """Handle PDF file selection"""
        files = filedialog.askopenfilenames(filetypes=[("PDF Files", "*.pdf")])
        if files:
            self.pdf_files = list(files)
            self.lbl_file_count.configure(text=f"📁 {len(files)} files selected")
            
            for pdf_file in files:
                self.config_manager.add_recent_pdf(pdf_file)
                
    def select_audio(self):
        """Handle audio file selection"""
        file = filedialog.askopenfilename(filetypes=[("Audio Files", "*.mp3 *.wav *.aac")])
        if file:
            self.entry_audio.delete(0, "end")
            self.entry_audio.insert(0, file)
            self.config_manager.set_default_audio_path(file)
            
    def get_settings(self) -> dict:
        """Get current settings from UI"""
        return {
            'dark_theme': self.var_dark.get(),
            'highlight': self.var_highlight.get(),
            'chromatic': self.var_chromatic.get(),
            'paper': self.var_paper.get(),
            'orientation': self.var_orientation.get(),
            'blur_type': self.var_blur_type.get(),
            'blur_intensity': self.var_blur_intensity.get(),
            'size_multiplier': self.var_highlight_size.get()
        }
        
    def update_status(self, msg: str):
        """Update status bar message"""
        self.lbl_status.configure(text=msg)
        self.root.update_idletasks()
        
    def save_current_settings(self):
        """Save current UI settings to config"""
        self.config_manager.update_settings({
            "last_used_text": self.entry_text.get(),
            "default_orientation": self.var_orientation.get(),
            "default_wps": self.var_wps.get(),
            "default_dark_theme": self.var_dark.get(),
            "default_highlight": self.var_highlight.get(),
            "default_chromatic": self.var_chromatic.get(),
            "default_paper": self.var_paper.get(),
            "default_blur_type": self.var_blur_type.get(),
            "default_blur_intensity": self.var_blur_intensity.get(),
            "highlight_size_multiplier": self.var_highlight_size.get(),
            "window_geometry": self.root.geometry(),
            "ui_size": self.ui_size
        })
        
    def start_preview_generation(self):
        """Start preview generation process"""
        text = self.entry_text.get()
        if not self.pdf_files or not text:
            messagebox.showerror("Error", "Select PDFs and Text first.")
            return
            
        self.save_current_settings()
        
        self.btn_preview.configure(state="disabled")
        self.btn_save.configure(state="disabled")
        self.update_status("🎬 Generating frames for preview...")
        
        t = threading.Thread(target=self._process_for_preview, args=(text,))
        t.start()
        
    def _process_for_preview(self, text: str):
        """Process PDFs for preview in background thread"""
        try:
            settings = self.get_settings()
            self.generated_frames = self.pdf_processor.get_frames(
                self.pdf_files, text, settings, self.update_status
            )
            
            if not self.generated_frames:
                self.update_status("❌ No text found.")
                messagebox.showwarning("Result", "No matches found.")
            else:
                self.update_status(f"✅ Generated {len(self.generated_frames)} frames.")
                self.root.after(0, lambda: self.btn_save.configure(state="normal"))
                self.root.after(0, self.launch_preview_window)
                
        except Exception as e:
            self.update_status(f"❌ Error: {e}")
            messagebox.showerror("Error", str(e))
        finally:
            self.root.after(0, lambda: self.btn_preview.configure(state="normal"))
            
    def launch_preview_window(self):
        """Launch preview window with sound"""
        if not self.generated_frames:
            return
            
        preview_win = ctk.CTkToplevel(self.root)
        preview_win.title("Preview (With Sound)")
        preview_win.geometry("800x600")
        
        preview_h = 600
        preview_w = int(preview_h * (16/9)) if self.var_orientation.get() == "16:9" else int(preview_h * (9/16))
        
        canvas_frame = ctk.CTkFrame(preview_win, fg_color="transparent")
        canvas_frame.pack(expand=True, fill="both", padx=20, pady=20)
        
        canvas_lbl = ctk.CTkLabel(canvas_frame, text="")
        canvas_lbl.pack(expand=True)
        
        self.preview_running = True
        self.current_frame_idx = 0
        
        audio_path = self.entry_audio.get()
        self.preview_sound = None
        if audio_path and os.path.exists(audio_path):
            try:
                self.preview_sound = pygame.mixer.Sound(audio_path)
            except Exception as e:
                print(f"Preview Audio Error: {e}")
                
        def play_frame():
            if not self.preview_running or not preview_win.winfo_exists():
                return
                
            if self.preview_sound:
                self.preview_sound.stop()
                self.preview_sound.play()
                
            pil_img = self.generated_frames[self.current_frame_idx]
            display_img = pil_img.resize((preview_w, preview_h), Image.Resampling.NEAREST)
            tk_img = ImageTk.PhotoImage(display_img)
            
            canvas_lbl.configure(image=tk_img)
            canvas_lbl.image = tk_img
            
            self.current_frame_idx = (self.current_frame_idx + 1) % len(self.generated_frames)
            
            try:
                current_wps = float(self.var_wps.get())
                if current_wps <= 0:
                    current_wps = 0.1
            except:
                current_wps = 1.5
                
            current_speed_ms = int((1.0 / current_wps) * 1000)
            preview_win.after(current_speed_ms, play_frame)
            
        preview_win.protocol("WM_DELETE_WINDOW", lambda: self.close_preview(preview_win))
        play_frame()
        
    def close_preview(self, win):
        """Close preview window"""
        self.preview_running = False
        if self.preview_sound:
            self.preview_sound.stop()
        win.destroy()
        
    def save_to_file(self):
        """Save video to file"""
        if not self.generated_frames:
            return
            
        output_file = filedialog.asksaveasfilename(
            defaultextension=".mp4",
            filetypes=[("MP4 Video", "*.mp4")]
        )
        if not output_file:
            return
            
        audio_file = self.entry_audio.get()
        try:
            wps = float(self.var_wps.get())
        except:
            wps = 1.5
            
        self.btn_save.configure(state="disabled")
        self.btn_preview.configure(state="disabled")
        
        t = threading.Thread(target=self._render_video_file, args=(output_file, audio_file, wps))
        t.start()
        
    def _render_video_file(self, output_path: str, audio_path: str, wps: float):
        """Render video file in background thread"""
        self.update_status("🎬 Encoding Video & Audio... (This may take a moment)")
        try:
            success = self.video_renderer.save_video(
                self.generated_frames, output_path, audio_path=audio_path, wps=wps
            )
            
            if success:
                self.config_manager.add_recent_output(output_path)
                messagebox.showinfo("Success", f"Video Saved Successfully!\nSpeed: {wps} wps")
            else:
                messagebox.showerror("Error", "Failed to save video.")
                
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            self.update_status("🎯 Ready")
            self.root.after(0, lambda: self.btn_save.configure(state="normal"))
            self.root.after(0, lambda: self.btn_preview.configure(state="normal"))

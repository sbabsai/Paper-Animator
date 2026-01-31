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
from cli_mode import QuickCommandConfig


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
        
        # Real-time preview window
        self.preview_window = None
        self.preview_canvas_label = None
        self.preview_update_pending = False
        self.preview_update_delay = 400  # ms delay for debouncing
        self.preview_thread = None
        self.preview_cancel_event = threading.Event()
        self.preview_cache = {}  # Cache for preview frames
        self.preview_cache_key = None
        self.preview_lock = threading.Lock()
        
        self.blobs = []
        self.spotlight = None
        self.animation_running = False
        self.last_frame_time = time.time()
        
        # Track settings changes
        self._last_settings_hash = None
        
        pygame.mixer.init()
        
        self._setup_responsive_sizing()
        
        self._setup_root_window()
        
        self._create_background()
        self._create_main_container()
        self._create_ui_content()
        
        self._start_animations()
        
        self._load_saved_settings()
        
    def _setup_responsive_sizing(self):
        """Set up automatic responsive sizing based on screen size"""
        # Calculate optimal window size based on screen
        width_percent = 0.75
        height_percent = 0.75
            
        max_width = min(int(self.screen_width * width_percent), self.screen_width - 100)
        max_height = min(int(self.screen_height * height_percent), self.screen_height - 100)
        
        self.window_width = max(600, min(max_width, 1200))
        self.window_height = max(500, min(max_height, 850))
        
        x = (self.screen_width - self.window_width) // 2
        y = (self.screen_height - self.window_height) // 2
        self.root.geometry(f"{self.window_width}x{self.window_height}+{x}+{y}")
        
        # Allow window to be resized
        self.root.minsize(600, 500)
        
    def _setup_root_window(self):
        """Configure root window properties"""
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)
        
        self.root.configure(fg_color="#0a0a0a")
        
        self.root.bind("<Motion>", self._on_mouse_move)
        self.root.bind("<Leave>", self._on_mouse_leave)
        self.root.bind("<Configure>", self._on_window_resize)
        
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
        
        padding = max(15, min(30, self.window_width // 35))
        self.main_container.grid(row=0, column=0, padx=padding, pady=padding, sticky="nsew")
        
        self.main_container.grid_columnconfigure(0, weight=1)
        self.main_container.grid_rowconfigure(0, weight=1)
        
    def _create_ui_content(self):
        """Create all UI content"""
        self._create_scrollable_container()
        
        self._create_title()
        
        self._create_file_selection()
        
        self._create_text_input()
        
        self._create_visual_settings()
        
        self._create_speed_control()
        
        self._create_audio_settings()
        
        self._create_action_buttons()
        
        self._create_status_bar()
        
    def _create_scrollable_container(self):
        """Create scrollable container for UI content"""
        self.scroll_frame = ctk.CTkScrollableFrame(
            self.main_container,
            fg_color="transparent",
            scrollbar_button_color="#3b82f6",
            scrollbar_button_hover_color="#2563eb"
        )
        self.scroll_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.scroll_frame.grid_columnconfigure(0, weight=1)
        
        self.content_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        self.content_frame.grid(row=0, column=0, sticky="nsew")
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(8, weight=1)
        
    def _on_ui_size_change(self, value):
        """Handle UI size change - deprecated, kept for compatibility"""
        pass
        
    def _create_title(self):
        """Create application title"""
        title_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        title_frame.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        title_frame.grid_columnconfigure(0, weight=1)
        
        title_size = max(20, min(32, self.window_width // 30))
        subtitle_size = max(11, min(16, self.window_width // 45))
        
        self.title_label = ctk.CTkLabel(
            title_frame,
            text="🎬 Paper Animator",
            font=ctk.CTkFont(size=title_size, weight="bold"),
            text_color="#ffffff"
        )
        self.title_label.grid(row=0, column=0, pady=(0, 5), sticky="ew")
        
        self.subtitle_label = ctk.CTkLabel(
            title_frame,
            text="PDF Text Animation Studio",
            font=ctk.CTkFont(size=subtitle_size),
            text_color="#a0a0a0"
        )
        self.subtitle_label.grid(row=1, column=0, sticky="ew")
        
    def _create_file_selection(self):
        """Create file selection section"""
        section_frame = GlassPanel(self.content_frame)
        section_frame.grid(row=1, column=0, padx=20, pady=8, sticky="ew")
        section_frame.grid_columnconfigure(0, weight=1)
        section_frame.grid_columnconfigure(1, weight=1)
        
        section_title_size = max(13, min(18, self.window_width // 45))
        label_size = max(10, min(13, self.window_width // 65))
        
        ctk.CTkLabel(
            section_frame,
            text="📁 Select PDFs",
            font=ctk.CTkFont(size=section_title_size, weight="bold"),
            text_color="#ffffff"
        ).grid(row=0, column=0, columnspan=2, pady=(12, 8), sticky="ew", padx=15)
        
        button_height = max(32, min(42, self.window_height // 22))
        self.btn_files = ModernButton(
            section_frame,
            text="Browse PDF Files",
            command=self.select_pdfs,
            fg_color="#3b82f6",
            hover_color="#2563eb",
            height=button_height
        )
        self.btn_files.grid(row=1, column=0, padx=15, pady=8, sticky="w")
        
        self.lbl_file_count = ctk.CTkLabel(
            section_frame,
            text="No files selected",
            font=ctk.CTkFont(size=label_size),
            text_color="#a0a0a0"
        )
        self.lbl_file_count.grid(row=1, column=1, padx=15, pady=8, sticky="ew")
        
    def _create_text_input(self):
        """Create text input section"""
        section_frame = GlassPanel(self.content_frame)
        section_frame.grid(row=2, column=0, padx=20, pady=8, sticky="ew")
        section_frame.grid_columnconfigure(0, weight=1)
        
        section_title_size = max(13, min(18, self.window_width // 45))
        entry_size = max(10, min(13, self.window_width // 65))
        
        ctk.CTkLabel(
            section_frame,
            text="🔍 Text to Find",
            font=ctk.CTkFont(size=section_title_size, weight="bold"),
            text_color="#ffffff"
        ).grid(row=0, column=0, pady=(12, 8), sticky="ew", padx=15)
        
        entry_height = max(32, min(42, self.window_height // 22))
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
        
        # Bind text changes to trigger preview update
        self.entry_text.bind('<KeyRelease>', lambda e: self._trigger_preview_update())
        
        default_text = self.config_manager.get("last_used_text", "Phinma")
        if default_text:
            self.entry_text.insert(0, default_text)
            
    def _create_visual_settings(self):
        """Create visual settings section"""
        section_frame = GlassPanel(self.content_frame)
        section_frame.grid(row=3, column=0, padx=20, pady=8, sticky="ew")
        section_frame.grid_columnconfigure(0, weight=1)
        section_frame.grid_columnconfigure(1, weight=1)
        
        section_title_size = max(13, min(18, self.window_width // 45))
        label_size = max(10, min(13, self.window_width // 65))
        combo_height = max(28, min(38, self.window_height // 25))
        slider_height = max(14, min(22, self.window_height // 45))
        
        ctk.CTkLabel(
            section_frame,
            text="🎨 Visual Settings",
            font=ctk.CTkFont(size=section_title_size, weight="bold"),
            text_color="#ffffff"
        ).grid(row=0, column=0, columnspan=2, pady=(12, 10), sticky="ew", padx=15)
        
        self.var_dark = ctk.BooleanVar(value=self.config_manager.get("default_dark_theme", False))
        self.var_highlight = ctk.BooleanVar(value=self.config_manager.get("default_highlight", True))
        self.var_chromatic = ctk.BooleanVar(value=self.config_manager.get("default_chromatic", False))
        self.var_paper = ctk.BooleanVar(value=self.config_manager.get("default_paper", False))
        self.var_orientation = ctk.StringVar(value=self.config_manager.get("default_orientation", "16:9"))
        
        self.var_highlight_size = ctk.DoubleVar(value=self.config_manager.get("highlight_size_multiplier", 1.0))
        
        # Add traces for real-time preview updates
        self.var_dark.trace_add('write', self._trigger_preview_update)
        self.var_highlight.trace_add('write', self._trigger_preview_update)
        self.var_chromatic.trace_add('write', self._trigger_preview_update)
        self.var_paper.trace_add('write', self._trigger_preview_update)
        self.var_orientation.trace_add('write', self._trigger_preview_update)
        self.var_highlight_size.trace_add('write', self._trigger_preview_update)
        
        row = 1
        col = 0
        
        ctk.CTkCheckBox(
            section_frame, text="🌙 Dark Theme", variable=self.var_dark,
            font=ctk.CTkFont(size=label_size), checkbox_width=20, checkbox_height=20
        ).grid(row=row, column=col, sticky="w", padx=20, pady=6)
        
        col += 1
        ctk.CTkCheckBox(
            section_frame, text="✨ Text Highlight", variable=self.var_highlight,
            font=ctk.CTkFont(size=label_size), checkbox_width=20, checkbox_height=20
        ).grid(row=row, column=col, sticky="w", padx=20, pady=6)
        
        row += 1
        col = 0
        ctk.CTkCheckBox(
            section_frame, text="🌈 Chromatic Aberration", variable=self.var_chromatic,
            font=ctk.CTkFont(size=label_size), checkbox_width=20, checkbox_height=20
        ).grid(row=row, column=col, sticky="w", padx=20, pady=6)
        
        col += 1
        ctk.CTkCheckBox(
            section_frame, text="📄 Paper Texture", variable=self.var_paper,
            font=ctk.CTkFont(size=label_size), checkbox_width=20, checkbox_height=20
        ).grid(row=row, column=col, sticky="w", padx=20, pady=6)
        
        row += 1
        col = 0
        ctk.CTkLabel(
            section_frame, text="📐 Orientation:",
            font=ctk.CTkFont(size=label_size), text_color="#ffffff"
        ).grid(row=row, column=col, sticky="w", padx=20, pady=(10, 5))
        
        col += 1
        self.combo_orientation = ctk.CTkComboBox(
            section_frame, values=["16:9", "9:16"], variable=self.var_orientation,
            font=ctk.CTkFont(size=label_size), height=combo_height, corner_radius=8,
            border_width=1, border_color="#404040", fg_color="#1a1a1a"
        )
        self.combo_orientation.grid(row=row, column=col, sticky="w", padx=20, pady=(10, 5))
        
        row += 1
        col = 0
        ctk.CTkLabel(
            section_frame, text="🌫️ Blur Type:",
            font=ctk.CTkFont(size=label_size), text_color="#ffffff"
        ).grid(row=row, column=col, sticky="w", padx=20, pady=10)
        
        col += 1
        self.var_blur_type = ctk.StringVar(value=self.config_manager.get("default_blur_type", "None"))
        self.var_blur_type.trace_add('write', self._trigger_preview_update)
        self.combo_blur_type = ctk.CTkComboBox(
            section_frame, values=["None", "Gaussian", "Vertical", "Radial (Center Clear)"],
            variable=self.var_blur_type, font=ctk.CTkFont(size=label_size), height=combo_height,
            corner_radius=8, border_width=1, border_color="#404040", fg_color="#1a1a1a"
        )
        self.combo_blur_type.grid(row=row, column=col, sticky="w", padx=20, pady=10)
        
        row += 1
        col = 0
        ctk.CTkLabel(
            section_frame, text="⚡ Blur Intensity:",
            font=ctk.CTkFont(size=label_size), text_color="#ffffff"
        ).grid(row=row, column=col, sticky="w", padx=20, pady=(5, 10))
        
        col += 1
        self.var_blur_intensity = ctk.StringVar(value=self.config_manager.get("default_blur_intensity", "Low"))
        self.var_blur_intensity.trace_add('write', self._trigger_preview_update)
        self.combo_blur_intensity = ctk.CTkComboBox(
            section_frame, values=["Low", "Medium", "High"], variable=self.var_blur_intensity,
            font=ctk.CTkFont(size=label_size), height=combo_height, corner_radius=8,
            border_width=1, border_color="#404040", fg_color="#1a1a1a"
        )
        self.combo_blur_intensity.grid(row=row, column=col, sticky="w", padx=20, pady=(5, 10))
        
        row += 1
        col = 0
        ctk.CTkLabel(
            section_frame, text="🔍 Highlight Size (TEST):",
            font=ctk.CTkFont(size=label_size), text_color="#ffffff"
        ).grid(row=row, column=col, sticky="w", padx=20, pady=(10, 5))
        
        col += 1
        slider_frame = ctk.CTkFrame(section_frame, fg_color="transparent")
        slider_frame.grid(row=row, column=col, sticky="ew", padx=20, pady=(8, 10))
        slider_frame.grid_columnconfigure(0, weight=1)
        
        self.scale_highlight_size = ctk.CTkSlider(
            slider_frame, from_=1.0, to=5.0, variable=self.var_highlight_size,
            height=slider_height, corner_radius=8, progress_color="#3b82f6", button_color="#3b82f6"
        )
        self.scale_highlight_size.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        
        self.entry_highlight_size = ctk.CTkEntry(
            slider_frame, textvariable=self.var_highlight_size, width=50,
            height=max(30, min(38, self.window_height // 28)), corner_radius=6, font=ctk.CTkFont(size=11)
        )
        self.entry_highlight_size.grid(row=0, column=1)
        
    def _create_speed_control(self):
        """Create speed control section"""
        section_frame = GlassPanel(self.content_frame)
        section_frame.grid(row=4, column=0, padx=20, pady=8, sticky="ew")
        section_frame.grid_columnconfigure(0, weight=1)
        
        section_title_size = max(13, min(18, self.window_width // 45))
        label_size = max(10, min(13, self.window_width // 65))
        slider_height = max(14, min(22, self.window_height // 45))
        
        ctk.CTkLabel(
            section_frame,
            text="⚡ Speed Control",
            font=ctk.CTkFont(size=section_title_size, weight="bold"),
            text_color="#ffffff"
        ).grid(row=0, column=0, pady=(12, 10), sticky="ew", padx=15)
        
        self.var_wps = ctk.DoubleVar(value=self.config_manager.get("default_wps", 1.5))
        self.var_wps.trace_add('write', self._trigger_preview_update)
        
        slider_frame = ctk.CTkFrame(section_frame, fg_color="transparent")
        slider_frame.grid(row=1, column=0, padx=20, pady=(0, 12), sticky="ew")
        slider_frame.grid_columnconfigure(0, weight=1)
        
        self.scale_wps = ctk.CTkSlider(
            slider_frame, from_=0.5, to=50.0, variable=self.var_wps,
            height=slider_height, corner_radius=8, progress_color="#10b981", button_color="#10b981"
        )
        self.scale_wps.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        
        speed_frame = ctk.CTkFrame(slider_frame, fg_color="transparent")
        speed_frame.grid(row=0, column=1)
        
        entry_height = max(30, min(40, self.window_height // 25))
        self.entry_wps = ctk.CTkEntry(
            speed_frame, textvariable=self.var_wps, width=70, height=entry_height,
            corner_radius=6, font=ctk.CTkFont(size=label_size, weight="bold")
        )
        self.entry_wps.grid(row=0, column=0, padx=(0, 4))
        
        ctk.CTkLabel(
            speed_frame, text="wps", font=ctk.CTkFont(size=label_size, weight="bold"),
            text_color="#10b981"
        ).grid(row=0, column=1)
        
    def _create_audio_settings(self):
        """Create audio settings section"""
        section_frame = GlassPanel(self.content_frame)
        section_frame.grid(row=5, column=0, padx=20, pady=8, sticky="ew")
        section_frame.grid_columnconfigure(0, weight=1)
        
        section_title_size = max(13, min(18, self.window_width // 45))
        label_size = max(10, min(13, self.window_width // 65))
        
        ctk.CTkLabel(
            section_frame,
            text="🔊 Audio Settings",
            font=ctk.CTkFont(size=section_title_size, weight="bold"),
            text_color="#ffffff"
        ).grid(row=0, column=0, pady=(12, 10), sticky="ew", padx=15)
        
        audio_frame = ctk.CTkFrame(section_frame, fg_color="transparent")
        audio_frame.grid(row=1, column=0, padx=20, pady=(0, 12), sticky="ew")
        audio_frame.grid_columnconfigure(0, weight=1)
        
        entry_height = max(32, min(42, self.window_height // 22))
        self.entry_audio = ctk.CTkEntry(
            audio_frame, placeholder_text="Select audio file...",
            font=ctk.CTkFont(size=label_size), height=entry_height, corner_radius=8,
            border_width=1, border_color="#404040", fg_color="#1a1a1a"
        )
        self.entry_audio.grid(row=0, column=0, padx=(0, 8), sticky="ew")
        
        button_width = max(80, min(110, self.window_width // 9))
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
            font=ctk.CTkFont(size=max(7, min(10, self.window_width // 80))),
            text_color="#888888"
        ).grid(row=2, column=0, padx=15, pady=(0, 10), sticky="w")
        
    def _create_action_buttons(self):
        """Create action buttons section"""
        section_frame = GlassPanel(self.content_frame)
        section_frame.grid(row=6, column=0, padx=20, pady=12, sticky="ew")
        section_frame.grid_columnconfigure(0, weight=1)
        
        button_height = max(36, min(48, self.window_height // 20))
        button_font_size = max(12, min(15, self.window_width // 55))
        
        self.btn_preview = ModernButton(
            section_frame,
            text="🎬 Open Live Preview",
            command=self._open_preview_window,
            fg_color="#f59e0b",
            hover_color="#d97706",
            font=ctk.CTkFont(size=button_font_size, weight="bold"),
            height=button_height
        )
        self.btn_preview.grid(row=0, column=0, padx=20, pady=(15, 8), sticky="ew")
        
        self.btn_save = ModernButton(
            section_frame,
            text="💾 Save Video (MP4)",
            command=self.save_to_file,
            fg_color="#10b981",
            hover_color="#059669",
            font=ctk.CTkFont(size=button_font_size, weight="bold"),
            height=button_height
        )
        self.btn_save.grid(row=1, column=0, padx=20, pady=(8, 8), sticky="ew")
        
        self.btn_quick_cmd = ModernButton(
            section_frame,
            text="⚡ Save to Quick Command",
            command=self._save_to_quick_command,
            fg_color="#8b5cf6",
            hover_color="#7c3aed",
            font=ctk.CTkFont(size=button_font_size, weight="bold"),
            height=button_height
        )
        self.btn_quick_cmd.grid(row=2, column=0, padx=20, pady=(8, 15), sticky="ew")
        
    def _create_status_bar(self):
        """Create status bar"""
        status_frame = GlassPanel(self.content_frame, height=max(32, min(42, self.window_height // 25)))
        status_frame.grid(row=7, column=0, padx=20, pady=(0, 15), sticky="ew")
        status_frame.grid_columnconfigure(0, weight=1)
        
        status_font_size = max(10, min(13, self.window_width // 65))
        
        self.lbl_status = ctk.CTkLabel(
            status_frame,
            text="🎯 Ready to create animations",
            font=ctk.CTkFont(size=status_font_size),
            text_color="#a0a0a0"
        )
        self.lbl_status.grid(row=0, column=0, padx=20, pady=10, sticky="w")
        
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
    
    def _on_window_resize(self, event=None):
        """Handle window resize - update UI scaling dynamically"""
        # Only handle main window resize (not child widgets)
        if event and event.widget != self.root:
            return
            
        # Get current window size
        current_width = self.root.winfo_width()
        current_height = self.root.winfo_height()
        
        # Update window dimensions
        self.window_width = current_width
        self.window_height = current_height
        
        # Update UI scaling
        self._update_ui_scaling()
        
        # Update preview window size if it exists
        if self.preview_window and self.preview_window.winfo_exists():
            self._update_preview_window_size()
    
    def _update_ui_scaling(self):
        """Update UI element sizes based on current window dimensions"""
        # Calculate scale factors
        scale_x = self.window_width / 1000  # base width
        scale_y = self.window_height / 700  # base height
        scale = min(scale_x, scale_y, 1.2)  # cap at 1.2x
        
        # Update scroll frame
        if hasattr(self, 'scroll_frame'):
            padding = max(2, min(8, int(5 * scale)))
            self.scroll_frame.grid_configure(padx=padding, pady=padding)
    
    def _open_preview_window(self):
        """Open the real-time preview window"""
        if self.preview_window and self.preview_window.winfo_exists():
            self.preview_window.lift()
            return
            
        self.preview_window = ctk.CTkToplevel(self.root)
        self.preview_window.title("Live Preview")
        self.preview_window.geometry("640x480")
        self.preview_window.minsize(320, 240)
        
        # Position preview window to the right of main window
        main_x = self.root.winfo_x()
        main_y = self.root.winfo_y()
        main_width = self.root.winfo_width()
        self.preview_window.geometry(f"+{main_x + main_width + 20}+{main_y}")
        
        # Create preview canvas
        canvas_frame = ctk.CTkFrame(self.preview_window, fg_color="transparent")
        canvas_frame.pack(expand=True, fill="both", padx=10, pady=10)
        
        self.preview_canvas_label = ctk.CTkLabel(canvas_frame, text="No preview available\nSelect PDFs and enter text to see preview")
        self.preview_canvas_label.pack(expand=True)
        
        # Handle window close
        self.preview_window.protocol("WM_DELETE_WINDOW", self._on_preview_window_close)
        
        # Start real-time updates
        self._schedule_preview_update()
    
    def _on_preview_window_close(self):
        """Handle preview window close"""
        self.preview_running = False
        if self.preview_sound:
            self.preview_sound.stop()
        if self.preview_window:
            self.preview_window.destroy()
            self.preview_window = None
    
    def _schedule_preview_update(self):
        """Schedule a preview update with debouncing"""
        if self.preview_update_pending:
            return
            
        self.preview_update_pending = True
        self.preview_cancel_event.set()  # Cancel any running generation
        self.root.after(self.preview_update_delay, self._update_preview)
    
    def _update_preview(self):
        """Update the preview based on current settings"""
        with self.preview_lock:
            self.preview_update_pending = False
            
            # Check if we have the minimum required data
            text = self.entry_text.get().strip() if hasattr(self, 'entry_text') else ""
            if not self.pdf_files or not text:
                if self.preview_window and self.preview_window.winfo_exists():
                    self.preview_canvas_label.configure(text="No preview available\nSelect PDFs and enter text to see preview")
                return
            
            # Check if settings have changed
            current_settings = self.get_settings()
            settings_hash = self._hash_settings(current_settings, text)
            
            if settings_hash == self._last_settings_hash:
                return  # No changes, skip update
                
            self._last_settings_hash = settings_hash
            
            # Cancel any existing thread
            self.preview_cancel_event.set()
            
            # Generate preview frames in background
            self.update_status("🎬 Updating preview...")
            self.preview_thread = threading.Thread(
                target=self._generate_preview_frames, 
                args=(text, current_settings), 
                daemon=True
            )
            self.preview_thread.start()
    
    def _hash_settings(self, settings, text):
        """Create a hash of current settings to detect changes"""
        import hashlib
        settings_str = f"{text}|{settings}|{','.join(self.pdf_files)}"
        return hashlib.md5(settings_str.encode()).hexdigest()
    
    def _generate_preview_frames(self, text, settings):
        """Generate preview frames in background with cancellation support"""
        self.preview_cancel_event.clear()
        
        try:
            # Create a copy of settings with lower resolution for faster preview
            preview_settings = settings.copy()
            preview_settings['preview_mode'] = True
            preview_settings['preview_dpi'] = 100  # Lower DPI for faster processing
            
            # Check cache first
            cache_key = self._hash_settings(settings, text)
            if cache_key in self.preview_cache:
                if self.preview_cancel_event.is_set():
                    return
                self.generated_frames = self.preview_cache[cache_key]
                self.preview_cache_key = cache_key
                self.root.after(0, lambda: self._start_preview_playback())
                self.root.after(0, lambda: self.update_status(f"✅ Preview: {len(self.generated_frames)} frames (cached)"))
                return
            
            # Generate frames with periodic cancellation checks
            frames = []
            def progress_callback(msg):
                if self.preview_cancel_event.is_set():
                    raise InterruptedError("Preview generation cancelled")
            
            frames = self.pdf_processor.get_frames(
                self.pdf_files[:1] if len(self.pdf_files) > 1 else self.pdf_files,  # Process only first PDF for speed
                text, preview_settings, progress_callback
            )
            
            if self.preview_cancel_event.is_set():
                return
            
            if frames:
                self.generated_frames = frames
                # Limit cache size to prevent memory issues (max 3 entries)
                if len(self.preview_cache) >= 3:
                    oldest_key = next(iter(self.preview_cache))
                    del self.preview_cache[oldest_key]
                self.preview_cache[cache_key] = frames  # Cache the frames
                self.preview_cache_key = cache_key
                self.root.after(0, lambda: self._start_preview_playback())
                self.root.after(0, lambda: self.update_status(f"✅ Preview: {len(frames)} frames"))
            else:
                self.root.after(0, lambda: self.update_status("❌ No matches found"))
                if self.preview_window and self.preview_window.winfo_exists():
                    self.root.after(0, lambda: self.preview_canvas_label.configure(text="No matches found\nTry different text or PDFs"))
        except InterruptedError:
            pass  # Silently ignore cancelled operations
        except Exception as e:
            self.root.after(0, lambda: self.update_status(f"❌ Preview error: {e}"))
    
    def _start_preview_playback(self):
        """Start playing the preview frames"""
        if not self.generated_frames or not self.preview_window or not self.preview_window.winfo_exists():
            return
        
        # Clear resized frames cache when new frames arrive
        self._preview_resized_frames = []
        self._last_preview_size = None
            
        self.preview_running = True
        self.current_frame_idx = 0
        self._play_next_frame()
    
    def _play_next_frame(self):
        """Play the next frame in the preview (optimized)"""
        if not self.preview_running or not self.preview_window or not self.preview_window.winfo_exists():
            return
        
        if not self.generated_frames:
            return
        
        # Batch process: pre-resize all frames for current window size on first run
        if not hasattr(self, '_preview_resized_frames') or self._preview_size_changed():
            self._resize_preview_frames()
        
        # Display current frame
        if hasattr(self, '_preview_resized_frames') and self._preview_resized_frames:
            tk_img = self._preview_resized_frames[self.current_frame_idx]
            self.preview_canvas_label.configure(image=tk_img, text="")
            self.preview_canvas_label.image = tk_img
        
        # Move to next frame
        self.current_frame_idx = (self.current_frame_idx + 1) % len(self.generated_frames)
        
        # Check for settings updates periodically (every loop)
        if self.current_frame_idx == 0:
            self._schedule_preview_update()
        
        # Calculate next frame timing
        try:
            current_wps = float(self.var_wps.get()) if hasattr(self, 'var_wps') else 1.5
            if current_wps <= 0:
                current_wps = 1.5
        except:
            current_wps = 1.5
            
        current_speed_ms = int((1.0 / current_wps) * 1000)
        self.preview_window.after(current_speed_ms, self._play_next_frame)
    
    def _preview_size_changed(self):
        """Check if preview window size changed"""
        if not hasattr(self, '_last_preview_size'):
            return True
        current_w = self.preview_window.winfo_width()
        current_h = self.preview_window.winfo_height()
        return (current_w, current_h) != self._last_preview_size
    
    def _resize_preview_frames(self):
        """Pre-resize all frames for smoother playback"""
        if not self.generated_frames or not self.preview_window:
            return
            
        # Calculate display size
        preview_w = max(320, self.preview_window.winfo_width() - 40)
        preview_h = max(240, self.preview_window.winfo_height() - 60)
        
        # Maintain aspect ratio
        orientation = self.var_orientation.get() if hasattr(self, 'var_orientation') else "16:9"
        target_ratio = 16/9 if orientation == "16:9" else 9/16
        
        display_w = int(preview_h * target_ratio)
        display_h = preview_h
        
        if display_w > preview_w:
            display_w = preview_w
            display_h = int(preview_w / target_ratio)
        
        # Store size to detect changes
        self._last_preview_size = (self.preview_window.winfo_width(), self.preview_window.winfo_height())
        
        # Pre-resize all frames using faster NEAREST for preview
        self._preview_resized_frames = []
        for pil_img in self.generated_frames:
            display_img = pil_img.resize((display_w, display_h), Image.Resampling.NEAREST)
            self._preview_resized_frames.append(ImageTk.PhotoImage(display_img))
    
    def _update_preview_window_size(self):
        """Update preview window size when main window moves"""
        if not self.preview_window or not self.preview_window.winfo_exists():
            return
        # Preview window maintains its own size, just ensure it's visible
        self.preview_window.lift()
    
    def _trigger_preview_update(self, *args):
        """Trigger a preview update (called when settings change)"""
        if self.preview_window and self.preview_window.winfo_exists():
            self._schedule_preview_update()
            
    def _load_saved_settings(self):
        """Load settings from configuration"""
        geometry = self.config_manager.get("window_geometry")
        
        if geometry:
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
        
        # Open preview window automatically after a short delay
        self.root.after(1000, self._open_preview_window)
                
    def select_pdfs(self):
        """Handle PDF file selection"""
        files = filedialog.askopenfilenames(filetypes=[("PDF Files", "*.pdf")])
        if files:
            self.pdf_files = list(files)
            self.lbl_file_count.configure(text=f"📁 {len(files)} files selected")
            
            for pdf_file in files:
                self.config_manager.add_recent_pdf(pdf_file)
            
            # Trigger preview update
            self._trigger_preview_update()
                
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
        
    def _save_to_quick_command(self):
        """Save current settings to quick command config"""
        try:
            gui_settings = {
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
                "default_audio": self.entry_audio.get() if hasattr(self, 'entry_audio') else ""
            }
            
            if QuickCommandConfig.save_from_gui(gui_settings):
                self.update_status("✅ Settings saved to quickcommand.txt")
                from tkinter import messagebox
                messagebox.showinfo("Success", "Settings saved to quickcommand.txt!\n\nYou can now run CLI mode with:\npython main.py --cli")
            else:
                self.update_status("❌ Failed to save quick command settings")
        except Exception as e:
            self.update_status(f"❌ Error saving quick command: {e}")
    
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
            "window_geometry": self.root.geometry()
        })
        
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

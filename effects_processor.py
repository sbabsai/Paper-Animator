import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps
from typing import Tuple


class EffectsProcessor:
    """Handles all visual effects and image processing for PyMuPDF-extracted content"""
    
    def apply_all_effects(self, img: Image.Image, text_width: float, text_height: float, 
                         settings: dict) -> Image.Image:
        """
        Apply all selected effects to an image
        
        Args:
            img: Input PIL Image
            text_width: Width of the text region (in pixels)
            text_height: Height of the text region (in pixels)
            settings: Dictionary of effect settings
        """
        if settings.get('dark_theme'):
            img = ImageOps.invert(img)
        
        if settings.get('highlight'):
            img = self._apply_highlight(img, text_width, text_height, settings)
        
        blur_type = settings.get('blur_type', 'None')
        blur_intensity = settings.get('blur_intensity', 'Low')
        
        if blur_type != 'None':
            if blur_type == 'Gaussian':
                radius = self._get_blur_radius(blur_intensity, 'gaussian')
                img = img.filter(ImageFilter.GaussianBlur(radius=radius))
            elif blur_type == 'Vertical':
                img = self._apply_vertical_blur(img, blur_intensity)
            elif blur_type == 'Radial (Center Clear)':
                img = self._apply_radial_blur(img, blur_intensity)
        
        if settings.get('chromatic'):
            img = self._apply_chromatic_aberration(img, offset=6)
        
        if settings.get('paper'):
            img = self._apply_paper_texture(img, intensity=0.08)
        
        return img
    
    def _apply_chromatic_aberration(self, img: Image.Image, offset: int = 5) -> Image.Image:
        r, g, b = img.split()
        r_data = np.array(r)
        g_data = np.array(g)
        b_data = np.array(b)
        r_shifted = np.roll(r_data, -offset, axis=1)
        b_shifted = np.roll(b_data, offset, axis=1)
        new_r = Image.fromarray(r_shifted)
        new_b = Image.fromarray(b_shifted)
        return Image.merge("RGB", (new_r, g, new_b))
    
    def _apply_paper_texture(self, img: Image.Image, intensity: float = 0.1) -> Image.Image:
        img_arr = np.array(img)
        noise = np.random.randint(0, 255, img_arr.shape, dtype='uint8')
        noise_img = Image.fromarray(noise, 'RGB')
        return Image.blend(img, noise_img, alpha=intensity)
    
    def _apply_vertical_blur(self, img: Image.Image, intensity: str) -> Image.Image:
        size = self._get_kernel_size(intensity)
        kernel = [0] * (size * size)
        for i in range(size):
            kernel[i * size + (size // 2)] = 1
        summ = sum(kernel)
        kernel = [k / summ for k in kernel]
        return img.filter(ImageFilter.Kernel((size, size), kernel))
    
    def _apply_radial_blur(self, img: Image.Image, intensity: str) -> Image.Image:
        radius = self._get_blur_radius(intensity, 'radial')
        blurred_img = img.filter(ImageFilter.GaussianBlur(radius=radius))
        w, h = img.size
        Y, X = np.ogrid[:h, :w]
        center_y, center_x = h / 2, w / 2
        dist_from_center = np.sqrt((X - center_x)**2 + (Y - center_y)**2)
        max_dist = np.sqrt(center_x**2 + center_y**2)
        normalized_dist = dist_from_center / max_dist
        mask_arr = np.clip((normalized_dist - 0.2) * 3, 0, 1) * 255
        mask_img = Image.fromarray(mask_arr.astype('uint8'), 'L')
        return Image.composite(blurred_img, img, mask_img)
    
    def _apply_highlight(self, img: Image.Image, text_width: float, text_height: float, 
                        settings: dict) -> Image.Image:
        """Apply realistic highlighter effect using pixel-based dimensions from PyMuPDF"""
        draw = ImageDraw.Draw(img, "RGBA")
        
        size_multiplier = settings.get('size_multiplier', 1.0)
        
        img_w, img_h = img.size
        img_cx, img_cy = img_w / 2, img_h / 2
        
        highlight_width = text_width * size_multiplier
        highlight_height = text_height * size_multiplier
        
        h_x0 = img_cx - (highlight_width / 2)
        h_y0 = img_cy - (highlight_height / 2)
        h_x1 = img_cx + (highlight_width / 2)
        h_y1 = img_cy + (highlight_height / 2)
        
        if size_multiplier > 1.0:
            padding_x = text_width * 0.15
            padding_y = text_height * 0.15
            h_x0 -= padding_x
            h_y0 -= padding_y
            h_x1 += padding_x
            h_y1 += padding_y
        
        if settings.get('dark_theme'):
            highlight_color = (0, 0, 255, 90)
        else:
            highlight_color = (255, 255, 0, 90)
            
        draw.rounded_rectangle([h_x0, h_y0, h_x1, h_y1], radius=8, fill=highlight_color)
        
        return img
    
    def _get_kernel_size(self, intensity: str) -> int:
        if intensity == 'Low': return 10
        if intensity == 'Medium': return 25
        if intensity == 'High': return 45
        return 15
    
    def _get_blur_radius(self, intensity: str, blur_type: str) -> int:
        if blur_type == 'gaussian':
            if intensity == 'Low': return 2
            if intensity == 'Medium': return 5
            if intensity == 'High': return 10
        elif blur_type == 'radial':
            if intensity == 'Low': return 4
            if intensity == 'Medium': return 8
            if intensity == 'High': return 15
        return 5
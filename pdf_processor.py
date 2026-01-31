import fitz
import os
from typing import List, Callable, Tuple
from PIL import Image


class PDFProcessor:
    """Handles PDF text extraction and frame generation"""
    
    def __init__(self):
        self.stop_event = False
    
    def get_frames(self, pdf_paths: List[str], search_text: str, settings: dict, 
                   progress_callback: Callable[[str], None] = None) -> List[Image.Image]:
        """
        Extract frames from PDF files based on search text
        """
        found_frames = []
        
        for i, pdf_path in enumerate(pdf_paths):
            if self.stop_event:
                break
                
            try:
                if not os.path.exists(pdf_path):
                    if progress_callback:
                        progress_callback(f"Skipping missing file: {os.path.basename(pdf_path)}")
                    continue
                    
                doc = fitz.open(pdf_path)
                
                if doc.is_encrypted:
                    if progress_callback:
                        progress_callback(f"Skipping encrypted file: {os.path.basename(pdf_path)}")
                    doc.close()
                    continue
                
                for page_num, page in enumerate(doc):
                    text_instances = page.search_for(search_text)
                    for rect in text_instances:
                        if self.stop_event:
                            break
                            
                        frame = self._process_frame(page, rect, settings)
                        found_frames.append(frame)
                        
                        if progress_callback:
                            progress_callback(f"Processed match in {os.path.basename(pdf_path)} (Page {page_num + 1})")
                            
                doc.close()
                
            except fitz.FitzError as e:
                if progress_callback:
                    progress_callback(f"PDF error in {os.path.basename(pdf_path)}: {str(e)}")
            except Exception as e:
                if progress_callback:
                    progress_callback(f"Unexpected error in {os.path.basename(pdf_path)}: {str(e)}")
                    
        return found_frames
    
    def _process_frame(self, page, rect, settings: dict) -> Image.Image:
        """
        Process a single text instance into a frame
        """
        from effects_processor import EffectsProcessor
        
        effects = EffectsProcessor()
        
        orientation = settings.get('orientation', '16:9')
        if orientation == '16:9':
            target_w, target_h = 1920, 1080
            aspect_ratio = 1920 / 1080
        else:
            target_w, target_h = 1080, 1920
            aspect_ratio = 1080 / 1920

        text_width = rect.x1 - rect.x0
        text_height = rect.y1 - rect.y0
        text_center_x = (rect.x0 + rect.x1) / 2
        text_center_y = (rect.y0 + rect.y1) / 2

        zoom_factor = 4.0 
        view_w = text_width * zoom_factor
        view_h = view_w / aspect_ratio

        if view_h < text_height * 1.5:
            view_h = text_height * 2.0
            view_w = view_h * aspect_ratio

        crop_rect = fitz.Rect(
            text_center_x - (view_w / 2),
            text_center_y - (view_h / 2),
            text_center_x + (view_w / 2),
            text_center_y + (view_h / 2)
        )

        dpi_scale = target_w / view_w
        
        scaled_text_w = text_width * dpi_scale
        scaled_text_h = text_height * dpi_scale
        
        mat = fitz.Matrix(dpi_scale, dpi_scale)
        pix = page.get_pixmap(matrix=mat, clip=crop_rect, alpha=False)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        
        img = img.resize((target_w, target_h), Image.Resampling.LANCZOS)

        img = effects.apply_all_effects(img, scaled_text_w, scaled_text_h, settings)
        
        return img
    
    def stop_processing(self):
        self.stop_event = True
import numpy as np
from PIL import Image
from moviepy import ImageSequenceClip, AudioFileClip, concatenate_audioclips, AudioClip
import os


class VideoRenderer:
    """Handles video rendering and audio integration"""
    
    def __init__(self):
        pass
    
    def save_video(self, frames: list, output_path: str, audio_path: str = None, 
                   wps: float = 1.5, fps: int = 24) -> bool:
        """
        Save frames as a video with optional audio
        
        Args:
            frames: List of PIL Images to render as video
            output_path: Path where to save the video
            audio_path: Optional path to audio file
            wps: Words per second (controls timing)
            fps: Frames per second for output video
            
        Returns:
            True if successful, False otherwise
        """
        if not frames:
            return False
        
        duration_per_clip = 1.0 / wps
        total_clips = len(frames)
        print(f"Saving Video: {total_clips} frames. WPS: {wps}. Duration per frame: {duration_per_clip}s")

        numpy_frames = [np.array(img) for img in frames]
        clip = ImageSequenceClip(numpy_frames, durations=[duration_per_clip] * total_clips)
        
        if audio_path and os.path.exists(audio_path):
            try:
                sound_effect = AudioFileClip(audio_path)
                
                if sound_effect.duration > duration_per_clip:
                    audio_unit = sound_effect.subclip(0, duration_per_clip)
                else:
                    padding_duration = duration_per_clip - sound_effect.duration
                    
                    n_channels = sound_effect.nchannels
                    make_frame_silence = lambda t: [0] * n_channels
                    
                    silence = AudioClip(make_frame_silence, duration=padding_duration, fps=sound_effect.fps)
                    audio_unit = concatenate_audioclips([sound_effect, silence])
                
                full_audio_list = [audio_unit] * total_clips
                final_audio = concatenate_audioclips(full_audio_list)
                
                clip = clip.set_audio(final_audio)
                
            except Exception as e:
                print(f"Audio Processing Error: {e}")

        try:
            clip.write_videofile(
                output_path, 
                codec='libx264', 
                audio_codec='aac', 
                fps=fps,
                preset='medium',
                logger='bar'
            )
        except Exception as e:
            print(f"Video rendering error: {e}")
            return False
        finally:
            try:
                if 'sound_effect' in locals():
                    sound_effect.close()
                clip.close()
            except:
                pass
                
        return True
    
    def get_preview_audio_duration(self, audio_path: str) -> float:
        """
        Get the duration of an audio file for preview purposes
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Duration in seconds, or 0.0 if error/doesn't exist
        """
        if not audio_path or not os.path.exists(audio_path):
            return 0.0
            
        try:
            audio_clip = AudioFileClip(audio_path)
            duration = audio_clip.duration
            audio_clip.close()
            return duration
        except Exception as e:
            print(f"Error reading audio duration: {e}")
            return 0.0
    
    def estimate_file_size(self, frames: list, duration_per_frame: float, fps: int = 24) -> str:
        """
        Estimate the output file size
        
        Args:
            frames: List of frames
            duration_per_frame: Duration per frame in seconds
            fps: Frames per second
            
        Returns:
            Estimated file size as human-readable string
        """
        if not frames:
            return "0 MB"
            
        total_duration = len(frames) * duration_per_frame
        estimated_mb = total_duration * 1.5
        
        if estimated_mb > 1024:
            return f"{estimated_mb/1024:.1f} GB"
        else:
            return f"{estimated_mb:.1f} MB"
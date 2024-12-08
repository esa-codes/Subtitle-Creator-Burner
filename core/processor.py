# core/processor.py

import whisper
import subprocess
import os
from pathlib import Path
import shutil
import json
import logging
from datetime import timedelta
from typing import Dict

from core.model_info import ModelInfo
from utils.translator import SubtitleTranslator

class SubtitleProcessor:
    """Manages the creation and processing of subtitles."""

    def __init__(self):
        # Conf logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('subtitle_app.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

        # Cache directory
        self.cache_dir = Path.home() / '.cache' / 'whisper'
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Initialize the translator
        self.translator = SubtitleTranslator()

        # Current model
        self.current_model = None

        # Processing state
        self.processing = False

    def format_timestamp(self, seconds: float) -> str:
        """Converts seconds to SRT timestamp format."""
        td = timedelta(seconds=seconds)
        hours = td.seconds//3600
        minutes = (td.seconds//60)%60
        seconds = td.seconds%60
        milliseconds = td.microseconds//1000
        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"

    def extract_audio(self, video_path: str) -> str:
        """Extract audio from video."""
        self.logger.info("Extracting audio from video")
        audio_path = os.path.splitext(video_path)[0] + "_temp.wav"

        try:
            cmd = [
                'ffmpeg',
                '-i', video_path,
                '-vn',
                '-acodec', 'pcm_s16le',
                '-ar', '16000',
                '-ac', '1',
                audio_path,
                '-y'
            ]

            shell = True if os.name == 'nt' else False
            result = subprocess.run(
                cmd,
                shell=shell,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            if result.returncode != 0:
                raise Exception(f"FFmpeg error: {result.stderr}")

            return audio_path

        except Exception as e:
            self.logger.error(f"Error extracting audio: {str(e)}")
            raise


    def is_model_downloaded(self, model_name: str) -> bool:
        """Check if a model is already downloaded."""
        if model_name == "large":
            model_path = self.cache_dir / "large-v3.pt"
        else:
            model_path = self.cache_dir / f"{model_name}.pt"
        return model_path.exists()

    def check_disk_space(self, required_bytes: int) -> bool:
        """Check if there is enough disk space."""
        free_space = shutil.disk_usage(self.cache_dir).free
        return free_space > required_bytes * 1.2

    def download_model(self, model_name: str) -> bool:
        """Download a Whisper model."""
        try:
            required_space = ModelInfo.SIZES[model_name]['size']
            if not self.check_disk_space(required_space):
                raise Exception("Insufficient disk space")

            import os
            import whisper

            # Set Whisper's download directory to our cache directory
            os.environ["XDG_CACHE_HOME"] = str(self.cache_dir.parent)

            if self.current_model is not None:
                del self.current_model
                import gc
                gc.collect()

            self.current_model = whisper.load_model(model_name)
            return True

        except Exception as e:
            self.logger.error(f"Error downloading model: {str(e)}")
            raise

    def create_subtitles(self, video_path: str, srt_path: str, model_name: str,
                        language: str = "auto", progress_callback=None) -> bool:
        """Create subtitles for a video."""
        try:
            if progress_callback:
                progress_callback("Loading model...", 10)

            if not self.current_model:
                self.current_model = whisper.load_model(model_name)

            # Backup existing SRT file if needed
            if os.path.exists(srt_path):
                backup_path = srt_path + '.bak'
                shutil.copy2(srt_path, backup_path)

            if progress_callback:
                progress_callback("Extracting audio...", 20)

            # Estract audio
            audio_path = self.extract_audio(video_path)

            if progress_callback:
                progress_callback("Transcribing audio...", 40)

            # Transcribe audio
            options = {
                "language": None if language == "auto" else language,
                "task": "transcribe",
                "verbose": False
            }

            result = self.current_model.transcribe(audio_path, **options)

            if progress_callback:
                progress_callback("Creating SRT file...", 80)

            # Create SRT file
            srt_content = []
            for i, seg in enumerate(result["segments"], 1):
                start_time = self.format_timestamp(seg["start"])
                end_time = self.format_timestamp(seg["end"])
                text = seg["text"].strip()
                srt_content.extend([
                    str(i),
                    f"{start_time} --> {end_time}",
                    text + "\n"
                ])

            with open(srt_path, 'w', encoding='utf-8') as f:
                f.write("\n".join(srt_content))

            # Clean temporary files
            os.remove(audio_path)

            if progress_callback:
                progress_callback("Subtitles created successfully!", 100)

            return True

        except Exception as e:
            self.logger.error(f"Error creating subtitles: {str(e)}")
            raise

    def burn_subtitles(self, input_video: str, srt_path: str, output_video: str = None,
                       font_size: str = "24", font_name: str = "Arial",
                       font_color: str = "white", font_outline: str = "black",
                       video_quality: str = "23", video_preset: str = "medium",
                       background_color: str = "none", uppercase: bool = False,
                       word_by_word: bool = False, subtitle_position: str = "bottom",
                       margin_left: int = 50,
                       progress_callback=None) -> bool:
        try:
            if progress_callback:
                progress_callback("Preparing burning process...", 10)

            if output_video is None:
                output_video = os.path.splitext(input_video)[0] + "_subbed.mp4"

            # Modify subtitle file if needed
            if uppercase or word_by_word:
                modified_srt_path = self.modify_subtitle_file(srt_path, uppercase, word_by_word)
            else:
                modified_srt_path = srt_path


            # Prepare style with additional options
            style_components = [
                f"FontSize={font_size}",
                f"FontName={font_name}",
                f"PrimaryColour={self.convert_color_to_hex(font_color)}",
                f"OutlineColour={self.convert_color_to_hex(font_outline)}",
                f"MarginL={margin_left}",
                f"MarginR=50",
                f"MarginV=20",
                "Outline=1",
                "Shadow=1"
            ]


            # Add subtitle positioning
            style_components.append(f"Alignment={self._get_alignment(subtitle_position)}")

            # Add background color if specified
            if background_color == "none":
                style_components.extend([
                    "BorderStyle=1",
                    "Outline=1"
                ])
            else:
                # Configure background
                style_components.extend([
                    f"BackColour={self.convert_color_to_hex(background_color)}",
                    "BorderStyle=3",
                    "Outline=1"
                ])


            style = ",".join(style_components)


            if progress_callback:
                progress_callback("Burning subtitles...", 30)

            ffmpeg_cmd = [
                'ffmpeg', '-i', input_video,
                '-vf', f"subtitles='{modified_srt_path}':force_style='{style}'",
                '-c:v', 'libx264',
                '-preset', video_preset,
                '-crf', video_quality,
                '-c:a', 'aac',
                '-b:a', '192k',
                output_video,
                '-y'
            ]

            process = subprocess.Popen(
                ffmpeg_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )

            stdout, stderr = process.communicate()

            if process.returncode != 0:
                raise RuntimeError(f"FFmpeg error: {stderr}")

            # Clean up modified subtitle file if it was created
            if modified_srt_path != srt_path:
                os.remove(modified_srt_path)

            if progress_callback:
                progress_callback("Burning completed!", 100)

            return True

        except Exception as e:
            self.logger.error(f"Error burning subtitles: {str(e)}")
            raise

    def modify_subtitle_file(self, input_srt: str, uppercase: bool = False, word_by_word: bool = False) -> str:
        """Modify subtitle file based on specified options."""
        try:
            # Create a new modified SRT file
            output_srt = os.path.splitext(input_srt)[0] + "_modified.srt"

            with open(input_srt, 'r', encoding='utf-8') as infile, \
                 open(output_srt, 'w', encoding='utf-8') as outfile:

                for line in infile:
                    # Check if this is a subtitle text line
                    if '-->' not in line and line.strip().isdigit() == False and line.strip():
                        text = line.strip()

                        # Apply uppercase if selected
                        if uppercase:
                            text = text.upper()

                        # Apply word-by-word if selected
                        if word_by_word:
                            text = ' '.join([word for word in text.split()])

                        outfile.write(text + '\n')
                    else:
                        # Write other lines as they are
                        outfile.write(line)

            return output_srt

        except Exception as e:
            self.logger.error(f"Error modifying subtitle file: {str(e)}")
            raise

    def convert_color_to_hex(self, color_name: str) -> str:
        """Converts color name to hexadecimal format for FFmpeg subtitles (BGR format)."""
        color_map = {
            'white': '&HFFFFFF&',    # BGR: 255,255,255
            'yellow': '&H00FFFF&',   # BGR: 0,255,255
            'black': '&H000000&',    # BGR: 0,0,0
            'green': '&H00FF00&',    # BGR: 0,255,0
            'cyan': '&HFFFF00&',     # BGR: 255,255,0
            'gray': '&H808080&',     # BGR: 128,128,128
            'none': ''               # Nessun colore
        }
        return color_map.get(color_name.lower(), '&HFFFFFF&')



    def translate_subtitles(self, input_srt: str, from_lang: str, to_lang: str) -> str:
        """Translate subtitles."""
        try:
            output_srt = os.path.splitext(input_srt)[0] + f"_{to_lang}.srt"
            self.translator.translate_srt(input_srt, output_srt, from_lang, to_lang)
            return output_srt
        except Exception as e:
            self.logger.error(f"Error translating subtitles: {str(e)}")
            raise

    def _get_alignment(self, position: str) -> str:
        """Convert position to FFmpeg subtitle alignment."""
        alignment_map = {
            "top center": "8",     # Top center
            "bottom": "2"          # Bottom center (default)
        }
        return alignment_map.get(position, "2")  # Default to bottom


    def load_settings(self) -> Dict:
        """Load saved settings."""
        try:
            settings_path = Path.home() / '.subtitle_app' / 'settings.json'
            if settings_path.exists():
                with open(settings_path, 'r') as f:
                    settings = json.load(f)
                    self.logger.info("Settings loaded successfully")
                    return settings
            return {
                'font_size': "24",
                'font_name': "Arial",
                'font_color': "white",
                'font_outline': "black",
                'background_color': "none",
                'uppercase': False,
                'word_by_word': False,
                'whisper_model': "base",
                'whisper_language': "auto",
                'video_quality': "23",
                'video_preset': "medium"
            }
        except Exception as e:
            self.logger.error(f"Error loading settings: {str(e)}")
            raise

    def save_settings(self, settings: Dict) -> bool:
        """Save the current settings."""
        try:
            settings_path = Path.home() / '.subtitle_app'
            settings_path.mkdir(parents=True, exist_ok=True)
            with open(settings_path / 'settings.json', 'w') as f:
                json.dump(settings, f, indent=4)
            self.logger.info("Settings saved successfully")
            return True
        except Exception as e:
            self.logger.error(f"Error saving settings: {str(e)}")
            raise

    def update_all_model_status(self) -> Dict[str, bool]:
        """Update the status of all models."""
        status = {}
        for model in ModelInfo.SIZES.keys():
            is_downloaded = self.is_model_downloaded(model)
            status[model] = is_downloaded
            if is_downloaded:
                self.logger.info(f"Model {model} is already downloaded")
        return status

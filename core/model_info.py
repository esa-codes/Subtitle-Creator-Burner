# core/model_info.py

import humanize

class ModelInfo:
    """Information about available Whisper models."""

    SIZES = {
        'tiny': {'size': 150_000_000, 'desc': 'Fastest, least accurate'},
        'base': {'size': 400_000_000, 'desc': 'Fast, decent accuracy'},
        'small': {'size': 1_000_000_000, 'desc': 'Balanced speed/accuracy'},
        'medium': {'size': 3_000_000_000, 'desc': 'Slower, more accurate'},
        'large': {'size': 6_000_000_000, 'desc': 'Slowest, most accurate'}
    }

    LANGUAGES = {
        'auto': 'Auto Detect',
        'en': 'English',
        'it': 'Italian',
        'fr': 'French',
        'de': 'German',
        'es': 'Spanish',
        'pt': 'Portuguese',
        'nl': 'Dutch',
        'ru': 'Russian',
        'zh': 'Chinese',
        'ja': 'Japanese',
        'ko': 'Korean'
    }

    @staticmethod
    def get_model_info(model_name: str) -> str:
        """Returns formatted information about the model."""
        info = ModelInfo.SIZES.get(model_name, {})
        size_str = humanize.naturalsize(info.get('size', 0), binary=True)
        desc = info.get('desc', '')
        return f"{model_name} ({size_str}) - {desc}"

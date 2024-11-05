# translator.py
from deep_translator import GoogleTranslator
import re

class SubtitleTranslator:
    def __init__(self):
        self.supported_languages = GoogleTranslator().get_supported_languages()

    def translate_srt(self, input_file: str, output_file: str, from_lang: str, to_lang: str) -> None:
        """Translates an SRT file from one language to another."""
        try:
            translator = GoogleTranslator(source=from_lang, target=to_lang)

            with open(input_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # divide the content into blocks (each subtitle is a block)
            blocks = content.strip().split('\n\n')
            translated_blocks = []

            for block in blocks:
                lines = block.split('\n')
                if len(lines) >= 3:
                    # Keep the subtitle number
                    number = lines[0]
                    # Keep the timestamp
                    timestamp = lines[1]
                    # Merge and translate text
                    text = ' '.join(lines[2:])
                    translated_text = translator.translate(text)

                    # Recreate the block
                    translated_block = f"{number}\n{timestamp}\n{translated_text}\n"
                    translated_blocks.append(translated_block)

            # Save the translated file
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(translated_blocks))

            return True

        except Exception as e:
            raise Exception(f"Error translating subtitles: {str(e)}")

    def get_supported_languages(self):
        """Returns the list of supported languages."""
        return self.supported_languages

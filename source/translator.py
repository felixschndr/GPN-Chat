import json
import os

from transformers import MarianMTModel, MarianTokenizer

from source.git_root_finder import GitRootFinder
from source.logger import LoggerMixin


class Translator(LoggerMixin):
    """
    The `Translator` class is responsible for translating text from one language to another.
    Start the translation process by calling the `start()` method.
    """

    def __init__(self, target_language: str = "de"):
        super().__init__()

        self.target_language = target_language

        model_name_source_english = f"Helsinki-NLP/opus-mt-en-{target_language}"
        model_name_source_german = f"Helsinki-NLP/opus-mt-de-{target_language}"

        self.translation_model_source_english = MarianMTModel.from_pretrained(
            model_name_source_english
        )
        self.tokenizer_source_english = MarianTokenizer.from_pretrained(
            model_name_source_english
        )

        self.translation_model_source_german = MarianMTModel.from_pretrained(
            model_name_source_german
        )
        self.tokenizer_source_german = MarianTokenizer.from_pretrained(
            model_name_source_german
        )

        data_directory = os.path.join(GitRootFinder.get(), "data")
        self.metadata_directory = os.path.join(data_directory, "metadata")
        self.transcription_directory = os.path.join(data_directory, "transcriptions")

    def translate_text(self, text_to_translate: str, source_language: str) -> str:
        """
        Translate text from one language to another.

        :param text_to_translate: The text to be translated.
        :param source_language: The language of the text to be translated.
        :return: The translated text.

        Example:
            translator = Translator()
            translated_text = translator.translate_text("Hello", "en")
            print(translated_text)  # Output: "Hallo"
        """
        if source_language == "en":
            tokenizer = self.tokenizer_source_english
            translation_model = self.translation_model_source_english
        else:
            tokenizer = self.tokenizer_source_german
            translation_model = self.translation_model_source_german

        inputs = tokenizer([text_to_translate], return_tensors="pt", padding=True)
        translated = translation_model.generate(**inputs)
        translated_text = tokenizer.decode(translated[0], skip_special_tokens=True)

        return translated_text

    def start(self) -> None:
        """
        This method is used to start the translation process for metadata files.

        :return: None
        """
        for metadata_file_name in os.listdir(self.metadata_directory):
            with open(
                os.path.join(self.metadata_directory, metadata_file_name),
                mode="r",
                encoding="utf-8",
            ) as file:
                metadata = json.load(file)
                language = metadata["language"]

                if language == self.target_language:
                    self.log.debug(
                        f"{metadata_file_name} has the correct language, skipping..."
                    )
                    continue

                self.log.info(
                    f"Translating {metadata_file_name} from {language} to {self.target_language}"
                )

                transcription_file_name = metadata_file_name.replace(".json", ".txt")
                transcription_file_path = os.path.join(
                    self.transcription_directory, transcription_file_name
                )
                with open(
                    transcription_file_path, mode="rw", encoding="utf-8"
                ) as transcription_file:
                    transcription = transcription_file.read()
                    translated_text = self.translate_text(transcription, language)

                    transcription_file.seek(0)
                    transcription_file.truncate()
                    transcription_file.write(translated_text)

                    self.log.debug(
                        f"Translated text written to {transcription_file_path}"
                    )


if __name__ == "__main__":
    translator = Translator(target_language="de")
    print(translator.start())

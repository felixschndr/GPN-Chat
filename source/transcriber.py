import os
import threading
from shutil import which

import whisper
from dotenv import load_dotenv

from source.git_root_finder import GitRootFinder
from source.logger import LoggerMixin


class Transcriber(LoggerMixin):
    """
    This module contains the `Transcriber` class, which is used to transcribe audio files to text.
    """

    def __init__(self):
        super().__init__()

        load_dotenv()

        self.transcriber_model_name = os.getenv("TRANSCRIBER_MODEL")
        self.log.debug(f'Using model "{self.transcriber_model_name}" for transcription')

        self._check_for_ffmpeg()
        self._find_audio_files()

    @staticmethod
    def _check_for_ffmpeg() -> None:
        """
        Check for the presence of ffmpeg.

        :return: None
        """
        if not which("ffmpeg"):
            raise SystemError("ffmpeg is not installed!")

    def _find_audio_files(self) -> None:
        """
        This method is used to find audio files in a specific directory and set the input and output directories for audio processing.

        :return: None
        """
        data_directory = os.path.join(GitRootFinder.get(), "data")
        self.audio_input_directory = os.path.join(data_directory, "audio")
        self.transcription_output_directory = os.path.join(
            data_directory, "transcriptions"
        )

        if not os.path.exists(self.transcription_output_directory):
            os.makedirs(self.transcription_output_directory)

        self.all_audio_files = [os.listdir(self.audio_input_directory)[0]]
        self.number_of_audio_files = len(self.all_audio_files)
        self.log.debug(
            f"Found audio files ({self.number_of_audio_files}): {self.all_audio_files}"
        )

    def transcribe_file(self, filename: str) -> None:
        """
        Transcribes an audio file to text.

        :param filename: The name of the audio file to transcribe.
        :return: None
        """
        input_file_path = os.path.join(self.audio_input_directory, filename)
        output_file_name = filename.replace(".mp3", ".txt")
        output_file_path = os.path.join(
            self.transcription_output_directory, output_file_name
        )

        model = whisper.load_model(self.transcriber_model_name)
        result = model.transcribe(input_file_path)
        with open(output_file_path, "w") as text_file:
            text_file.write(result["text"])
        self.log.info(f'Finished transcribing "{filename}"')

    def start(self) -> None:
        """
        Starts the transcription process of audio files using multiple threads.

        :return: None
        """
        self.log.info(
            "Starting to transcribe the audio files using multiple CPU cores, this may take a while..."
        )
        threads = []
        for index, filename in enumerate(self.all_audio_files, start=1):
            self.log.info(
                f"Transcribing {index} of {self.number_of_audio_files} - {filename}"
            )
            thread = threading.Thread(target=self.transcribe_file, args=[filename])
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()


transcriber = Transcriber()
transcriber.start()

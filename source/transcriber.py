import multiprocessing
import os
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

        self.all_audio_files = sorted(os.listdir(self.audio_input_directory))
        self.number_of_audio_files = len(self.all_audio_files)
        self.log.debug(
            f"Found audio files ({self.number_of_audio_files}): {self.all_audio_files}"
        )

    def transcribe_file(self, filename: str, overwrite: bool) -> None:
        """
        Transcribes an audio file and saves the transcription to a text file.

        :param filename: The name of the audio file to transcribe.
        :param overwrite: A boolean indicating whether to overwrite existing transcriptions.
        :return: None
        """
        self.log.info(f"Transcribing {filename}")

        input_file_path = os.path.join(self.audio_input_directory, filename)
        output_file_name = filename.replace(".mp3", ".txt")
        output_file_path = os.path.join(
            self.transcription_output_directory, output_file_name
        )

        if os.path.exists(output_file_path) and not overwrite:
            self.log.debug("Transcription already exists, skipping file...")

        model = whisper.load_model(self.transcriber_model_name)
        result = model.transcribe(input_file_path)
        with open(output_file_path, "w") as text_file:
            text_file.write(result["text"])
        self.log.info(f'Finished transcribing "{filename}"')

    def start(self, overwrite: bool = False) -> None:
        """
        Start the transcription process for all audio files using multiple CPU cores.

        :param overwrite: A boolean indicating whether to overwrite existing transcriptions.
        :return: None
        """
        self.log.info(
            f"Starting to transcribe the {self.number_of_audio_files} audio files using multiple CPU cores, this may take a while..."
        )

        # Use 3/4 of the cores
        num_cores = multiprocessing.cpu_count() * 3 // 4

        with multiprocessing.Pool(num_cores) as pool:
            iterable = [(audio_file, overwrite) for audio_file in self.all_audio_files]

            pool.starmap(self.transcribe_file, iterable)


transcriber = Transcriber()
transcriber.start()

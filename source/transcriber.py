import multiprocessing
import os
from concurrent.futures import ThreadPoolExecutor
from shutil import which

import whisper
from dotenv import load_dotenv

from source.git_root_finder import GitRootFinder
from source.logger import LoggerMixin


class Transcriber(LoggerMixin):
    """
    A class that handles the transcription of audio files using a specified transcriber model.

    :param transcriber_model_name: The model name to use for transcription (default is "base"). Choose from OpenAI's
    Whisper models.
    :param max_cores: The maximum number of CPU cores to use for the transcription process.
    :param overwrite: A flag indicating whether existing transcriptions should be overwritten.
    """

    def __init__(
        self,
        transcriber_model_name: str = "base",
        max_cores: int = None,
        overwrite: bool = False,
    ):
        super().__init__()

        load_dotenv()

        self.transcriber_model_name = transcriber_model_name
        self.log.debug(f'Using model "{self.transcriber_model_name}" for transcription')

        self._check_for_ffmpeg()
        self._find_audio_files()

        if max_cores is None:
            self.max_cores = multiprocessing.cpu_count() * 3 // 4
        else:
            self.max_cores = max_cores

        self.overwrite = overwrite

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

    def transcribe_file(self, filename: str) -> None:
        """
        Transcribes an audio file and saves the transcription to a text file.

        :param filename: The name of the audio file to transcribe.
        :return: None
        """
        input_file_path = os.path.join(self.audio_input_directory, filename)
        output_file_name = filename.replace(".mp3", ".txt")
        output_file_path = os.path.join(
            self.transcription_output_directory, output_file_name
        )
        if os.path.exists(output_file_path) and not self.overwrite:
            self.log.debug("Transcription already exists, skipping file...")
            return

        model = whisper.load_model(self.transcriber_model_name, device="cuda")

        self.log.info(f'Starting transcribing "{filename}"')
        transcription = model.transcribe(input_file_path)["text"]

        with open(output_file_path, "w", encoding="utf-8") as text_file:
            text_file.write(transcription)
        self.log.info(f'Finished transcribing "{filename}"')

    def start(self) -> None:
        """
        Starts the transcription process for audio files using multiple CPU cores. This may take a while.

        :return: None
        """
        self.log.info(
            f"Starting to transcribe the {self.number_of_audio_files} audio files using {self.max_cores} workers, this may take a while..."
        )

        with ThreadPoolExecutor(max_workers=self.max_cores) as executor:
            list(executor.map(self.transcribe_file, self.all_audio_files))


if __name__ == "__main__":
    transcriber = Transcriber(overwrite=True)
    transcriber.start()

import multiprocessing
import os
import tempfile
from itertools import repeat
from shutil import which

import whisper
from dotenv import load_dotenv
from pydub import AudioSegment

from source.git_root_finder import GitRootFinder
from source.logger import LoggerMixin


class Transcriber(LoggerMixin):
    """
    This class is responsible for transcribing audio files using multiple CPU cores.

    Inherits from LoggerMixin.

    :param max_cores: The maximum number of CPU cores to use for transcription. Defaults to 3/4 of the available CPU cores.
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

        self.temp_folder = tempfile.TemporaryDirectory()

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

    @staticmethod
    def _split_audio_into_segments(
        whole_audio: AudioSegment,
    ) -> list[tuple[int, int, int]]:
        """
        Splits the given audio into segments based on a specified segment duration.

        :param whole_audio: The full audio to be split into segments.
        :return: A list of tuples, where each tuple contains the start time, end time, and index of a segment.
        """
        segment_duration_ms = 30000
        audio_duration_ms = len(whole_audio)

        segments = []
        for index, start_time in enumerate(
            range(0, audio_duration_ms, segment_duration_ms)
        ):
            # Calculate end of segment (either duration of segment or end of audio file)
            end_time = min(start_time + segment_duration_ms, audio_duration_ms)

            segments.append((start_time, end_time, index))

        return segments

    def _transcribe_segment(
        self, args: tuple[int, int, int], whole_audio: AudioSegment
    ) -> tuple[int, str]:
        """
        This method transcribes a segment of an audio file using the Whisper transcription model.

        :param args: A tuple containing the start time, end time, and segment index of the audio segment.
        :param whole_audio: The whole audio file.

        :return: A tuple containing the segment index and the transcription of the audio segment.
        """
        start_time, end_time, segment_index = args

        segment = whole_audio[start_time:end_time]

        self.log.debug(f"Saving audio segment {segment_index} to file")
        segment_file_path = os.path.join(
            self.temp_folder.name, f"gpn_transcription_temp_segment_{segment_index}.wav"
        )
        segment.export(segment_file_path, format="wav")

        model = whisper.load_model(self.transcriber_model_name, device="cuda")

        self.log.debug(f"Transcribing audio segment {segment_index}")
        transcription = model.transcribe(segment_file_path)["text"]
        self.log.debug(f"Finished transcribing audio segment {segment_index}")

        os.remove(segment_file_path)

        return segment_index, transcription

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

        self.log.info(f"Loading audio file {filename}")
        whole_audio = AudioSegment.from_file(input_file_path, format="mp3")
        self.log.debug("Finished loading audio file")

        segments = self._split_audio_into_segments(whole_audio)
        amount_of_segments = len(segments)
        self.log.debug(f"Splitting audio file into {amount_of_segments} segments")

        finished_transcriptions = ["" for _ in range(amount_of_segments)]

        with multiprocessing.Pool(self.max_cores) as pool:
            for index, transcription in pool.starmap(
                self._transcribe_segment, zip(segments, repeat(whole_audio))
            ):
                finished_transcriptions[index] = transcription

        joined_transcription = " ".join(finished_transcriptions)

        with open(output_file_path, "w") as text_file:
            text_file.write(joined_transcription)
        self.log.info(f'Finished transcribing "{filename}"')

    def start(self) -> None:
        """
        Starts the transcription process for audio files using multiple CPU cores. This may take a while.

        :param overwrite: A boolean value indicating whether to overwrite existing transcription files. Defaults to False.
        :return: None
        """
        self.log.info(
            f"Starting to transcribe the {self.number_of_audio_files} audio files using, this may take a while..."
        )

        for audio_file in self.all_audio_files:
            self.transcribe_file(audio_file)

        self.temp_folder.cleanup()

import multiprocessing
import os
from shutil import which

import whisper
from dotenv import load_dotenv
from pydub import AudioSegment

from source.git_root_finder import GitRootFinder
from source.logger import LoggerMixin
from source.segment import Segment


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

    @staticmethod
    def _split_audio_into_segments(whole_audio: AudioSegment) -> list[Segment]:
        segments = []
        segment_duration_ms = 30000
        audio_duration_ms = len(whole_audio)
        # Schleife durch die Audiodauer in Schritten der Segmentdauer
        for index, start_time in enumerate(
                range(0, audio_duration_ms, segment_duration_ms)
        ):
            # Berechne das Ende des Segments (entweder die Segmentdauer oder das Ende der Audiodatei)
            end_time = min(start_time + segment_duration_ms, audio_duration_ms)

            segments.append(Segment(whole_audio, start_time, end_time, index))

        return segments

    def _transcribe_segment(self, segment: Segment) -> Segment:
        # Schneidet das Segment der Audio-Datei aus
        segment = segment.whole_audio[Segment.start_time:Segment.end_time]

        self.log.debug(f"Saving audio segment {Segment.index} to file")
        segment_file_path = f"/tmp/gpn_transcription_temp_segment_{Segment.index}.wav"
        segment.export(segment_file_path, format="wav")

        # Transkription mit Whisper durchführen
        model = whisper.load_model(self.transcriber_model_name, device="cuda")

        self.log.debug(f"Transcribing audio segment {Segment.index}")
        segment.transcription = model.transcribe(segment_file_path)["text"]
        self.log.debug(f"Finished transcribing audio segment {Segment.index}")

        os.remove(segment_file_path)

        return segment

    def transcribe_file(self, filename: str, overwrite: bool) -> None:
        """
        Transcribes an audio file and saves the transcription to a text file.

        :param filename: The name of the audio file to transcribe.
        :param overwrite: A boolean indicating whether to overwrite existing transcriptions.
        :return: None
        """
        input_file_path = os.path.join(self.audio_input_directory, filename)
        output_file_name = filename.replace(".mp3", ".txt")
        output_file_path = os.path.join(
            self.transcription_output_directory, output_file_name
        )
        if os.path.exists(output_file_path) and not overwrite:
            self.log.debug("Transcription already exists, skipping file...")
            return

        self.log.info(f"Loading audio file {filename}")
        whole_audio = AudioSegment.from_file(input_file_path, format="mp3")
        self.log.debug("Finished loading audio file")

        segments = self._split_audio_into_segments(whole_audio)
        amount_of_segments = len(segments)
        self.log.debug(f"Splitting audio file into {amount_of_segments} segments")

        # Use 3/4 of the cores
        num_cores = multiprocessing.cpu_count() * 3 // 4
        finished_transcriptions = ["" for _ in range(amount_of_segments)]
        # print(segments)

        with multiprocessing.Pool(num_cores) as pool:
            for segment in pool.starmap(
                self._transcribe_segment, segments
            ):
                finished_transcriptions[segment.index] = segment.transcription

        joined_transcription = " ".join(finished_transcriptions)

        with open(output_file_path, "w") as text_file:
            text_file.write(joined_transcription)
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

        for audio_file in self.all_audio_files:
            self.transcribe_file(audio_file, overwrite)
            break


transcriber = Transcriber()
transcriber.start(overwrite=True)

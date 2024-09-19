import multiprocessing
import os
from itertools import repeat

import whisper
from pydub import AudioSegment

from source.logger import LoggerMixin

class Transcriber(LoggerMixin):
    def _transcribe_segment(self, args, audio):
        audio_file_path, start_time, end_time, segment_index = args

        # Schneidet das Segment der Audio-Datei aus
        segment = audio[start_time:end_time]

        self.log.debug(f"Saving audio segment {segment_index} to file")
        segment_file_path = f"/tmp/gpn_transcription_temp_segment_{segment_index}.wav"
        segment.export(segment_file_path, format="wav")

        # Transkription mit Whisper durchführen
        model = whisper.load_model("tiny")

        self.log.info(f"Transcribing audio segment {segment_index}")
        transcription = model.transcribe(segment_file_path)
        self.log.debug(f"Finished transcribing audio segment {segment_index}")

        os.remove(segment_file_path)

        return segment_index, transcription["text"]


    def transcribe_audio(self, audio_file_path, segment_duration_ms=30000):
        self.log.info(f"Loading audio file {audio_file_path}")
        audio = AudioSegment.from_file(audio_file_path)
        self.log.debug(f"Finished loading audio file")

        audio_duration_ms = round(len(audio) / 2)

        # Liste der Segmente (Start- und Endzeiten)
        segments = [
            (audio_file_path, i, min(i + segment_duration_ms, audio_duration_ms), idx)
            for idx, i in enumerate(range(0, audio_duration_ms, segment_duration_ms))
        ]
        amount_of_segments = len(segments)

        self.log.debug(f"Splitting audio into {amount_of_segments} segments")

        # Transkriptionen parallelisieren
        num_cores = 10
        finished_transcriptions = ["" for _ in range(amount_of_segments)]
        with multiprocessing.Pool(num_cores) as pool:
            for segment_index, transcribed_segment in pool.starmap(
                self._transcribe_segment, zip(segments, repeat(audio))
            ):
                finished_transcriptions[segment_index] = transcribed_segment

        joined_transcription = " ".join(finished_transcriptions)

        return joined_transcription


# Beispiel: Audio-Datei transkribieren
# audio_file_path = "../data/audio/Aerodynamics 101.mp3"
transcriber = Transcriber()
# print(transcriber.transcribe_audio("../data/audio_example.mp3"))
print(transcriber.transcribe_audio("../data/audio/Aerodynamics 101.mp3"))

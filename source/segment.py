import dataclasses

from pydub import AudioSegment


@dataclasses.dataclass
class Segment:
    whole_audio: AudioSegment
    start_time: int
    end_time: int
    index: int
    transcription: str = ""

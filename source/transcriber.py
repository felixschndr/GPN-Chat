import glob
import os
import threading
from shutil import which

import whisper
from dotenv import load_dotenv


class Transcriber:
    def __init__(self):
        load_dotenv()

        if not which("ffmpeg"):
            raise SystemError("ffmpeg is not installed!")

        self.data_directory = os.getenv("DATA_DIRECTORY")
        self.transcriber_model_name = os.getenv("TRANSCRIBER_MODEL")

        data_input_directory = os.path.join(self.data_directory, "audio", "input")
        self.data_output_directory = os.path.join(
            self.data_directory, "audio", "output", self.transcriber_model_name
        )

        if not os.path.exists(self.data_output_directory):
            os.makedirs(self.data_output_directory)

        self.all_audio_files = glob.glob(f"{data_input_directory}/*.mp3")
        self.number_of_audio_files = len(self.all_audio_files)

    def transcribe_file(self, index: int, file: str) -> None:
        file_name = os.path.basename(file)
        output_file_name = file_name.replace(".mp3", ".txt")
        output_file_path = os.path.join(self.data_output_directory, output_file_name)

        print(f"{index} of {self.number_of_audio_files} - {file_name}", flush=True)

        model = whisper.load_model(self.transcriber_model_name)
        result = model.transcribe(file)
        with open(output_file_path, "w") as text_file:
            text_file.write(result["text"])
        print("\tFinished transcribing")

    def start(self) -> None:
        print("Transcribing audio files...")
        threads = []
        for index, file in enumerate(self.all_audio_files, start=1):
            thread = threading.Thread(target=self.transcribe_file, args=(index, file))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()


# transcriber = Transcriber()
# transcriber.start()

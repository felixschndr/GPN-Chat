import glob
import os
from shutil import which

import whisper
from dotenv import load_dotenv

load_dotenv()


if not which("ffmpeg"):
    raise SystemError("ffmpeg is not installed!")

DATA_DIRECTORY = os.getenv("DATA_DIRECTORY")
TRANSCRIBER_MODEL_NAME = os.getenv("TRANSCRIBER_MODEL")

data_input_directory = os.path.join(DATA_DIRECTORY, "audio", "input")
data_output_directory = os.path.join(
    DATA_DIRECTORY, "audio", "output", TRANSCRIBER_MODEL_NAME
)

if not os.path.exists(data_output_directory):
    os.makedirs(data_output_directory)

model = whisper.load_model(TRANSCRIBER_MODEL_NAME)


all_audio_files = glob.glob(f"{data_input_directory}/*.mp3")
number_of_audio_files = len(all_audio_files)

print("Transcribing audio files...")
for index, file in enumerate(all_audio_files, start=1):
    file_name = os.path.basename(file)
    output_file_name = file_name.replace(".mp3", ".txt")
    output_file_path = os.path.join(data_output_directory, output_file_name)

    print(f"{index} of {number_of_audio_files} - {file_name}")

    result = model.transcribe(file)
    with open(output_file_name, "w") as text_file:
        text_file.write(result["text"])
    print("\tFinished transcribing")

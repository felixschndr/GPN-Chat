import json
import os.path

from haystack import Document, component


@component
class TranscriptionAndMetadataToDocument:
    @component.output_types(documents=list[Document])
    def run(self, data_directory: str) -> dict[str, list[Document]]:
        documents = []

        transcriptions_directory = os.path.join(data_directory, "transcriptions")
        metadata_directory = os.path.join(data_directory, "metadata")

        all_metadata_files = sorted(os.listdir(metadata_directory))
        all_transcriptions_files = sorted(os.listdir(transcriptions_directory))
        metadata_transcription_pairs = list(
            zip(all_metadata_files, all_transcriptions_files)
        )

        for metadata_file_name, transcription_file_name in metadata_transcription_pairs:
            metadata_file = open(metadata_file_name, "r")
            transcription_file = open(transcription_file_name, "r")

            Document(
                content=transcription_file.read(), meta=json.loads(metadata_file.read())
            )

        return {"documents": documents}

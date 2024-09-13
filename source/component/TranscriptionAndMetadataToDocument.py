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

        metadata_transcription_pairs = list(
            zip(
                sorted(os.listdir(metadata_directory)),
                sorted(os.listdir(transcriptions_directory)),
            )
        )

        for metadata_file_name, transcription_file_name in metadata_transcription_pairs:
            with open(transcription_file_name, "r") as transcription_file, open(
                metadata_file_name, "r"
            ) as metadata_file:
                Document(
                    content=transcription_file.read(),
                    meta=json.loads(metadata_file.read()),
                )

        return {"documents": documents}

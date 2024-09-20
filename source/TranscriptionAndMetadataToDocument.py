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

        transcription_files = [
            os.path.join(transcriptions_directory, filename)
            for filename in os.listdir(transcriptions_directory)
        ]
        metadata_files = [
            os.path.join(metadata_directory, filename)
            for filename in os.listdir(metadata_directory)
        ]

        metadata_transcription_pairs = list(
            zip(
                sorted(transcription_files),
                sorted(metadata_files),
            )
        )

        for transcription_file_name, metadata_file_name in metadata_transcription_pairs:
            with open(transcription_file_name, "r", encoding="utf-8") as transcription_file, open(
                metadata_file_name, "r", encoding="utf-8"
            ) as metadata_file:
                documents.append(
                    Document(
                        content=transcription_file.read(),
                        meta=json.loads(metadata_file.read()),
                    )
                )

        return {"documents": documents}

import os

from haystack.components.embedders import SentenceTransformersDocumentEmbedder
from haystack.components.preprocessors import DocumentSplitter
from haystack.components.writers import DocumentWriter
from haystack.core.pipeline import Pipeline
from haystack_integrations.document_stores.qdrant import QdrantDocumentStore

from source.git_root_finder import GitRootFinder
from source.transcription_and_metadata_to_document import (
    TranscriptionAndMetadataToDocument,
)


class IndexingPipeline:
    """
    Initializes an indexing pipeline for processing and storing documents.
    It has to be run once when all data is available. Afterward only run the GPNChatPipeline

    This pipeline consists of the following components:

    - TranscriptionAndMetadataToDocument: Converts transcription and metadata to documents.
    - DocumentSplitter: Splits documents into smaller segments.
    - SentenceTransformersDocumentEmbedder: Embeds the document segments using a pre-trained sentence transformer model.
    - DocumentWriter: Writes the embedded documents to a Qdrant document store.

    The components are connected in a sequence where the output of one is passed as input to the next.

    The pipeline is visualized and saved as an image file "indexing_pipeline.png".
    """

    def __init__(self):
        qdrant_document_store = QdrantDocumentStore(
            location="http://localhost:6333",
            recreate_index=True,
            return_embedding=True,
            wait_result_from_api=True,
            embedding_dim=384,
            index="gpn-chat",
            use_sparse_embeddings=False,
            sparse_idf=True,
        )

        self.pipeline = Pipeline()

        self.pipeline.add_component(
            instance=TranscriptionAndMetadataToDocument(), name="textfile_loader"
        )
        self.pipeline.add_component(
            instance=DocumentSplitter(
                split_by="sentence", split_length=5, split_overlap=2
            ),
            name="splitter",
        )
        self.pipeline.add_component(
            instance=SentenceTransformersDocumentEmbedder(
                model="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
            ),
            name="embedder",
        )
        self.pipeline.add_component(
            name="writer", instance=DocumentWriter(qdrant_document_store)
        )

        self.pipeline.connect(sender="textfile_loader", receiver="splitter")
        self.pipeline.connect(sender="splitter", receiver="embedder")
        self.pipeline.connect(sender="embedder.documents", receiver="writer")

        self.pipeline.draw("indexing_pipeline.png")

    def run(self) -> None:
        """
        Runs the data processing pipeline.

        :return: None
        """
        data_directory = os.path.join(GitRootFinder.get(), "data")
        self.pipeline.run({"textfile_loader": {"data_directory": data_directory}})


if __name__ == "__main__":
    indexing_pipeline = IndexingPipeline()
    indexing_pipeline.run()

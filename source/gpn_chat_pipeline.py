import os

from dotenv import load_dotenv
from haystack.components.embedders import SentenceTransformersDocumentEmbedder
from haystack.components.preprocessors import DocumentSplitter
from haystack.components.writers import DocumentWriter
from haystack.core.pipeline import Pipeline
from haystack_integrations.document_stores.qdrant import QdrantDocumentStore

from source.component.TranscriptionAndMetadataToDocument import (
    TranscriptionAndMetadataToDocument,
)
from source.git_root_finder import GitRootFinder


class GPNChatPipeline:
    def __init__(self):
        qdrant_document_store = QdrantDocumentStore(
            location="http://localhost:6333",
            recreate_index=True,
            return_embedding=True,
            wait_result_from_api=True,
            embedding_dim=384,
            index="gpn-chat",
            use_sparse_embeddings=True,
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
            instance=SentenceTransformersDocumentEmbedder(model="all-MiniLM-L6-v2"),
            name="embedder",
        )
        self.pipeline.add_component(
            name="writer", instance=DocumentWriter(qdrant_document_store)
        )

        self.pipeline.connect("textfile_loader", "splitter")
        self.pipeline.connect(sender="splitter", receiver="embedder")
        self.pipeline.connect(sender="embedder.documents", receiver="writer")
        # self.pipeline.draw(path="gpn_chat_pipeline.png")

    def run(self, data_directory: str) -> None:
        self.pipeline.run({"textfile_loader": {"data_directory": data_directory}})


load_dotenv()
repository_root = GitRootFinder.get()
data_directory = os.path.join(repository_root, os.environ["DATA_DIRECTORY"])

gpn_chat_pipeline = GPNChatPipeline()
gpn_chat_pipeline.run(data_directory)

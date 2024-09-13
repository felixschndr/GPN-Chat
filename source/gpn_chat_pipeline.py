import os

from dotenv import load_dotenv
from haystack.components.converters import TextFileToDocument
from haystack.components.embedders import SentenceTransformersDocumentEmbedder
from haystack.components.preprocessors import DocumentSplitter
from haystack.components.writers import DocumentWriter
from haystack.core.pipeline import Pipeline
from haystack_integrations.document_stores.qdrant import QdrantDocumentStore


class GPNChatPipeline:
    def __init__(self):
        qdrant_document_store = QdrantDocumentStore(
            location="http://localhost:6333",
            recreate_index=True,
            return_embedding=True,
            wait_result_from_api=True,
            embedding_dim=1024,
            index="bge-large-en-v1.5",
            use_sparse_embeddings=True,
            sparse_idf=True,
        )

        self.pipeline = Pipeline()

        self.pipeline.add_component(
            instance=TextFileToDocument(), name="textfile_loader"
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
        self.pipeline.draw(path="gpn_chat_pipeline.png")

    def run(self, sources: list[str]) -> None:
        self.pipeline.run({"textfile_loader": sources})


load_dotenv()
data_directory = os.environ["DATA_DIRECTORY"]
transcriber_model_name = os.getenv("TRANSCRIBER_MODEL")

text_file_directory = os.path.join(
    data_directory, "audio", "output", transcriber_model_name
)
sources = os.listdir()
GPNChatPipeline()

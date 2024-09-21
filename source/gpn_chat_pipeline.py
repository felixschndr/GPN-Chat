import os
import time

from haystack_integrations.components.connectors.langfuse import LangfuseConnector
import docker
from haystack.components.builders import ChatPromptBuilder
from haystack.components.embedders import SentenceTransformersDocumentEmbedder, SentenceTransformersTextEmbedder
from haystack.components.preprocessors import DocumentSplitter
from haystack.components.writers import DocumentWriter
from haystack.core.pipeline import Pipeline
from haystack.dataclasses import ChatMessage
from haystack_integrations.components.generators.ollama import OllamaChatGenerator
from haystack_integrations.components.retrievers.qdrant import QdrantEmbeddingRetriever
from haystack_integrations.document_stores.qdrant import QdrantDocumentStore

from source.git_root_finder import GitRootFinder
from source.TranscriptionAndMetadataToDocument import TranscriptionAndMetadataToDocument

DOCUMENT_PROMPT_TEMPLATE = """
    Beantworte anhand der folgenden Dokumente die Frage. \nDokumente:
    {% for doc in documents %}
        {{ doc.content }}
    {% endfor %}

    \nFrage: {{query}}
    \nAntwort:
    """

class IndexingPipeline:
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
            instance=TranscriptionAndMetadataToDocument(), name="textfile_loader" #TextFileToDocument()
        )
        self.pipeline.add_component(
            instance=DocumentSplitter(
                split_by="sentence", split_length=5, split_overlap=2
            ),
            name="splitter",
        )
        self.pipeline.add_component(
            instance=SentenceTransformersDocumentEmbedder(model="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"), # jinaai/jina-embeddings-v3
            name="embedder",
        )
        self.pipeline.add_component(
            name="writer", instance=DocumentWriter(qdrant_document_store)
        )

        self.pipeline.connect(sender="textfile_loader", receiver="splitter")
        self.pipeline.connect(sender="splitter", receiver="embedder")
        self.pipeline.connect(sender="embedder.documents", receiver="writer")

    def run(self):
        data_directory = os.path.join(GitRootFinder.get(), "data")
        self.pipeline.run({
            "textfile_loader": {"data_directory": data_directory}
        })


class GPNChatPipeline:
    def __init__(self):
        # self._start_qdrant_container()

        ollama_chat_generator = OllamaChatGenerator(
            model="llama3.1:8b",  # "llama3.1",
            url="http://localhost:11434/api/chat",
            generation_kwargs={
                "num_predict": 512,
                "temperature": 0.95,
            },
        )

        qdrant_document_store = QdrantDocumentStore(
            location="http://localhost:6333",
            embedding_dim=384,
            index="gpn-chat",
            use_sparse_embeddings=False,
            sparse_idf=True,
        )

        embedder = SentenceTransformersTextEmbedder(model="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
        self.pipeline = Pipeline()
        self.pipeline.add_component(
            "tracer", LangfuseConnector("Basic RAG Pipeline")
        )
        self.pipeline.add_component(
            name="dense_text_embedder",
            instance=embedder,  # OllamaTextEmbedder(model="mxbai-embed-large")
        )
        self.pipeline.add_component("retriever", QdrantEmbeddingRetriever(document_store=qdrant_document_store, top_k=10))
        self.pipeline.add_component(
            "prompt_builder", ChatPromptBuilder(template=[ChatMessage.from_user(DOCUMENT_PROMPT_TEMPLATE)])
        )
        self.pipeline.add_component("llm", ollama_chat_generator)

        self.pipeline.connect(
            sender="dense_text_embedder.embedding", receiver="retriever.query_embedding"
        )
        self.pipeline.connect(sender="retriever", receiver="prompt_builder.documents")
        self.pipeline.connect(sender="retriever.documents", receiver="prompt_builder.documents")
        self.pipeline.connect(sender="prompt_builder", receiver="llm")

    def _start_qdrant_container(self) -> None:
        """
        Starts a Qdrant container for data storage and indexing.

        :return: None.
        """
        qdrant_data_directory = os.path.join(GitRootFinder.get(), "data", "qdrant")
        docker_client = docker.from_env()
        self.qdrant_container = docker_client.containers.run(
            "qdrant/qdrant",
            detach=True,
            volumes=[f"{qdrant_data_directory}:/qdrant/storage"],
            ports={"6333": "6333", "6334": "6334"},
        )
        while "listening on" not in str(self.qdrant_container.logs()).lower():
            print("waiting")
            time.sleep(1)

    def run(self, query: str) -> str:
        response = self.pipeline.run({
            "dense_text_embedder": {"text": query},
            "prompt_builder": {"query": query}
        })

        # self.qdrant_container.stop()
        return response["llm"]["replies"][0].content

if __name__ == "__main__":
    indexing_pipeline = IndexingPipeline()
    indexing_pipeline.run()

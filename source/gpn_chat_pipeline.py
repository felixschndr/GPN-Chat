import os
import time

import docker
from haystack.components.builders import ChatPromptBuilder
from haystack.components.embedders import SentenceTransformersDocumentEmbedder
from haystack.components.preprocessors import DocumentSplitter
from haystack.components.writers import DocumentWriter
from haystack.core.pipeline import Pipeline
from haystack.dataclasses import ChatMessage
from haystack_integrations.components.generators.ollama import OllamaChatGenerator
from haystack_integrations.document_stores.qdrant import QdrantDocumentStore

from source.git_root_finder import GitRootFinder
from source.TranscriptionAndMetadataToDocument import TranscriptionAndMetadataToDocument

DOCUMENT_PROMPT_TEMPLATE = """
    Beantworte anhand der folgenden Dokumente die Frage.
    Dokumente:
    {% for doc in documents %}
        {{ doc.content }}
    {% endfor %}

    Frage: {{query}}
    Antwort:
    """
PROMPT_TEMPLATE = """
    Beantworte jede Frage als wärst du Mario aus den Super Mario Spielen. Frage: {{query}} Antwort:
    """


class GPNChatPipeline:
    def __init__(self):
        self._start_qdrant_container()

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
        self.pipeline.add_component(
            "prompt_builder",
            ChatPromptBuilder(template=[ChatMessage.from_user(PROMPT_TEMPLATE)]),
        )
        self.pipeline.add_component("llm", ollama_chat_generator)

        self.pipeline.connect("prompt_builder.prompt", receiver="llm.messages")

        self.pipeline.connect("textfile_loader", "splitter")
        self.pipeline.connect(sender="splitter", receiver="embedder")
        self.pipeline.connect(sender="embedder.documents", receiver="writer")
        # self.pipeline.draw(path="gpn_chat_pipeline.png")

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
        # data_directory = os.path.join(GitRootFinder.get(), "data")
        # response = self.pipeline.run({"textfile_loader": {"data_directory": data_directory}, "prompt_builder": {"query": ChatMessage.from_user(query)}})
        response = self.pipeline.run(
            {"prompt_builder": {"query": ChatMessage.from_user(query)}}
        )

        self.qdrant_container.stop()
        return response["llm"]["replies"][0].content

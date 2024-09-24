import os
from pathlib import Path
from typing import Callable

from haystack.components.builders import ChatPromptBuilder
from haystack.components.embedders import SentenceTransformersTextEmbedder
from haystack.core.pipeline import Pipeline
from haystack.dataclasses import ChatMessage
from haystack_integrations.components.generators.ollama import OllamaChatGenerator
from haystack_integrations.components.retrievers.qdrant import QdrantEmbeddingRetriever
from haystack_integrations.document_stores.qdrant import QdrantDocumentStore

from source.git_root_finder import GitRootFinder
from source.logger import LoggerMixin

DOCUMENT_PROMPT_TEMPLATE = """
    Beantworte anhand der folgenden Dokumente die Frage. \nDokumente:
    {% for doc in documents %}
        {{ doc.content }}
    {% endfor %}

    \nFrage: {{query}}
    \nAntwort:
    """


class GPNChatPipeline(LoggerMixin):
    """
    GPNChatPipeline is a class that defines a chat pipeline leveraging various components
    like a dense text embedder, a retriever, a prompt builder, and a language model.
    It interacts with a Qdrant document store for data storage and indexing.
    """

    def __init__(self, streaming_callback: Callable):
        super().__init__()

        ollama_chat_generator = OllamaChatGenerator(
            model="llama3.1:8b",
            url="http://localhost:11434/api/chat",
            generation_kwargs={
                "num_predict": 512,
                "temperature": 0.95,
            },
            streaming_callback=streaming_callback,
        )

        qdrant_document_store = QdrantDocumentStore(
            location="http://localhost:6333",
            embedding_dim=384,
            index="gpn-chat",
            use_sparse_embeddings=False,
            sparse_idf=True,
        )

        self.pipeline = Pipeline()

        self.pipeline.add_component(
            name="dense_text_embedder",
            instance=SentenceTransformersTextEmbedder(
                model="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
            ),
        )
        self.pipeline.add_component(
            "retriever",
            QdrantEmbeddingRetriever(document_store=qdrant_document_store, top_k=10),
        )
        self.pipeline.add_component(
            "prompt_builder",
            ChatPromptBuilder(
                template=[ChatMessage.from_user(DOCUMENT_PROMPT_TEMPLATE)]
            ),
        )
        self.pipeline.add_component("llm", ollama_chat_generator)

        self.pipeline.connect(
            sender="dense_text_embedder.embedding", receiver="retriever.query_embedding"
        )
        self.pipeline.connect(sender="retriever", receiver="prompt_builder.documents")
        self.pipeline.connect(
            sender="retriever.documents", receiver="prompt_builder.documents"
        )
        self.pipeline.connect(sender="prompt_builder", receiver="llm")

        self.pipeline.draw(
            Path(os.path.join(GitRootFinder.get(), "gpn_chat_pipeline.png"))
        )

    def run(self, query: str) -> str:
        """
        Sends the query input from the user to the pipeline

        :param query: A string representing the input query for which a response is to be generated.
        :return: The content of the reply generated by the language model based on the provided query.
        """
        response = self.pipeline.run(
            {"dense_text_embedder": {"text": query}, "prompt_builder": {"query": query}}
        )

        return response["llm"]["replies"][0].content

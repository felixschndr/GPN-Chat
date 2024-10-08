import streamlit as st
from haystack.dataclasses import StreamingChunk

from source.gpn_chat_pipeline import GPNChatPipeline


class Chatbot:
    """
    Class that represents a Chatbot capable of processing prompts by sending them to the pipeline and generating responses.
    """

    def __init__(self):
        self.container = None
        self.response_tokens = None

        self.pipeline = GPNChatPipeline(self.write_streaming_chunk)

    def run(self, prompt: str) -> str:
        """
        Send the prompt from the user to the pipeline and returns the response.

        :param prompt: The input string for which the model will generate a response.
        :return: The response generated by the model pipeline.
        """
        self.container = st.empty()
        self.response_tokens = []

        return self.pipeline.run(prompt)

    def write_streaming_chunk(self, chunk: StreamingChunk) -> None:
        """
        :param chunk: A chunk of data to be written to the streaming response. The chunk is an instance of StreamingChunk and contains the content to be appended and written.
        :return: None
        """
        self.response_tokens.append(chunk.content)
        self.container.write("".join(self.response_tokens))

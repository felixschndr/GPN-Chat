import streamlit as st
from haystack.dataclasses import StreamingChunk, ChatMessage

from source.gpn_chat_pipeline import GPNChatPipeline


class Chatbot:

    def __init__(self):
        self.pipeline = GPNChatPipeline(self.write_streaming_chunk)


    def run(self, prompt: str) -> str:
        self.container = st.empty()
        self.response_tokens = []

        response = self.pipeline.run(prompt)

        return response


    def write_streaming_chunk(self, chunk: StreamingChunk):
        self.response_tokens.append(chunk.content)
        self.container.write("".join(self.response_tokens))

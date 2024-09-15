import streamlit as st

HOST = "http://localhost:11434"


class ChatUI:
    def __init__(self):
        self.client = self.build_connection_to_model()

    # def build_connection_to_model(self) -> Client:
    #     return Client(host=HOST)
    #
    # def get_response(self, prompt: str):
    #     return client.chat(
    #         model="llama3.1",
    #         messages=[
    #             {
    #                 "role": "user",
    #                 "content": prompt,
    #             },
    #         ],
    #     )

    def run(self) -> None:
        st.title("GPN Chat")

        # Initialize chat history
        if "messages" not in st.session_state:
            st.session_state.messages = []

        # Display chat messages from history on app rerun
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Accept user input
        if prompt := st.chat_input("What is up?"):
            # Display user message in chat message container
            with st.chat_message("user"):
                st.markdown(prompt)
            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": prompt})

        # Display assistant response in chat message container
        with st.chat_message("assistant"):
            response = st.write_stream(self.get_response(prompt))
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})

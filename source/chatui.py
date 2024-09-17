import streamlit as st

from gpn_chat_pipeline import GPNChatPipeline


class ChatUI:
    def __init__(self):
        self.pipeline = GPNChatPipeline()

    def get_response(self, prompt: str) -> str:
        response = self.pipeline.run(prompt)
        return response

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
            response = self.pipeline.run(prompt)
            st.write(response)
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})

        pass


def main():
    chat = ChatUI()
    chat.run()


if __name__ == "__main__":
    main()

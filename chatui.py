import streamlit as st

from source.chatbot import Chatbot
from source.gpn_chat_pipeline import GPNChatPipeline

RENDERED_MESSAGES = "rendered_messages"
CHAT_HISTORY = "chat_history"
GPN_CHAT_PIPELINE = "gpn_chat_pipeline"

def main():
    title = "GPN Chat"
    st.set_page_config(page_title=title)
    st.title(title)
    configuration = configure_state()
    initialize_session_state(configuration)
    render_history()
    run_ui()

def configure_state() -> dict:
    return {
        RENDERED_MESSAGES: [],
        CHAT_HISTORY: [],
        GPN_CHAT_PIPELINE: Chatbot(),
    }

def initialize_session_state(config):
    """
        Initialize Streamlit session state variables using the provided configuration.

    Args:
        config (dict): Configuration dictionary.
    """
    for key, value in config.items():
        if key not in st.session_state:
            st.session_state[key] = value

def render_history():
    for message in st.session_state[RENDERED_MESSAGES]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

def run_ui():
    # Accept user input
    if prompt := st.chat_input("Womit kann ich helfen?"):
        # Display user message in chat message container
        with st.chat_message("user"):
            st.markdown(prompt)
        # Add user message to chat history
        st.session_state[RENDERED_MESSAGES].append({"role": "user", "content": prompt})

        # Display assistant response in chat message container
        with st.chat_message("assistant"):
            with st.spinner("Generiere Antwort ..."):
                response = st.session_state[GPN_CHAT_PIPELINE].run(prompt)
        # Add assistant response to chat history
        st.session_state[RENDERED_MESSAGES].append(
            {"role": "assistant", "content": response}
        )


if __name__ == "__main__":
    main()

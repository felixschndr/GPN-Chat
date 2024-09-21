import streamlit as st

from source.gpn_chat_pipeline import GPNChatPipeline

UI_RENDERED_MESSAGES = "ui_rendered_messages"
CHAT_HISTORY = "chat_history"
CONVERSATIONAL_PIPELINE = "conversational_pipeline"

def main():
    configuration = configure_state()
    initialize_session_state(configuration)
    title = "GPN Chat"
    st.set_page_config(page_title=title)
    st.title(title)
    render_history()
    run_ui()

def configure_state() -> dict:
    return {
        UI_RENDERED_MESSAGES: [],
        CHAT_HISTORY: [],
        CONVERSATIONAL_PIPELINE: GPNChatPipeline(),
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
    for message in st.session_state[UI_RENDERED_MESSAGES]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

def run_ui():
    # Accept user input
    if prompt := st.chat_input("What is up?"):
        # Display user message in chat message container
        with st.chat_message("user"):
            st.markdown(prompt)
        # Add user message to chat history
        st.session_state[UI_RENDERED_MESSAGES].append({"role": "user", "content": prompt})

        # Display assistant response in chat message container
        with st.chat_message("assistant"):
            response = st.session_state[CONVERSATIONAL_PIPELINE].run(prompt)
            st.write(response)
        # Add assistant response to chat history
        st.session_state[UI_RENDERED_MESSAGES].append(
            {"role": "assistant", "content": response}
        )


if __name__ == "__main__":
    main()

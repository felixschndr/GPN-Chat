import streamlit as st

from source.chatbot import Chatbot

TITLE = "GPN-Chat"

RENDERED_MESSAGES = "rendered_messages"
CHAT_HISTORY = "chat_history"
GPN_CHAT_PIPELINE = "gpn_chat_pipeline"


def main() -> None:
    st.set_page_config(page_title=TITLE)
    st.title(TITLE)

    st.session_state[RENDERED_MESSAGES] = []
    st.session_state[CHAT_HISTORY] = []
    st.session_state[GPN_CHAT_PIPELINE] = Chatbot()

    render_history()
    run_ui()


def render_history() -> None:
    """
    Render the chat history stored in the session state. Each message is displayed based on its role and content.

    :return: None
    """
    for message in st.session_state[RENDERED_MESSAGES]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])


def run_ui() -> None:
    """
    Accepts user input, processes it, and updates the chat message containers with the user's message and the assistant's response. The function maintains chat history in the session state.

    :return: None
    """
    if prompt := st.chat_input("Womit kann ich helfen?"):
        with st.chat_message("user"):
            st.markdown(prompt)

        st.session_state[RENDERED_MESSAGES].append({"role": "user", "content": prompt})

        with st.chat_message("assistant"):
            with st.spinner("Generiere Antwort ..."):
                response = st.session_state[GPN_CHAT_PIPELINE].run(prompt)

        st.session_state[RENDERED_MESSAGES].append(
            {"role": "assistant", "content": response}
        )


if __name__ == "__main__":
    main()

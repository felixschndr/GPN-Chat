import os

from dotenv import load_dotenv

load_dotenv()


def load_text_files() -> list[str]:
    """
    Loads text files from the specified directory.

    :return: A list of strings containing the contents of the text files.
    """
    data_directory = os.environ["DATA_DIRECTORY"]
    transcriber_model_name = os.getenv("TRANSCRIBER_MODEL")

    text_file_directory = os.path.join(
        data_directory, "audio", "output", transcriber_model_name
    )

    texts = []
    for filename in os.listdir(text_file_directory):
        with open(
            os.path.join(text_file_directory, filename), "r", encoding="utf-8"
        ) as f:
            texts.append(f.read())
    return texts


def split_text_into_chunks(texts: list[str]) -> list[list[str]]:
    """
    Split Text into Chunks

    Split a list of texts into chunks by splitting the text at each occurrence of a period (".") character. The resulting chunks will be in lowercase.

    :param texts: A list of strings representing the texts to be split.
    :return: A list of lists, where each inner list represents a chunk containing lowercase text.

    Example:

    ```python
    texts = ["Hello. How are you?", "I am fine. Thanks.", "Goodbye."]
    chunks = split_text_into_chunks(texts)
    print(chunks)
    ```

    Output:
    ```
    [['hello', ' how are you?'], ['i am fine', ' thanks'], ['goodbye']]
    ```
    """
    chunks = []
    for text in texts:
        chunks += [text.lower().split(".")]

    return chunks


training_texts = load_text_files()
training_texts_processed = split_text_into_chunks(training_texts)
print(training_texts_processed)

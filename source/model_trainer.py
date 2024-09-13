import os

from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from torch import Tensor

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


def split_text_into_chunks(texts: list[str]) -> list[str]:
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
        chunks += text.lower().split(".")

    return chunks


def create_embeddings(training_texts: list[str]) -> Tensor:
    """
    A function to create embeddings for a given list of training texts using the BERT model.

    :param training_texts: A list of strings containing the training texts.
    :return: A Tensor containing the embeddings of the training texts.

    Example:
    ```python
    training_texts = ["This is the first sentence.", "This is the second sentence."]
    embeddings = create_embeddings(training_texts)
    print(embeddings)
    ```

    Output:
    ```
    tensor([[...], [...]], dtype=float32)
    ```
    """
    # We use the BERT model since it is made for context capturing and creating sentences
    transformer_model = SentenceTransformer("all-MiniLM-L6-v2")
    return transformer_model.encode(training_texts, convert_to_tensor=True)


training_texts_raw = load_text_files()
training_texts_chunked = split_text_into_chunks(training_texts_raw)
embeddings = create_embeddings(training_texts_chunked)
print(embeddings.shape)

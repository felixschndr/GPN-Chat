# GPN-Chat

This repository aims to create a LLM with the help of RAG (Retrieval Augmented Generation) to be able to answer questions based on the public talks of the
[Gulaschprogrammiernacht (GPN)](https://entropia.de/GPN22/en).

The Gulaschprogrammiernacht is an annual four-day event organized by Entropia e.V., part of the Chaos Computer
Club (CCC) in Karlsruhe, Germany. Originally conceived by computer science students in Karlsruhe in 2002, it has grown
into one of Europe's major gatherings for the hacker community. The event, which is held at the ZKM | Center for Art and
Media as well as the State Academy of Design Karlsruhe, includes hacking, programming, **lectures**, workshops, and as the
name suggests, a significant amount of goulash cooking to feed participants. 

There are many interesting **lectures**, however they are all quite long (about an hour each) and I currently don't have the time to listen to them. Thus, my idea was to create a LLM which I could ask questions about all the talks.

## Inner workings

There are five stages to achieve this:

1. **Crawling** all the data from the [GPN archive](https://media.ccc.de/b/conferences/gpn)
   - This is done in the [crawler](source/crawler.py).
   - It gets all the metadata such as speaker, date, length of the talk and writes it do `data/metadata/name_of_the_talk.json`.
   - It downloads the corresponding audio file and saves is to `data/audio/name_of_the_talk.mp3`.
2. **Transcribing** the audio files
   - This is done in the [transcriber](source/transcriber.py).
   - The `Transcriber` uses a speech to text model from [OpenAI's whisper](https://github.com/openai/whisper).
     - It iterates over all audio files in `data/audio/` and loads them.
     - It splits them up into smaller chunks and then uses multithreading to transcribe them.
     - Afterward it combines all the parts of the transcriptions into one large file and writes it to `data/transcriptions/name_of_the_talk.txt`
3. **Translating** the transcriptions
   - This is done in the [translator](source/translator.py).
   - It iterates over all metadata files and checks whether its corresponding transcription is not in the target language.
   - The target language can be specified by using `--translation-target-language` in `main.py`.
   - When a transcription is not in the target language it is translated and written back to the original file.
4. Creating the **Pipeline**
   - This is done in the [GPNChatPipeline](source/gpn_chat_pipeline.py).
   - This project uses [RAG](https://de.wikipedia.org/wiki/Retrieval_Augmented_Generation) in order to determine which next word is most likely depending on the current context (the same technology ChatGPT uses).
   - The pipeline has multiple steps
     1. Loading in the data (audio file and metadata): With the help of a [custom component](source/TranscriptionAndMetadataToDocument.py) to match the corresponding files the data is loaded.
     2. Splitting the data: The transcriptions are split on a sentence level to help the RAG understand the data.
     3. Embedding the data: This converts the text into high-dimensional vectors that capture semantic meaning, enabling efficient comparison.
     4. Writing the data into a `QdrantDocumentStore`: The processed data is stored such that a vector map can be created. This map is used to determine the next word based on the current context.
5. **Interacting** with the Pipeline
   - This is done in the [ChatUI](source/chatui.py).
   - The `ChatUI` creates a browser application with the help of [streamlit](https://streamlit.io/) in which the user can interact (--> ask questions) with the Pipeline.

## Development

1. Create a virtual environment
   ```bash
   python -m venv .venv
   ```
2. Activate the virtual environment
   ```bash
   source .venv/bin/activate
   ```
3. Install the requirements
   ```bash
   poetry install
   ```
4. Run
   ```text
   $ python main.py --help

   usage: Gulaschprogrammiernacht Chat
   [-h] [--crawl] [--transcribe] [--transcription-model {tiny,base,small,medium,large}] [--transcription-cpu-count TRANSCRIPTION_CPU_COUNT] [--overwrite-existing-transcriptions] [--translation-target-language TRANSLATION_TARGET_LANGUAGE] [--loglevel {debug,info,warning,error,critical}]
   
   A GPT that is trained on the Gulaschprogrammiernacht Talks
   
   options:
   -h, --help
      show this help message and exit
   --crawl
      Crawl the audio files and metadata from the GPN archive. This is slow and only has to be done once, the data is written to disk - Default: False
   --transcribe
      Transcribe the audio files. This is slow and only has to be done once, the data is written to disk - Default: False
   --transcription-model {tiny,base,small,medium,large}
      The Whisper model to be used to transcribe the audio files. The larger the model the more accurate the transcriptions become but the slower it gets. See https://github.com/openai/whisper?tab=readme-ov-file#available-models-and-languages for more information - Default: base
   --transcription-cpu-count TRANSCRIPTION_CPU_COUNT
      The amount of CPU cores to use for transcribing - Default: 3/4 of the available CPU cores (15)
   --overwrite-existing-transcriptions
      Overwrite existing transcriptions - Default: False
   --translation-target-language TRANSLATION_TARGET_LANGUAGE
      Language to translate the transcriptions to. Specify a ISO 639 language code - Default: de
   --loglevel {debug,info,warning,error,critical}
      Set the logging level - Default: info
   ```

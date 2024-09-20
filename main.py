import argparse
import multiprocessing
import os

from iso639 import Lang
from iso639.exceptions import InvalidLanguageValue

from source.crawler import Crawler
from source.transcriber import Transcriber
from source.translator import Translator


class IllegalArgumentError(ValueError):
    pass


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="Gulaschprogrammiernacht Chat",
        description="A GPT that is trained on the Gulaschprogrammiernacht Talks",
    )

    crawl_argument_name = "--crawl"
    parser.add_argument(
        crawl_argument_name,
        action="store_true",
        default=False,
        help="Crawl the audio files and metadata from the GPN archive. This is slow and only has to be done once, the data is written to disk - Default: %(default)s",
    )
    transcribe_argument_name = "--transcribe"
    parser.add_argument(
        transcribe_argument_name,
        action="store_true",
        default=False,
        help="Transcribe the audio files. This is slow and only has to be done once, the data is written to disk - Default: %(default)s",
    )
    transcribe_model_argument_name = "--transcription-model"
    parser.add_argument(
        transcribe_model_argument_name,
        choices=["tiny", "base", "small", "medium", "large"],
        help="The Whisper model to be used to transcribe the audio files. The larger the model the more accurate the transcriptions become but the slower it gets. See https://github.com/openai/whisper?tab=readme-ov-file#available-models-and-languages for more information - Default: base",
    )
    transcribe_cpu_count_argument_name = "--transcription-cpu-count"
    parser.add_argument(
        transcribe_cpu_count_argument_name,
        type=int,
        default=None,
        help=f"The amount of CPU cores to use for transcribing - Default: 3/4 of the available CPU cores ({multiprocessing.cpu_count() * 3 // 4})",
    )
    overwrite_existing_transcriptions_argument_name = (
        "--overwrite-existing-transcriptions"
    )
    parser.add_argument(
        overwrite_existing_transcriptions_argument_name,
        action="store_true",
        default=False,
        help="Overwrite existing transcriptions - Default: %(default)s",
    )
    translation_target_language_argument_name = "--translation-target-language"
    parser.add_argument(
        translation_target_language_argument_name,
        help="Language to translate the transcriptions to. Specify a ISO 639 language code - Default: de",
    )
    parser.add_argument(
        "--loglevel",
        choices=["debug", "info", "warning", "error", "critical"],
        default="info",
        help="Set the logging level - Default: %(default)s",
    )

    if not args.crawl and not args.transcribe:
        raise IllegalArgumentError(
            f"Error: You must at least specify {crawl_argument_name} or {transcribe_argument_name}! To run the UI run python chatui.py."
        )

    if not args.transcribe:
        if args.transcription_model:
            raise IllegalArgumentError(
                f"Error: {transcribe_model_argument_name} can only be used if {transcribe_argument_name} is provided!"
            )
        if args.transcription_cpu_count:
            raise IllegalArgumentError(
                f"Error: {transcribe_cpu_count_argument_name} can only be used if {transcribe_argument_name} is provided!"
            )
        if args.overwrite_existing_transcriptions:
            raise IllegalArgumentError(
                f"Error: {transcribe_cpu_count_argument_name} can only be used if {transcribe_argument_name} is provided!"
            )
    if (
        args.transcription_cpu_count
        and args.transcription_cpu_count > multiprocessing.cpu_count()
    ):
        raise IllegalArgumentError(
            f"Error: {transcribe_cpu_count_argument_name} has to be lower than the number of available CPU cores ({multiprocessing.cpu_count()})"
        )

    if args.translation_target_language:
        try:
            Lang(args.translation_target_language)
        except InvalidLanguageValue:
            raise IllegalArgumentError(
                f"Error: {args.translation_target_language} is not a valid ISO 639 language code!"
            )

    # FIXME: Does not work yet
    os.environ["LOGLEVEL"] = args.loglevel.upper()

    return args


args = parse_arguments()

if args.crawl:
    crawler = Crawler()
    crawler.run()

if args.transcribe:
    transcriber = Transcriber(
        transcriber_model_name=args.transcription_model,
        max_cores=args.transcription_cpu_count,
        overwrite=args.overwrite_existing_transcriptions,
    )
    transcriber.start()

translator = Translator(target_language=args.translation_target_language)
translator.start()

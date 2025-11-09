#!/usr/bin/env python
# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Export Marugoto lessons as Disce deck."""

import argparse
import logging
from collections.abc import Sequence
from difflib import SequenceMatcher
from enum import Enum
from pathlib import Path
from typing import Self, override
from urllib.parse import urlencode
from urllib.request import urlopen

from disce.models.base import UUIDModelList
from disce.models.cards import Card
from disce.models.exports import DeckExport, ExportedDeck
from disce.tools import format_plural
from pydantic import BaseModel, ConfigDict, ValidationError

_logger = logging.getLogger(__name__)


class ArgumentEnum(Enum):
    """Enum that can be used as argparse argument type."""

    @classmethod
    def parse(cls, argument: str) -> Self:
        """Parse a string into the enum value."""
        member = next((member for member in cls if member.name.casefold() == argument.casefold()), None)
        if member is None:
            msg = f"invalid {cls.__name__} value: {argument}"
            raise argparse.ArgumentTypeError(msg)
        return member

    @override
    def __str__(self) -> str:
        return self.name.lower()


class Language(ArgumentEnum):
    """Language of the answer sides."""

    CHINESE = "zh"
    """Chinese language."""
    ENGLISH = "en"
    """English language."""
    FRENCH = "fr"
    """French language."""
    INDONESIAN = "id"
    """Indonesian language."""
    PORTUGUESE = "pt"
    """Portuguese language."""
    SPANISH = "es"
    """Spanish language."""
    THAI = "th"
    """Thai language."""
    VIETNAMESE = "vi"
    """Vietnamese language."""


class Level(ArgumentEnum):
    """Language level of textbook."""

    A1 = "A1"
    """Beginner level A1."""
    A2_1 = "A2-1"
    """Elementary level A2-1."""
    A2_2 = "A2-2"
    """Elementary level A2-2."""


class TextbookType(ArgumentEnum):
    """Type of textbook."""

    GOI = "vocab"
    """Vocabulary book."""
    KATSUDOO = "act"
    """Activity book."""
    RIKAI = "comp"
    """Comprehension book."""


class WordType(ArgumentEnum):
    """Type of word."""

    ADVERB = "Adverb"
    """Adverb."""
    CONJUNCTION = "Conjunction"
    """Conjunction."""
    EXPRESSION = "Expression"
    """Expression."""
    I_ADJECTIVE = "i-Adjective"
    """i-Adjective."""
    NA_ADJECTIVE = "na-Adjective"
    """na-Adjective."""
    NOUN = "Noun"
    """Noun."""
    OTHERS = "Others"
    """Other words."""
    VERB_GODAN = "Verb1"
    """Godan verb."""
    VERB_ICHIDAN = "Verb2"
    """Ichidan verb."""
    VERB_IRREGULAR = "Verb3"
    """Irregular verb."""


class MarugotoWord(BaseModel):
    """A word from Marugoto API."""

    model_config = ConfigDict(extra="ignore")

    KANA: str
    """Kana reading of the word."""
    KANJI: str
    """Kanji representation of the word."""
    UWRD: str
    """Word in the target language."""


class MarugotoResponse(BaseModel):
    """Response from Marugoto API."""

    model_config = ConfigDict(extra="ignore")

    DATA: list[MarugotoWord]
    """List of words."""


DEFAULT_LANGUAGE = Language.ENGLISH
DEFAULT_LEVEL = Level.A1
DEFAULT_TEXTBOOKS = [TextbookType.KATSUDOO, TextbookType.RIKAI]
DEFAULT_EXCLUDED_WORD_TYPES: list[WordType] = []
NUMBER_OF_LESSONS_PER_LEVEL = 18
NUMBER_OF_LESSONS_PER_TOPIC = 2


def main() -> None:
    """Make sure pyscript.toml is up to date."""
    logging.basicConfig(format="%(message)s", level=logging.INFO)
    arguments = parse_arguments()
    if arguments.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    export = export_marugoto_lessons(
        arguments.lessons,
        language=arguments.language,
        level=arguments.level,
        textbooks=arguments.textbooks,
        excluded_word_types=arguments.excluded_word_types,
    )
    save_exported_decks(export, arguments.output_path)


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--exclude-words",
        dest="excluded_word_types",
        nargs="+",
        type=WordType.parse,
        choices=WordType,
        default=DEFAULT_EXCLUDED_WORD_TYPES,
        help="types of words to exclude (default: %(default)s)",
    )
    parser.add_argument(
        "--language",
        type=Language.parse,
        choices=Language,
        default=DEFAULT_LANGUAGE,
        help="language of the answer sides (default: %(default)s)",
    )
    parser.add_argument(
        "--level",
        type=Level.parse,
        choices=Level,
        default=DEFAULT_LEVEL,
        help="language level of textbook (default: %(default)s)",
    )
    parser.add_argument(
        "--textbooks",
        nargs="+",
        type=TextbookType.parse,
        choices=TextbookType,
        default=DEFAULT_TEXTBOOKS,
        help="type of textbook (default: %(default)s)",
    )
    parser.add_argument("-v", "--verbose", action=argparse.BooleanOptionalAction, help="enable verbose output")
    parser.add_argument(
        "lessons",
        metavar="LESSON",
        nargs="+",
        type=check_lesson_argument,
        help=f"lesson number to include (1-{NUMBER_OF_LESSONS_PER_LEVEL})",
    )
    parser.add_argument("output_path", metavar="OUTPUT_PATH", type=Path, help="path to the output file")
    return parser.parse_args()


def check_lesson_argument(argument: str) -> int:
    """Check that a lesson argument is valid."""
    try:
        lesson = int(argument)
    except ValueError:
        msg = f"must be an integer: {argument}"
        raise argparse.ArgumentTypeError(msg) from None
    if not (1 <= lesson <= NUMBER_OF_LESSONS_PER_LEVEL):
        msg = f"must be between 1 and {NUMBER_OF_LESSONS_PER_LEVEL}: {argument}"
        raise argparse.ArgumentTypeError(msg)
    return lesson


def export_marugoto_lessons(
    lessons: list[int],
    language: Language = DEFAULT_LANGUAGE,
    level: Level = DEFAULT_LEVEL,
    textbooks: Sequence[TextbookType] = tuple(DEFAULT_TEXTBOOKS),
    excluded_word_types: Sequence[WordType] = tuple(DEFAULT_EXCLUDED_WORD_TYPES),
) -> DeckExport:
    """Export Marugoto lessons as an ExportedDeck."""
    _logger.info("exporting %s", format_plural(len(lessons), "lesson"))
    export = DeckExport()
    for lesson in lessons:
        cards = export_marugoto_lesson(
            lesson,
            language=language,
            level=level,
            textbooks=textbooks,
            excluded_word_types=excluded_word_types,
        )
        deck_name = f"Marugoto {level.value} Lesson {lesson}"
        export.decks.append(ExportedDeck(name=deck_name, cards=UUIDModelList(cards)))
    return export


def export_marugoto_lesson(
    lesson: int,
    language: Language = DEFAULT_LANGUAGE,
    level: Level = DEFAULT_LEVEL,
    textbooks: Sequence[TextbookType] = tuple(DEFAULT_TEXTBOOKS),
    excluded_word_types: Sequence[WordType] = tuple(DEFAULT_EXCLUDED_WORD_TYPES),
) -> list[Card]:
    """Export a Marugoto lesson as a list of Cards."""
    params = {
        "ls": str(lesson),
        "lv": level.value,
        "tp": str((lesson - 1) // NUMBER_OF_LESSONS_PER_TOPIC + 1),
        "tx": ",".join(textbook.value for textbook in textbooks),
        "ut": language.value,
    }
    if WordType.OTHERS in excluded_word_types:
        params["class"] = ",".join(word_type.value for word_type in WordType if word_type not in excluded_word_types)
    elif excluded_word_types:
        params["class_ex"] = ",".join(word_type.value for word_type in excluded_word_types)
    _logger.info("fetching words for lesson %d", lesson)
    url = f"https://words.marugotoweb.jp/SearchCategoryAPI?{urlencode(params)}"
    _logger.debug("request URL: %s", url)
    with urlopen(url) as response:
        response_json = response.read()
    try:
        parsed_response = MarugotoResponse.model_validate_json(response_json)
    except ValidationError:
        _logger.error("failed to parse response: %s", response_json)  # noqa: TRY400
        raise
    _logger.info("got %s", format_plural(len(parsed_response.DATA), "word"))
    return [
        Card(
            front=guess_furigana(word.KANJI.strip(), word.KANA.strip()),
            back=process_target_word(word.UWRD.strip(), language),
        )
        for word in parsed_response.DATA
    ]


def guess_furigana(kanji_string: str, kana_string: str) -> str:
    """Guess furigana annotations for a kanji string given its kana reading."""
    matcher = SequenceMatcher(a=kanji_string, b=kana_string)
    parts = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        match tag:
            case "equal":
                parts.append(kanji_string[i1:i2])
            case "replace" | "delete":
                spread_kana_over_kanji(kanji_string[i1:i2], kana_string[j1:j2], parts)
            case "insert":
                # skip okurigana
                pass
            case _:
                msg = f"unknown tag: {tag}"
                raise ValueError(msg)
    return "".join(parts)


def spread_kana_over_kanji(kanji_string: str, kana_string: str, parts: list[str]) -> None:
    """Spread kana reading evenly over kanji characters and append to parts."""
    number_of_kana_per_kanji = len(kana_string) / len(kanji_string)
    last_pos = 0
    for idx, kanji_character in enumerate(kanji_string):
        parts.append(kanji_character)
        next_pos = round((idx + 1) * number_of_kana_per_kanji)
        if last_pos < next_pos:
            parts.append(f"[{kana_string[last_pos:next_pos]}]")
            last_pos = next_pos
    if last_pos < len(kana_string):
        parts.append(f"[{kana_string[last_pos:]}]")


def process_target_word(word: str, language: Language) -> str:
    """Process the target word for export."""
    if language in {Language.ENGLISH, Language.FRENCH, Language.PORTUGUESE, Language.SPANISH}:
        word = word.replace("\uff5e", "~")
        word = word.replace("\ufeff", "")
        if language is not Language.FRENCH:
            word = word.replace(" ?", "?")
    return word


def save_exported_decks(export: DeckExport, output_path: Path) -> None:
    """Save exported decks to a file."""
    _logger.info("saving exported decks to %s", output_path)
    output_path.write_text(export.model_dump_json(exclude_defaults=True, indent=4))


if __name__ == "__main__":
    main()

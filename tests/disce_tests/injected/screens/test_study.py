# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
from enum import StrEnum, auto
from types import SimpleNamespace
from typing import cast
from unittest.mock import call, patch

import pytest
from disce.diffs import Diff
from disce.models.cards import CardSide
from disce.models.configs import Configuration
from disce.models.deck_data import DeckData
from disce.ruby import TokenizedString
from disce.screens.decks import DecksScreen
from disce.screens.study import StudyScreen
from disce.storage.base import AbstractStorage
from pyscript import window

from disce_tests.injected.screens.tools import assert_event_bindings_registered
from disce_tests.injected.tools import assert_hidden, assert_visible


class WithRuby(StrEnum):
    NONE = auto()
    QUESTION = auto()
    ANSWER = auto()


class TestStudyScreen:
    @staticmethod
    @pytest.fixture(params=WithRuby)
    def with_ruby(request: pytest.FixtureRequest, storage: AbstractStorage, ruby_string: str) -> WithRuby:
        with_ruby = cast("WithRuby", request.param)
        if with_ruby is not WithRuby.NONE:
            deck_data = DeckData.load_from_storage(storage, "deck1")
            card = deck_data.cards["deck1_card1"]
            match with_ruby:
                case WithRuby.QUESTION:
                    card.front = ruby_string
                case WithRuby.ANSWER:
                    card.back = ruby_string
                case _:
                    msg = f"invalid with_ruby value: {with_ruby}"
                    raise ValueError(msg)
            deck_data.save_to_storage(storage)
        return with_ruby

    @staticmethod
    @pytest.fixture
    def screen(
        storage: AbstractStorage,
        deck_data_list: list[DeckData],
        with_ruby: WithRuby,  # noqa: ARG004
    ) -> StudyScreen:
        screen = StudyScreen([deck_data.uuid for deck_data in deck_data_list], storage)
        screen.show()
        return screen

    @staticmethod
    @pytest.fixture
    def expected_question_string(with_ruby: WithRuby, ruby_string: str) -> str:
        return ruby_string if with_ruby is WithRuby.QUESTION else "deck1_card1_front"

    @staticmethod
    @pytest.fixture
    def expected_question_without_ruby(with_ruby: WithRuby, string_without_ruby: str) -> str:
        return string_without_ruby if with_ruby is WithRuby.QUESTION else "deck1_card1_front"

    @staticmethod
    @pytest.fixture
    def expected_next_question_text() -> str:
        return "deck1_card2_front"

    @staticmethod
    @pytest.fixture
    def expected_answer_string(with_ruby: WithRuby, ruby_string: str) -> str:
        return ruby_string if with_ruby is WithRuby.ANSWER else "deck1_card1_back"

    @staticmethod
    @pytest.fixture
    def expected_answer_html(with_ruby: WithRuby, ruby_html: str) -> str:
        return ruby_html if with_ruby is WithRuby.ANSWER else "deck1_card1_back"

    @staticmethod
    @pytest.fixture
    def user_answer_text() -> str:
        return "xyz"

    @staticmethod
    @pytest.fixture
    def fill_answer_textbox(
        storage: AbstractStorage, configuration: Configuration, screen: StudyScreen, user_answer_text: str
    ) -> None:
        configuration.typewriter_mode = True
        configuration.save_to_storage(storage)
        screen.render()
        answer_textbox = screen.select_child(".disce-answer-textbox")
        answer_textbox.value = user_answer_text

    @staticmethod
    @pytest.fixture
    def expected_diff_html(user_answer_text: str, expected_answer_string: str) -> str:
        diff = Diff.from_strings(user_answer_text, expected_answer_string)
        return diff.to_html()

    @staticmethod
    def test_element(screen: DecksScreen) -> None:
        assert screen.element.id == "disce-study-screen"

    @staticmethod
    def test_set_current_card(screen: StudyScreen, expected_next_question_text: str) -> None:
        screen.set_current_card()
        assert screen._current_card.front == expected_next_question_text  # noqa: SLF001
        assert screen._current_card_side is CardSide.FRONT  # noqa: SLF001

    @staticmethod
    @pytest.mark.parametrize("typewriter_mode", [False, True])
    def test_render(
        storage: AbstractStorage,
        configuration: Configuration,
        screen: StudyScreen,
        expected_question_without_ruby: str,
        *,
        typewriter_mode: bool,
    ) -> None:
        configuration.typewriter_mode = typewriter_mode
        configuration.save_to_storage(storage)
        screen.render()
        TestStudyScreen._assert_render(screen, expected_question_without_ruby, expected_typewriter_mode=typewriter_mode)

    @staticmethod
    def _assert_render(
        screen: StudyScreen, expected_question_string: str, *, expected_typewriter_mode: bool = False
    ) -> None:
        assert (
            screen.select_child(".disce-study-card-question-side .disce-study-card-side-content").innerText
            == expected_question_string
        )
        assert screen.select_child(".disce-study-card-answer-side .disce-study-card-side-content").innerHTML == ""
        answer_textbox = screen.select_child(".disce-answer-textbox")
        assert answer_textbox.value == ""
        assert_visible(screen.select_child(".disce-show-answer-btn"), visible=not expected_typewriter_mode)
        assert_visible(answer_textbox, visible=expected_typewriter_mode)
        assert_visible(screen.select_child(".disce-submit-answer-btn"), visible=expected_typewriter_mode)
        assert_event_bindings_registered(screen.get_static_event_bindings())

    @staticmethod
    @pytest.mark.parametrize("is_correct", [False, True])
    def test_handle_answer(storage: AbstractStorage, screen: StudyScreen, *, is_correct: bool) -> None:
        target = screen.select_child(".disce-correct-answer-btn" if is_correct else ".disce-wrong-answer-btn")
        screen.handle_answer(SimpleNamespace(currentTarget=target))
        deck_data = DeckData.load_from_storage(storage, "deck1")
        card = deck_data.cards["deck1_card1"]
        assert card.front_answer_history == [False, False, False, False, False, is_correct]
        TestStudyScreen._assert_render(
            screen, str(TokenizedString.from_string(deck_data.cards["deck1_card2"].front).strip_ruby())
        )

    @staticmethod
    def test_skip_card(screen: StudyScreen, expected_next_question_text: str) -> None:
        screen.skip_card()
        TestStudyScreen._assert_render(screen, expected_next_question_text)

    @staticmethod
    def test_show_answer(screen: StudyScreen, expected_answer_html: str) -> None:
        with patch.object(screen, "read_front_side") as read_front_side_mock:
            screen.show_answer()
        assert (
            screen.select_child(".disce-study-card-answer-side .disce-study-card-side-content").innerHTML
            == expected_answer_html
        )
        assert_hidden(screen.select_child(".disce-show-answer-btn"))
        assert read_front_side_mock.call_args_list == [call()]

    @staticmethod
    def test_handle_textbox_keydown(
        screen: StudyScreen,
        fill_answer_textbox: None,  # noqa: ARG004
        expected_diff_html: str,
    ) -> None:
        event = window.Event.new("keydown")
        event.key = "Enter"
        with patch.object(screen, "read_front_side") as read_front_side_mock:
            screen.handle_textbox_keydown(event)
        TestStudyScreen._assert_submit_answer(screen, expected_diff_html)
        assert read_front_side_mock.call_args_list == [call()]

    @staticmethod
    def test_handle_textbox_keydown_no_enter(screen: StudyScreen, fill_answer_textbox: None) -> None:  # noqa: ARG004
        event = window.Event.new("keydown")
        event.key = "Space"
        screen.handle_textbox_keydown(event)
        assert_visible(screen.select_child(".disce-answer-textbox"))

    @staticmethod
    def test_submit_answer(
        screen: StudyScreen,
        fill_answer_textbox: None,  # noqa: ARG004
        expected_diff_html: str,
    ) -> None:
        with patch.object(screen, "read_front_side") as read_front_side_mock:
            screen.submit_answer()
        TestStudyScreen._assert_submit_answer(screen, expected_diff_html)
        assert read_front_side_mock.call_args_list == [call()]

    @staticmethod
    def _assert_submit_answer(screen: StudyScreen, expected_diff_html: str) -> None:
        assert (
            screen.select_child(".disce-study-card-answer-side .disce-study-card-side-content").innerHTML
            == expected_diff_html
        )
        assert_hidden(screen.select_child(".disce-answer-textbox"))
        assert_hidden(screen.select_child(".disce-submit-answer-btn"))

    @staticmethod
    def test_read_front_side(
        configuration: Configuration, screen: StudyScreen, expected_question_without_ruby: str
    ) -> None:
        with patch("disce.screens.study.speak") as speak_mock:
            screen.read_front_side()
        assert speak_mock.call_args_list == [
            call(
                expected_question_without_ruby,
                configuration.front_side_tts_voice,
                pitch=configuration.tts_pitch,
                rate=configuration.tts_rate,
                volume=configuration.tts_volume,
            )
        ]

    @staticmethod
    def test_read_front_side_no_voice(
        storage: AbstractStorage, configuration: Configuration, screen: StudyScreen
    ) -> None:
        configuration.front_side_tts_voice = None
        configuration.save_to_storage(storage)
        with patch("disce.screens.study.speak") as speak_mock:
            screen.read_front_side()
        assert speak_mock.call_args_list == []

    @staticmethod
    def test_read_front_side_empty_text(screen: StudyScreen) -> None:
        screen._current_card.front = ""  # noqa: SLF001
        with patch("disce.screens.study.speak") as speak_mock:
            screen.read_front_side()
        assert speak_mock.call_args_list == []

    @staticmethod
    def test_back_to_decks_screen(storage: AbstractStorage, screen: StudyScreen) -> None:
        screen.back_to_decks_screen()
        assert_hidden(screen)
        assert_visible(DecksScreen(storage))

    @staticmethod
    def test_get_tokenized_side(
        screen: StudyScreen, expected_question_string: str, expected_answer_string: str
    ) -> None:
        assert screen.get_tokenized_side(question=True) == TokenizedString.from_string(expected_question_string)
        assert screen.get_tokenized_side(question=False) == TokenizedString.from_string(expected_answer_string)

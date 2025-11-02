#!/usr/bin/env python
# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.


from types import SimpleNamespace

import pytest
from disce.data import CardSide, Configuration, DeckData
from disce.diffs import Diff
from disce.screens.decks import DecksScreen
from disce.screens.study import StudyScreen
from disce.storage.base import AbstractStorage
from pyscript import window

from disce_tests.injected.screens.tools import assert_event_bindings_registered
from disce_tests.injected.tools import assert_hidden, assert_visible


class TestStudyScreen:
    @staticmethod
    @pytest.fixture
    def screen(storage: AbstractStorage, deck_data_list: list[DeckData]) -> StudyScreen:
        screen = StudyScreen([deck_data.uuid for deck_data in deck_data_list], storage)
        screen.show()
        return screen

    @staticmethod
    @pytest.fixture
    def expected_question_text() -> str:
        return "deck1_card1_front"

    @staticmethod
    @pytest.fixture
    def expected_answer_text() -> str:
        return "deck1_card1_back"

    @staticmethod
    @pytest.fixture
    def user_answer_text() -> str:
        return "deck1_card5_back"

    @staticmethod
    @pytest.fixture
    def fill_answer_textbox(storage: AbstractStorage, screen: StudyScreen, user_answer_text: str) -> None:
        configuration = Configuration.load_from_storage_or_create(storage)
        configuration.typewriter_mode = True
        configuration.save_to_storage(storage)
        screen.render()
        answer_textbox = screen.select_child(".disce-answer-textbox")
        answer_textbox.value = user_answer_text

    @staticmethod
    @pytest.fixture
    def expected_diff_html(user_answer_text: str, expected_answer_text: str) -> str:
        diff = Diff.from_strings(user_answer_text, expected_answer_text)
        return diff.to_html()

    @staticmethod
    def test_element(screen: DecksScreen) -> None:
        assert screen.element.id == "disce-study-screen"

    @staticmethod
    def test_get_card_to_study(screen: StudyScreen, expected_question_text: str) -> None:
        card, card_side = screen.get_card_to_study()
        assert card.front == expected_question_text
        expected_card_side = CardSide.FRONT if "front" in expected_question_text else CardSide.BACK
        assert card_side is expected_card_side

    @staticmethod
    @pytest.mark.parametrize("typewriter_mode", [False, True])
    def test_render(
        storage: AbstractStorage, screen: StudyScreen, expected_question_text: str, *, typewriter_mode: bool
    ) -> None:
        configuration = Configuration.load_from_storage_or_create(storage)
        configuration.typewriter_mode = typewriter_mode
        configuration.save_to_storage(storage)
        screen.render()
        TestStudyScreen._assert_render(screen, expected_question_text, expected_typewriter_mode=typewriter_mode)

    @staticmethod
    def _assert_render(
        screen: StudyScreen, expected_question_text: str, *, expected_typewriter_mode: bool = False
    ) -> None:
        assert (
            screen.select_child(".disce-study-card-question-side .disce-study-card-side-content").innerText
            == expected_question_text
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
        TestStudyScreen._assert_render(screen, card.back)

    @staticmethod
    def test_skip_card(screen: StudyScreen, expected_question_text: str) -> None:
        screen.skip_card()
        TestStudyScreen._assert_render(screen, expected_question_text)

    @staticmethod
    def test_show_answer(screen: StudyScreen, expected_answer_text: str) -> None:
        screen.show_answer()
        assert (
            screen.select_child(".disce-study-card-answer-side .disce-study-card-side-content").innerText
            == expected_answer_text
        )
        assert_hidden(screen.select_child(".disce-show-answer-btn"))

    @staticmethod
    def test_handle_textbox_keydown(
        screen: StudyScreen,
        fill_answer_textbox: None,  # noqa: ARG004
        expected_diff_html: str,
    ) -> None:
        event = window.Event.new("keydown")
        event.key = "Enter"
        screen.handle_textbox_keydown(event)
        TestStudyScreen._assert_submit_answer(screen, expected_diff_html)

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
        screen.submit_answer()
        TestStudyScreen._assert_submit_answer(screen, expected_diff_html)

    @staticmethod
    def _assert_submit_answer(screen: StudyScreen, expected_diff_html: str) -> None:
        assert (
            screen.select_child(".disce-study-card-answer-side .disce-study-card-side-content").innerHTML
            == expected_diff_html
        )
        assert_hidden(screen.select_child(".disce-answer-textbox"))
        assert_hidden(screen.select_child(".disce-submit-answer-btn"))

    @staticmethod
    def test_back_to_decks_screen(storage: AbstractStorage, screen: StudyScreen) -> None:
        screen.back_to_decks_screen()
        assert_hidden(screen)
        assert_visible(DecksScreen(storage))

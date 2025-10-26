#!/usr/bin/env python
# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Screen for studying a deck."""

from collections.abc import Sequence
from typing import override

import disce.screens.decks as decks_screen
from disce.data import Card, CardSide, Configuration, DeckData
from disce.diffs import Diff
from disce.pyscript import Event, EventBinding, hide_element, show_element
from disce.screens.base import AbstractScreen
from disce.storage.base import AbstractStorage


class StudyScreen(AbstractScreen):
    """Screen for studying a deck."""

    def __init__(self, deck_uuids: Sequence[str], storage: AbstractStorage) -> None:
        """Initialize the screen."""
        super().__init__("#disce-study-screen")
        self._deck_uuids = list(deck_uuids)
        self._storage = storage
        self._configuration = Configuration.load_from_storage_or_create(self._storage)
        self._deck_data_list = [DeckData.load_from_storage(self._storage, uuid) for uuid in deck_uuids]
        self._merged_deck_data = DeckData.from_merge(self._deck_data_list)
        self._card_uuid_to_deck_uuid = {
            card.uuid: deck_data.uuid for deck_data in self._deck_data_list for card in deck_data.cards
        }
        self._current_card, self._current_card_side = self.get_card_to_study()

    def get_card_to_study(self) -> tuple[Card, CardSide]:
        """Get the card and side that should be studied next (based on the answer history)."""
        return self._merged_deck_data.get_card_to_study(history_length=self._configuration.history_length)

    @override
    def _get_static_event_bindings(self) -> list[EventBinding]:
        return [
            EventBinding(
                element=self.select_child(".disce-correct-answer-btn"), event="click", listener=self.handle_answer
            ),
            EventBinding(
                element=self.select_child(".disce-wrong-answer-btn"), event="click", listener=self.handle_answer
            ),
            EventBinding(element=self.select_child(".disce-skip-card-btn"), event="click", listener=self.skip_card),
            EventBinding(element=self.select_child(".disce-show-answer-btn"), event="click", listener=self.show_answer),
            EventBinding(
                element=self.select_child(".disce-answer-textbox"),
                event="keydown",
                listener=self.handle_textbox_keydown,
            ),
            EventBinding(
                element=self.select_child(".disce-submit-answer-btn"), event="click", listener=self.submit_answer
            ),
            EventBinding(
                element=self.select_child(".disce-back-to-decks-screen-btn"),
                event="click",
                listener=self.back_to_decks_screen,
            ),
        ]

    @override
    def render(self) -> None:
        self._configuration = Configuration.load_from_storage_or_create(self._storage)
        typewriter_mode = self._configuration.typewriter_mode
        self.select_child(
            ".disce-study-card-question-side .disce-study-card-side-content"
        ).innerText = self._current_card.get_side(self._current_card_side)
        self.select_child(".disce-study-card-answer-side .disce-study-card-side-content").innerHTML = ""
        answer_textbox = self.select_child(".disce-answer-textbox")
        answer_textbox.value = ""
        show_element(self.select_child(".disce-show-answer-btn"), show=not typewriter_mode)
        show_element(answer_textbox, show=typewriter_mode)
        show_element(self.select_child(".disce-submit-answer-btn"), show=typewriter_mode)
        if typewriter_mode:
            answer_textbox.focus()

    def handle_answer(self, event: Event) -> None:
        """Handle the answer given by the user."""
        is_correct = event.currentTarget == self.select_child(".disce-correct-answer-btn")
        deck_data = DeckData.load_from_storage(self._storage, self._card_uuid_to_deck_uuid[self._current_card.uuid])
        for current_deck_data in [deck_data, self._merged_deck_data]:
            card = current_deck_data.cards[self._current_card.uuid]
            card.record_answer(self._current_card_side, correct=is_correct)
        deck_data.save_to_storage(self._storage)
        self.skip_card()

    def skip_card(self, _event: Event | None = None) -> None:
        """Skip the current card and go to the next one."""
        self._current_card, self._current_card_side = self.get_card_to_study()
        self.render()

    def show_answer(self, _event: Event | None = None) -> None:
        """Show the answer side of the current card."""
        self.select_child(
            ".disce-study-card-answer-side .disce-study-card-side-content"
        ).innerText = self._current_card.get_opposite_side(self._current_card_side)
        hide_element(self.select_child(".disce-show-answer-btn"))

    def handle_textbox_keydown(self, event: Event) -> None:
        """Handle keydown events in the answer textbox."""
        if event.key == "Enter":
            self.submit_answer()

    def submit_answer(self, _event: Event | None = None) -> None:
        """Submit the answer typed by the user and show the answer side."""
        user_answer = self.select_child(".disce-answer-textbox").value.strip()
        correct_answer = self._current_card.get_opposite_side(self._current_card_side).strip()
        diff = Diff.from_strings(user_answer, correct_answer)
        self.select_child(".disce-study-card-answer-side .disce-study-card-side-content").innerHTML = diff.to_html()
        hide_element(self.select_child(".disce-answer-textbox"))
        hide_element(self.select_child(".disce-submit-answer-btn"))

    def back_to_decks_screen(self, _event: Event | None = None) -> None:
        """Go back to the decks screen."""
        decks_screen.DecksScreen(self._storage).show()
        self.hide()

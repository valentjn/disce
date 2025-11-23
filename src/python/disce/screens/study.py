#!/usr/bin/env python
# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Screen for studying a deck."""

from collections.abc import Sequence
from typing import TYPE_CHECKING, override

import disce.screens.decks as decks_screen
from disce.diffs import Diff
from disce.furigana import TokenizedString
from disce.models.configs import Configuration
from disce.models.deck_data import DeckData
from disce.models.exports import ExportedDeck
from disce.pyscript import Event, EventBinding, hide_element, show_element
from disce.screens.base import AbstractScreen
from disce.storage.base import AbstractStorage

if TYPE_CHECKING:
    from disce.models.cards import Card, CardSide


class StudyScreen(AbstractScreen):
    """Screen for studying a deck."""

    _CARD_HISTORY_LIMIT = 5
    """Maximum number of previously studied cards to remember."""

    def __init__(self, deck_uuids: Sequence[str], storage: AbstractStorage) -> None:
        """Initialize the screen."""
        super().__init__("#disce-study-screen")
        self._storage = storage
        deck_data_list = [DeckData.load_from_storage(storage, uuid) for uuid in deck_uuids]
        self._merged_deck_data = DeckData.from_merge(deck_data_list)
        self._card_uuid_to_deck_uuid = {
            card.uuid: deck_data.uuid for deck_data in deck_data_list for card in deck_data.cards
        }
        self._card_history: list[tuple[Card, CardSide]] = []
        self.set_current_card()

    def set_current_card(self) -> None:
        """Set the current card to study."""
        configuration = Configuration.load_from_storage_or_create(self._storage)
        self._current_card, self._current_card_side = self._merged_deck_data.get_card_to_study(
            exclude=[card for card, _ in self._card_history], history_length=configuration.history_length
        )
        self._card_history.append((self._current_card, self._current_card_side))
        self._card_history = self._card_history[-self._CARD_HISTORY_LIMIT :]

    @override
    def get_static_event_bindings(self) -> list[EventBinding]:
        return [
            EventBinding(self.select_child(".disce-correct-answer-btn"), "click", self.handle_answer),
            EventBinding(self.select_child(".disce-wrong-answer-btn"), "click", self.handle_answer),
            EventBinding(self.select_child(".disce-skip-card-btn"), "click", self.skip_card),
            EventBinding(self.select_child(".disce-show-answer-btn"), "click", self.show_answer),
            EventBinding(self.select_child(".disce-answer-textbox"), "keydown", self.handle_textbox_keydown),
            EventBinding(self.select_child(".disce-submit-answer-btn"), "click", self.submit_answer),
            EventBinding(self.select_child(".disce-back-to-decks-screen-btn"), "click", self.back_to_decks_screen),
        ]

    @override
    def render(self) -> None:
        configuration = Configuration.load_from_storage_or_create(self._storage)
        typewriter_mode = configuration.typewriter_mode
        self.select_child(".disce-study-card-question-side .disce-study-card-side-content").innerText = str(
            self.get_tokenized_side(question=True).strip_furigana()
        )
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
        deck_uuid = self._card_uuid_to_deck_uuid[self._current_card.uuid]
        deck_data = DeckData.load_from_storage(self._storage, deck_uuid)
        for current_deck_data in [deck_data, self._merged_deck_data]:
            card = current_deck_data.cards[self._current_card.uuid]
            card.record_answer(self._current_card_side, correct=is_correct)
        deck_data.save_to_storage(self._storage)
        configuration = Configuration.load_from_storage_or_create(self._storage)
        deck_metadata = configuration.deck_metadata[deck_uuid]
        deck_metadata = ExportedDeck.from_deck(deck_data, deck_metadata).to_deck_metadata()
        configuration.deck_metadata.set(deck_metadata)
        configuration.save_to_storage(self._storage)
        self.skip_card()

    def skip_card(self, _event: Event | None = None) -> None:
        """Skip the current card and go to the next one."""
        self.set_current_card()
        self.render()

    def show_answer(self, _event: Event | None = None) -> None:
        """Show the answer side of the current card."""
        self.select_child(
            ".disce-study-card-question-side .disce-study-card-side-content"
        ).innerHTML = self.get_tokenized_side(question=True).html
        self.select_child(
            ".disce-study-card-answer-side .disce-study-card-side-content"
        ).innerHTML = self.get_tokenized_side(question=False).html
        hide_element(self.select_child(".disce-show-answer-btn"))

    def handle_textbox_keydown(self, event: Event) -> None:
        """Handle keydown events in the answer textbox."""
        if event.key == "Enter":
            self.submit_answer()

    def submit_answer(self, _event: Event | None = None) -> None:
        """Submit the answer typed by the user and show the answer side."""
        self.select_child(
            ".disce-study-card-question-side .disce-study-card-side-content"
        ).innerHTML = self.get_tokenized_side(question=True).html
        user_answer = self.select_child(".disce-answer-textbox").value.strip()
        correct_answer = self._current_card.get_side(self._current_card_side.opposite).strip()
        diff = Diff.from_strings(user_answer, correct_answer)
        self.select_child(".disce-study-card-answer-side .disce-study-card-side-content").innerHTML = diff.to_html()
        hide_element(self.select_child(".disce-answer-textbox"))
        hide_element(self.select_child(".disce-submit-answer-btn"))

    def back_to_decks_screen(self, _event: Event | None = None) -> None:
        """Go back to the decks screen."""
        decks_screen.DecksScreen(self._storage).show()
        self.hide()

    def get_tokenized_side(self, *, question: bool) -> TokenizedString:
        """Get the tokenized string for either the question or answer side of the current card."""
        return TokenizedString.from_string(
            self._current_card.get_side(self._current_card_side if question else self._current_card_side.opposite)
        )

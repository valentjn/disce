#!/usr/bin/env python
# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Data models."""

import uuid

from pydantic import BaseModel, Field
from pyscript import window


class Card(BaseModel):
    """A flashcard."""

    front: str = ""
    """Text on the front side of the card (e.g., question or term in foreign language)."""
    back: str = ""
    """Text on the back side of the card (e.g., answer or term in native language)."""
    enabled: bool = True
    """Whether the card is enabled for review."""
    answer_history: list[bool] = []
    """History of answers (True for correct, False for incorrect, most recent last, reset when card is edited)."""


class Deck(BaseModel):
    """A deck of flashcards."""

    uuid: str = Field(default_factory=lambda: str(uuid.uuid4()))
    """Unique identifier for the deck."""
    name: str = "New Deck"
    """Name of the deck."""
    cards: list[Card] = []
    """List of cards in the deck."""

    def merge(self, other: "Deck") -> None:
        """Merge another deck into this one."""
        existing_cards = {(card.front, card.back): (index, card) for index, card in enumerate(self.cards)}
        for card in other.cards:
            existing_card_index, existing_card = existing_cards.get((card.front, card.back), (None, None))
            if existing_card_index is not None and existing_card is not None:
                self.cards[existing_card_index] = existing_card.model_copy(
                    update={
                        "enabled": existing_card.enabled or card.enabled,
                        "answer_history": existing_card.answer_history + card.answer_history,
                    }
                )
            else:
                self.cards.append(card)
                existing_card_index = len(self.cards) - 1
            existing_cards[(card.front, card.back)] = (existing_card_index, self.cards[existing_card_index])


class SavedData(BaseModel):
    """All saved data of the application."""

    decks: list[Deck] = []
    """List of decks."""

    def deck_exists(self, uuid: str) -> bool:
        """Check if a deck with the given UUID exists."""
        try:
            self._get_deck_index(uuid)
        except ValueError:
            return False
        return True

    def get_deck(self, uuid: str) -> Deck:
        """Get a deck by its UUID."""
        return self.decks[self._get_deck_index(uuid)]

    def set_deck(self, deck: Deck) -> None:
        """Add or update a deck."""
        try:
            index = self._get_deck_index(deck.uuid)
        except ValueError:
            self.decks.append(deck)
        else:
            self.decks[index] = deck

    def delete_deck(self, uuid: str) -> None:
        """Delete a deck by its UUID."""
        del self.decks[self._get_deck_index(uuid)]

    def _get_deck_index(self, uuid: str) -> int:
        """Get the index of a deck by its UUID."""
        index = next((index for index, deck in enumerate(self.decks) if deck.uuid == uuid), None)
        if index is None:
            msg = f"deck with UUID {uuid} not found"
            raise ValueError(msg)
        return index

    @staticmethod
    def load_from_local_storage() -> "SavedData":
        """Load saved data from local storage."""
        json = window.localStorage.getItem("saved_data_json")
        if not json:
            return SavedData(decks=[])
        return SavedData.model_validate_json(json)

    def save_to_local_storage(self) -> None:
        """Save data to local storage."""
        window.localStorage.setItem("saved_data_json", self.model_dump_json())

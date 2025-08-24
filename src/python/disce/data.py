#!/usr/bin/env python
# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Data models."""

from pydantic import BaseModel
from pyscript import window  # type: ignore[import-not-found]


class Card(BaseModel):
    """A flashcard."""

    front: str
    """Text on the front side of the card (e.g., question or term in foreign language)."""
    back: str
    """Text on the back side of the card (e.g., answer or term in native language)."""
    answer_history: list[bool] = []
    """History of answers (True for correct, False for incorrect, most recent last, reset when card is edited)."""


class Deck(BaseModel):
    """A deck of flashcards."""

    name: str
    """Name of the deck."""
    description: str = ""
    """Optional additional information about the deck."""
    cards: list[Card]
    """List of cards in the deck."""


class SavedData(BaseModel):
    """All saved data of the application."""

    decks: list[Deck]
    """List of decks."""

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

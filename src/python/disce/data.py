#!/usr/bin/env python
# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Data models."""

import random
from abc import ABC, abstractmethod
from enum import StrEnum, auto
from typing import Self, override
from uuid import uuid4

from pydantic import BaseModel, Field, NonNegativeInt
from pyscript import window

from disce.tools import log_time


class StorageModel(BaseModel, ABC):
    """Base model with storage support."""

    @staticmethod
    @abstractmethod
    def get_storage_key(uuid: str | None) -> str:
        """Get the key to use for storage."""
        raise NotImplementedError

    @classmethod
    def exists_in_storage(cls, uuid: str | None = None) -> bool:
        """Check if data exists in storage."""
        storage_key = cls.get_storage_key(uuid)
        return any(window.localStorage.key(index) == storage_key for index in range(window.localStorage.length))

    @classmethod
    def load_from_storage(cls, uuid: str | None = None) -> Self:
        """Load saved data from storage."""
        with log_time("loaded data from storage"):
            json = window.localStorage.getItem(cls.get_storage_key(uuid))
        with log_time("parsed data"):
            if not json:
                return cls()
            return cls.model_validate_json(json)

    def save_to_storage(self) -> None:
        """Save data to storage."""
        window.navigator.storage.persist()
        with log_time("serialized data"):
            json = self.model_dump_json()
        with log_time("saved data to storage"):
            window.localStorage.setItem(self.get_storage_key(getattr(self, "uuid", None)), json)

    @classmethod
    def delete_from_storage(cls, uuid: str | None = None) -> None:
        """Delete data from storage."""
        with log_time("deleted data from storage"):
            window.localStorage.removeItem(cls.get_storage_key(uuid))


class UUIDModel(BaseModel):
    """Base model with a UUID."""

    @staticmethod
    def generate_uuid() -> str:
        """Generate a new UUID."""
        return str(uuid4())

    uuid: str = Field(default_factory=generate_uuid)
    """Unique identifier."""


class Card(UUIDModel):
    """A flashcard."""

    front: str = ""
    """Text on the front side of the card (e.g., question or term in foreign language)."""
    back: str = ""
    """Text on the back side of the card (e.g., answer or term in native language)."""
    enabled: bool = True
    """Whether the card is enabled for review."""
    front_answer_history: list[bool] = []
    """History of answers when asked for front (correct/incorrect, most recent last, reset when card is edited)."""
    back_answer_history: list[bool] = []
    """History of answers when asked for back (correct/incorrect, most recent last, reset when card is edited)."""


class CardSide(StrEnum):
    """Side of a flashcard."""

    FRONT = auto()
    BACK = auto()


class DeckData(StorageModel, UUIDModel):
    """A deck of flashcards."""

    cards: list[Card] = []
    """List of cards in the deck."""

    @staticmethod
    @override
    def get_storage_key(uuid: str | None) -> str:
        if uuid is None:
            msg = "uuid must be provided"
            raise ValueError(msg)
        return f"deck_data_{uuid}"

    def merge(self, other: "DeckData") -> None:
        """Merge another deck into this one."""
        existing_cards = {(card.front, card.back): (index, card) for index, card in enumerate(self.cards)}
        for card in other.cards:
            existing_card_index, existing_card = existing_cards.get((card.front, card.back), (None, None))
            if existing_card_index is not None and existing_card is not None:
                self.cards[existing_card_index] = existing_card.model_copy(
                    update={
                        "enabled": existing_card.enabled or card.enabled,
                        "front_answer_history": existing_card.front_answer_history + card.front_answer_history,
                        "back_answer_history": existing_card.back_answer_history + card.back_answer_history,
                    }
                )
            else:
                self.cards.append(card.model_copy(update={"uuid": UUIDModel.generate_uuid()}))
                existing_card_index = len(self.cards) - 1
            existing_cards[(card.front, card.back)] = (existing_card_index, self.cards[existing_card_index])

    def get_card_to_study(self, history_length: int, seed: int | None = None) -> tuple[Card, CardSide]:
        """Get the card and side that should be studied next (based on the answer history)."""
        candidates: list[tuple[Card, CardSide]] = []
        minimum_history_length = None
        minimum_score = None
        for card in self.cards:
            if not card.enabled:
                continue
            for side in CardSide:
                append = False
                answer_history = card.front_answer_history if side is CardSide.FRONT else card.back_answer_history
                score = sum(answer_history[-history_length:])
                if minimum_history_length is None or len(answer_history) < minimum_history_length:
                    minimum_history_length = len(answer_history)
                    minimum_score = score
                    candidates.clear()
                    append = True
                elif len(answer_history) == minimum_history_length:
                    if minimum_score is None or score < minimum_score:
                        minimum_score = score
                        candidates.clear()
                        append = True
                    elif score == minimum_score:
                        append = True
                if append:
                    candidates.append((card, side))
        if not candidates:
            msg = "no enabled cards in deck"
            raise ValueError(msg)
        rng = random.Random(seed)
        return rng.choice(candidates)


class DeckMetadata(UUIDModel):
    """Metadata for a deck of flashcards."""

    name: str = "New Deck"
    """Name of the deck."""
    number_of_cards: int = 0
    """Number of cards in the deck."""


class ExportedDeck(BaseModel):
    """A deck exported for sharing or backup."""

    data: DeckData
    """The actual deck data."""
    metadata: DeckMetadata
    """Metadata for the deck."""


class DeckExport(BaseModel):
    """A collection of exported decks."""

    decks: list[ExportedDeck] = []
    """List of exported decks."""


class Configuration(StorageModel):
    """Configuration for the application."""

    deck_metadata: list[DeckMetadata] = []
    """List of metadata for all decks."""
    history_length: NonNegativeInt = 5
    """Number of recent answers to consider when selecting the next card to learn."""
    typewriter_mode: bool = False
    """Whether to enable typewriter mode (requiring full text input for answers)."""

    @staticmethod
    @override
    def get_storage_key(uuid: str | None) -> str:
        return "configuration"

    def deck_metadata_exists(self, uuid: str) -> bool:
        """Check if deck metadata with the given UUID exists."""
        try:
            self._get_deck_metadata_index(uuid)
        except ValueError:
            return False
        return True

    def get_deck_metadata(self, uuid: str) -> DeckMetadata:
        """Get deck metadata by its UUID."""
        return self.deck_metadata[self._get_deck_metadata_index(uuid)]

    def set_deck_metadata(self, metadata: DeckMetadata) -> None:
        """Add or update deck metadata."""
        try:
            index = self._get_deck_metadata_index(metadata.uuid)
        except ValueError:
            self.deck_metadata.append(metadata)
        else:
            self.deck_metadata[index] = metadata

    def delete_deck_metadata(self, uuid: str) -> None:
        """Delete deck metadata by its UUID."""
        del self.deck_metadata[self._get_deck_metadata_index(uuid)]

    def _get_deck_metadata_index(self, uuid: str) -> int:
        """Get the index of deck metadata by its UUID."""
        index = next((index for index, metadata in enumerate(self.deck_metadata) if metadata.uuid == uuid), None)
        if index is None:
            msg = f"deck metadata with UUID {uuid} not found"
            raise ValueError(msg)
        return index

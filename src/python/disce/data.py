#!/usr/bin/env python
# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Data models."""

import random
from abc import ABC, abstractmethod
from collections.abc import Iterator, Sequence
from copy import deepcopy
from enum import StrEnum, auto
from typing import Self, override
from uuid import uuid4

from pydantic import BaseModel, Field, NonNegativeInt, RootModel

from disce.storage.base import AbstractStorage
from disce.tools import log_time

type UUID = str


class AbstractStoredModel(BaseModel, ABC):
    """Base model for data that can be stored in a storage backend."""

    @staticmethod
    @abstractmethod
    def get_storage_key(uuid: UUID | None) -> str:
        """Get the key to use for storage."""
        raise NotImplementedError

    @classmethod
    def exists_in_storage(cls, storage: AbstractStorage, uuid: UUID | None = None) -> bool:
        """Check if data exists in storage."""
        storage_key = cls.get_storage_key(uuid)
        return storage.has(storage_key)

    @classmethod
    def load_from_storage(cls, storage: AbstractStorage, uuid: UUID | None = None) -> Self:
        """Load saved data from storage."""
        with log_time("loaded data from storage"):
            json = storage.load(cls.get_storage_key(uuid))
        with log_time("parsed data"):
            return cls.model_validate_json(json)

    def save_to_storage(self, storage: AbstractStorage) -> None:
        """Save data to storage."""
        with log_time("serialized data"):
            json = self.model_dump_json()
        with log_time("saved data to storage"):
            storage.save(self.get_storage_key(getattr(self, "uuid", None)), json)

    @classmethod
    def delete_from_storage(cls, storage: AbstractStorage, uuid: UUID | None = None) -> None:
        """Delete data from storage."""
        with log_time("deleted data from storage"):
            storage.delete(cls.get_storage_key(uuid))


class UUIDModel(BaseModel):
    """Base model with a UUID."""

    @staticmethod
    def generate_uuid() -> UUID:
        """Generate a new UUID."""
        return str(uuid4())

    uuid: UUID = Field(default_factory=generate_uuid)
    """Unique identifier."""


class UUIDModelList[T: UUIDModel](RootModel[list[T]]):
    """Base model for a list of UUID models."""

    root: list[T] = []
    """List of UUID models."""

    @override
    def __iter__(self) -> Iterator[T]:  # type: ignore[override]
        """Iterate over the items in the list."""
        return iter(self.root)

    def __len__(self) -> int:
        """Get the number of items in the list."""
        return len(self.root)

    def __contains__(self, uuid: UUID) -> bool:
        """Check if an item with the given UUID exists in the list."""
        try:
            self._get_index(uuid)
        except KeyError:
            return False
        return True

    def __getitem__(self, uuid: UUID) -> T:
        """Get an item by its UUID."""
        return self.root[self._get_index(uuid)]

    def set(self, value: T) -> None:
        """Set an item by its UUID (add if it doesn't exist)."""
        try:
            index = self._get_index(value.uuid)
        except KeyError:
            self.root.append(value)
        else:
            self.root[index] = value

    def __delitem__(self, uuid: UUID) -> None:
        """Delete an item by its UUID."""
        del self.root[self._get_index(uuid)]

    def _get_index(self, uuid: UUID) -> int:
        """Get the index of item by its UUID."""
        index = next((index for index, item in enumerate(self.root) if item.uuid == uuid), None)
        if index is None:
            raise KeyError(uuid)
        return index


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
    """Front side (e.g., question or term in foreign language)."""
    BACK = auto()
    """Back side (e.g., answer or term in native language)."""


class DeckData(AbstractStoredModel, UUIDModel):
    """A deck of flashcards."""

    cards: UUIDModelList[Card] = UUIDModelList()
    """List of cards in the deck."""

    @staticmethod
    @override
    def get_storage_key(uuid: UUID | None) -> str:
        if uuid is None:
            msg = "uuid must be provided"
            raise ValueError(msg)
        return f"deck_data_{uuid}"

    @staticmethod
    def from_merge(deck_data_list: "Sequence[DeckData]") -> "DeckData":
        """Create a new deck by merging multiple decks."""
        merged_deck = DeckData()
        for deck_data in deck_data_list:
            merged_deck.merge(deepcopy(deck_data))
        return merged_deck

    def merge(self, other: "DeckData") -> None:
        """Merge another deck into this one.

        Possibly updates cards of this and the other deck in place.
        """
        existing_cards = {(card.front, card.back): card for card in self.cards}
        for card in other.cards:
            existing_card = existing_cards.get((card.front, card.back), None)
            if existing_card is not None:
                existing_card.enabled = existing_card.enabled or card.enabled
                existing_card.front_answer_history += card.front_answer_history
                existing_card.back_answer_history += card.back_answer_history
            else:
                self.cards.set(card)
                existing_card = card
            existing_cards[(card.front, card.back)] = existing_card

    def get_card_to_study(self, *, history_length: int, seed: int | None = None) -> tuple[Card, CardSide]:
        """Get the card and side that should be studied next (based on the answer history)."""
        candidates: list[tuple[Card, CardSide]] = []
        minimum_relevant_history_length = None
        minimum_score = None
        for card in self.cards:
            if not card.enabled:
                continue
            for side in CardSide:
                append = False
                answer_history = card.front_answer_history if side is CardSide.FRONT else card.back_answer_history
                relevant_answer_history = answer_history[-history_length:]
                score = sum(relevant_answer_history)
                if (
                    minimum_relevant_history_length is None
                    or len(relevant_answer_history) < minimum_relevant_history_length
                ):
                    minimum_relevant_history_length = len(relevant_answer_history)
                    minimum_score = score
                    candidates.clear()
                    append = True
                elif len(relevant_answer_history) == minimum_relevant_history_length:
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


class Configuration(AbstractStoredModel):
    """Configuration for the application."""

    deck_metadata: UUIDModelList[DeckMetadata] = UUIDModelList()
    """List of metadata for all decks."""
    history_length: NonNegativeInt = 5
    """Number of recent answers to consider when selecting the next card to learn."""
    typewriter_mode: bool = False
    """Whether to enable typewriter mode (requiring full text input for answers)."""

    @staticmethod
    @override
    def get_storage_key(uuid: UUID | None) -> str:
        return "configuration"

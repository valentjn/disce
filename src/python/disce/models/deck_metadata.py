#!/usr/bin/env python
# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Data model for deck metadata."""

from pydantic import BaseModel

from disce.models.base import UUIDModel
from disce.models.cards import AnswerCounts, CardSide


class BaseDeckMetadata(BaseModel):
    """Metadata for an exported deck of flashcards."""

    name: str = "New Deck"
    """Name of the deck."""


class DeckMetadata(UUIDModel, BaseDeckMetadata):
    """Metadata for a deck of flashcards."""

    number_of_cards: int = 0
    """Number of cards in the deck."""
    answer_counts: dict[int, AnswerCounts] = {}
    """Counts of answers per history length, across all cards in the deck."""

    def get_answer_counts(self, history_length: int) -> AnswerCounts:
        """Get the answer counts for the given history length."""
        if history_length == 0 or not self.answer_counts:
            return AnswerCounts()
        maximum_history_length = max(self.answer_counts.keys())
        if history_length <= maximum_history_length:
            return self.answer_counts[history_length]
        maximum_answer_counts = self.answer_counts[maximum_history_length]
        return maximum_answer_counts.model_copy(
            update={
                "missing": maximum_answer_counts.missing
                + (history_length - maximum_history_length) * self.number_of_cards * len(CardSide),
            }
        )

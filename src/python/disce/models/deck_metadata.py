#!/usr/bin/env python
# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Data model for deck metadata."""

from pydantic import BaseModel, ConfigDict

from disce.models.base import UUIDModel
from disce.models.cards import AnswerCounts


class BaseDeckMetadata(BaseModel):
    """Metadata for an exported deck of flashcards."""

    name: str = "New Deck"
    """Name of the deck."""


class DeckMetadata(UUIDModel, BaseDeckMetadata):
    """Metadata for a deck of flashcards."""

    model_config = ConfigDict(extra="ignore")

    number_of_cards: int = 0
    """Number of cards in the deck."""
    answer_counts_v2: AnswerCounts = AnswerCounts()
    """Counts of answers across all cards in the deck."""

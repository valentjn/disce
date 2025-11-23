#!/usr/bin/env python
# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Data model for exported decks."""

from pydantic import BaseModel

from disce.models.cards import AnswerCounts
from disce.models.deck_data import DeckData
from disce.models.deck_metadata import BaseDeckMetadata, DeckMetadata


class ExportedDeck(DeckData, BaseDeckMetadata):
    """A deck exported for sharing or backup."""

    @staticmethod
    def from_deck(data: DeckData, metadata: DeckMetadata) -> "ExportedDeck":
        """Create an exported deck from deck data and metadata."""
        return ExportedDeck(uuid=data.uuid, cards=data.cards.model_copy(deep=True), name=metadata.name)

    def to_deck_data(self) -> DeckData:
        """Create deck data from the exported deck."""
        return DeckData(uuid=self.uuid, cards=self.cards.model_copy(deep=True))

    def to_deck_metadata(self) -> "DeckMetadata":
        """Create deck metadata from the exported deck."""
        answer_counts = sum((card.get_answer_counts(None) for card in self.cards), AnswerCounts())
        return DeckMetadata(
            uuid=self.uuid, name=self.name, number_of_cards=len(self.cards), answer_counts_v2=answer_counts
        )


class DeckExport(BaseModel):
    """A collection of exported decks."""

    decks: list[ExportedDeck] = []
    """List of exported decks."""

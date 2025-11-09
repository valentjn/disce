#!/usr/bin/env python
# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Data model for exported decks."""

from pydantic import BaseModel

from disce.models.cards import AnswerCounts, CardSide
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
        answer_counts: dict[int, AnswerCounts] = {}
        if self.cards:
            maximum_history_length = max(
                max(len(card.front_answer_history), len(card.back_answer_history)) for card in self.cards
            )
            current_counts = AnswerCounts()
            for history_length in range(1, maximum_history_length + 1):
                for card in self.cards:
                    for side in CardSide:
                        if len(answer_history := card.get_answer_history(side)) < history_length:
                            current_counts.missing += 1
                        elif answer_history[-history_length]:
                            current_counts.correct += 1
                        else:
                            current_counts.wrong += 1
                answer_counts[history_length] = current_counts.model_copy()
        return DeckMetadata(
            uuid=self.uuid, name=self.name, number_of_cards=len(self.cards), answer_counts=answer_counts
        )


class DeckExport(BaseModel):
    """A collection of exported decks."""

    decks: list[ExportedDeck] = []
    """List of exported decks."""

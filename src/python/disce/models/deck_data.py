#!/usr/bin/env python
# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Data model for deck data."""

import random
from collections.abc import Sequence
from typing import override

from disce.models.base import UUID, AbstractStoredModel, UUIDModel, UUIDModelList
from disce.models.cards import Card, CardSide


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
            merged_deck.merge(deck_data.model_copy(deep=True))
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

    def get_card_to_study(
        self, *, history_length: int, exclude: Sequence[Card] = (), seed: int | None = None
    ) -> tuple[Card, CardSide]:
        """Get the card and side that should be studied next (based on the answer history)."""
        excluded_card_uuids = {card.uuid for card in exclude}
        included_cards = [card for card in self.cards if card.uuid not in excluded_card_uuids]
        candidates = self._get_candidate_cards_to_study(included_cards, history_length)
        if not candidates and exclude:
            candidates = self._get_candidate_cards_to_study(self.cards.root, history_length)
        if not candidates:
            msg = "no enabled cards in deck"
            raise ValueError(msg)
        rng = random.Random(seed)
        return rng.choice(candidates)

    @staticmethod
    def _get_candidate_cards_to_study(cards: Sequence[Card], history_length: int) -> list[tuple[Card, CardSide]]:
        """Get the list of candidate cards to study based on their scores."""
        candidates = []
        minimum_score = None
        for card in cards:
            if not card.enabled:
                continue
            for side in CardSide:
                score = card.get_score(side, history_length)
                if minimum_score is None or score <= minimum_score:
                    if minimum_score is not None and score < minimum_score:
                        candidates.clear()
                    candidates.append((card, side))
                    minimum_score = score
        return candidates

#!/usr/bin/env python
# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from copy import deepcopy

import pytest
from disce.models.base import UUIDModelList
from disce.models.cards import Card, CardSide
from disce.models.deck_data import DeckData


class TestDeckData:
    @staticmethod
    def test_get_storage_key() -> None:
        assert DeckData.get_storage_key("uuid0") == "deck_data_uuid0"

    @staticmethod
    def test_get_storage_key_none_uuid() -> None:
        with pytest.raises(ValueError, match=r"^uuid must be provided$"):
            DeckData.get_storage_key(None)

    @staticmethod
    @pytest.fixture
    def merge_decks() -> tuple[DeckData, DeckData]:
        deck0 = DeckData(cards=UUIDModelList([Card(front="front0", back="back0"), Card(front="front1", back="back1")]))
        deck1 = DeckData(cards=UUIDModelList([Card(front="front1", back="back1"), Card(front="front2", back="back2")]))
        return deck0, deck1

    @staticmethod
    def test_from_merge(merge_decks: tuple[DeckData, DeckData]) -> None:
        old_cards0 = deepcopy(merge_decks[0].cards.root)
        old_cards1 = deepcopy(merge_decks[1].cards.root)
        merged = DeckData.from_merge(merge_decks)
        assert merged.cards.root == [old_cards0[0], old_cards0[1], old_cards1[1]]
        assert merge_decks[0].cards.root == old_cards0
        assert merge_decks[1].cards.root == old_cards1

    @staticmethod
    def test_merge(merge_decks: tuple[DeckData, DeckData]) -> None:
        old_cards0 = deepcopy(merge_decks[0].cards.root)
        old_cards1 = deepcopy(merge_decks[1].cards.root)
        merge_decks[0].merge(merge_decks[1])
        assert merge_decks[0].cards.root == [old_cards0[0], old_cards0[1], old_cards1[1]]
        assert merge_decks[1].cards.root == old_cards1

    @staticmethod
    def test_get_card_to_study_prefer_short_answer_history() -> None:
        deck = DeckData(
            cards=UUIDModelList([Card(uuid="uuid0", front_answer_history=[True], back_answer_history=[False, True])])
        )
        card, side = deck.get_card_to_study(history_length=2)
        assert card.uuid == "uuid0"
        assert side is CardSide.FRONT

    @staticmethod
    def test_get_card_to_study_prefer_low_score() -> None:
        deck = DeckData(
            cards=UUIDModelList(
                [
                    Card(uuid="uuid0", front_answer_history=[True], back_answer_history=[False]),
                    Card(uuid="uuid1", front_answer_history=[True], back_answer_history=[False]),
                ]
            )
        )
        _, side = deck.get_card_to_study(history_length=1)
        assert side is CardSide.BACK

    @staticmethod
    def test_get_card_to_study_skip_disabled() -> None:
        deck = DeckData(
            cards=UUIDModelList(
                [
                    Card(uuid="uuid0", enabled=False, front_answer_history=[False], back_answer_history=[False]),
                    Card(uuid="uuid1", front_answer_history=[True], back_answer_history=[True]),
                ]
            )
        )
        card, _ = deck.get_card_to_study(history_length=1)
        assert card.uuid == "uuid1"

    @staticmethod
    def test_get_card_to_study_no_enabled_cards() -> None:
        deck = DeckData(cards=UUIDModelList([Card(enabled=False)]))
        with pytest.raises(ValueError, match=r"^no enabled cards in deck$"):
            deck.get_card_to_study(history_length=1)

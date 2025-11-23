#!/usr/bin/env python
# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.


import pytest
from disce.models.base import UUIDModelList
from disce.models.cards import AnswerCounts, Card
from disce.models.deck_data import DeckData
from disce.models.deck_metadata import DeckMetadata
from disce.models.exports import ExportedDeck


class TestExportedDeck:
    @staticmethod
    @pytest.fixture
    def exported_deck() -> ExportedDeck:
        return ExportedDeck(
            uuid="uuid1",
            name="name",
            cards=UUIDModelList(
                [
                    Card(uuid="uuid2", front_answer_history=[True, False], back_answer_history=[False]),
                    Card(uuid="uuid3", front_answer_history=[True], back_answer_history=[]),
                ]
            ),
        )

    @staticmethod
    def test_from_deck(exported_deck: ExportedDeck) -> None:
        deck_data = DeckData(uuid="uuid1", cards=exported_deck.cards)
        deck_metadata = DeckMetadata(uuid="uuid1", name="name", number_of_cards=2)
        actual_exported_deck = ExportedDeck.from_deck(deck_data, deck_metadata)
        assert actual_exported_deck == exported_deck

    @staticmethod
    def test_to_deck_data(exported_deck: ExportedDeck) -> None:
        deck_data = exported_deck.to_deck_data()
        assert deck_data == DeckData(uuid="uuid1", cards=exported_deck.cards)

    @staticmethod
    def test_to_deck_metadata(exported_deck: ExportedDeck) -> None:
        deck_metadata = exported_deck.to_deck_metadata()
        assert deck_metadata == DeckMetadata(
            uuid="uuid1", name="name", number_of_cards=2, answer_counts_v2=AnswerCounts(correct=1, wrong=3, missing=16)
        )

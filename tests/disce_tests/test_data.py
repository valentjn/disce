#!/usr/bin/env python
# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from copy import deepcopy
from typing import override

import pytest
from disce.data import AbstractStoredModel, Card, CardSide, Configuration, DeckData, UUIDModel, UUIDModelList

from disce_tests.storage.dict import DictStorage


class DummyStoredModel(AbstractStoredModel, UUIDModel):
    field: str

    @staticmethod
    @override
    def get_storage_key(uuid: str | None) -> str:
        if uuid is None:
            msg = "uuid must be provided"
            raise ValueError(msg)
        return f"dummy-{uuid}"


class TestStoredModel:
    @staticmethod
    @pytest.fixture
    def storage() -> DictStorage:
        storage = DictStorage()
        storage["dummy-uuid0"] = '{"field": "value0"}'
        storage["dummy-uuid1"] = '{"field": "value1"}'
        return storage

    @staticmethod
    def test_get_storage_key() -> None:
        with pytest.raises(NotImplementedError):
            assert AbstractStoredModel.get_storage_key(None)

    @staticmethod
    @pytest.mark.parametrize(("uuid", "expected"), [("uuid0", True), ("uuid2", False)])
    def test_exists_in_storage(storage: DictStorage, uuid: str, *, expected: bool) -> None:
        assert DummyStoredModel.exists_in_storage(storage, uuid) == expected

    @staticmethod
    def test_load_from_storage(storage: DictStorage) -> None:
        model = DummyStoredModel.load_from_storage(storage, "uuid0")
        assert model.field == "value0"

    @staticmethod
    def test_load_from_storage_non_existent_uuid(storage: DictStorage) -> None:
        with pytest.raises(KeyError, match=r"^'dummy-uuid2'$"):
            DummyStoredModel.load_from_storage(storage, "uuid2")

    @staticmethod
    def test_load_from_storage_or_create(storage: DictStorage) -> None:
        model = DummyStoredModel.load_from_storage_or_create(storage, "uuid0")
        assert model.field == "value0"

    @staticmethod
    def test_load_from_storage_or_create_non_existent_uuid(storage: DictStorage) -> None:
        model = DummyStoredModel.load_from_storage_or_create(
            storage, "uuid2", default=DummyStoredModel(field="default")
        )
        assert model.field == "default"

    @staticmethod
    def test_save_to_storage(storage: DictStorage) -> None:
        model = DummyStoredModel(uuid="uuid2", field="value2")
        model.save_to_storage(storage)
        assert DummyStoredModel.load_from_storage(storage, "uuid2") == model

    @staticmethod
    def test_delete_from_storage(storage: DictStorage) -> None:
        DummyStoredModel.delete_from_storage(storage, "uuid1")
        assert not DummyStoredModel.exists_in_storage(storage, "uuid1")


class TestUUIDModel:
    @staticmethod
    def test_generate_uuid() -> None:
        assert UUIDModel.generate_uuid() != UUIDModel.generate_uuid()


class TestUUIDModelList:
    @pytest.fixture
    def cards(self) -> UUIDModelList[Card]:
        return UUIDModelList([Card(uuid="uuid0"), Card(uuid="uuid1")])

    @staticmethod
    def test_iter(cards: UUIDModelList[Card]) -> None:
        assert [card.uuid for card in cards] == ["uuid0", "uuid1"]

    @staticmethod
    def test_len(cards: UUIDModelList[Card]) -> None:
        assert len(cards) == 2

    @staticmethod
    @pytest.mark.parametrize(("card", "expected"), [(Card(uuid="uuid0"), True), (Card(uuid="uuid2"), False)])
    def test_contains(cards: UUIDModelList[Card], card: Card, *, expected: bool) -> None:
        assert (card.uuid in cards) == expected

    @staticmethod
    def test_getitem(cards: UUIDModelList[Card]) -> None:
        card = cards["uuid0"]
        assert card.uuid == "uuid0"

    @staticmethod
    def test_getitem_non_existent_key(cards: UUIDModelList[Card]) -> None:
        with pytest.raises(KeyError, match=r"^'uuid2'$"):
            cards["uuid2"]

    @staticmethod
    @pytest.mark.parametrize("uuid", ["uuid1", "uuid2"])
    def test_set(cards: UUIDModelList[Card], uuid: str) -> None:
        card = Card(uuid=uuid, front="front")
        cards.set(card)
        assert cards[card.uuid] == card

    @staticmethod
    def test_delitem(cards: UUIDModelList[Card]) -> None:
        del cards["uuid0"]
        assert "uuid0" not in cards

    @staticmethod
    def test_delitem_non_existent_key(cards: UUIDModelList[Card]) -> None:
        with pytest.raises(KeyError, match=r"^'uuid2'$"):
            del cards["uuid2"]


class TestCard:
    @staticmethod
    def test_get_side() -> None:
        card = Card(front="front", back="back")
        assert card.get_side(CardSide.FRONT) == "front"
        assert card.get_side(CardSide.BACK) == "back"

    @staticmethod
    def test_get_opposite_side() -> None:
        card = Card(front="front", back="back")
        assert card.get_opposite_side(CardSide.FRONT) == "back"
        assert card.get_opposite_side(CardSide.BACK) == "front"

    @staticmethod
    def test_record_answer() -> None:
        card = Card(front="front", back="back")
        card.record_answer(CardSide.FRONT, correct=True)
        card.record_answer(CardSide.FRONT, correct=False)
        card.record_answer(CardSide.BACK, correct=False)
        card.record_answer(CardSide.BACK, correct=True)
        assert card.front_answer_history == [True, False]
        assert card.back_answer_history == [False, True]


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


class TestConfiguration:
    @staticmethod
    def test_get_storage_key() -> None:
        assert Configuration.get_storage_key(None) == "configuration"

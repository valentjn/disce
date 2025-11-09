#!/usr/bin/env python
# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from typing import override

import pytest
from disce.models.base import AbstractStoredModel, UUIDModel, UUIDModelList
from disce.models.cards import Card

from disce_tests.unit.storage.dict import DictStorage


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
    def test_load_from_storage_nonexistent_uuid(storage: DictStorage) -> None:
        with pytest.raises(KeyError, match=r"^'dummy-uuid2'$"):
            DummyStoredModel.load_from_storage(storage, "uuid2")

    @staticmethod
    def test_load_from_storage_or_create(storage: DictStorage) -> None:
        model = DummyStoredModel.load_from_storage_or_create(storage, "uuid0")
        assert model.field == "value0"

    @staticmethod
    def test_load_from_storage_or_create_nonexistent_uuid(storage: DictStorage) -> None:
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
    def test_getitem_nonexistent_key(cards: UUIDModelList[Card]) -> None:
        with pytest.raises(KeyError, match=r"^'uuid2'$"):
            cards["uuid2"]

    @staticmethod
    def test_get(cards: UUIDModelList[Card]) -> None:
        card = cards.get("uuid0")
        assert card is not None
        assert card.uuid == "uuid0"

    @staticmethod
    def test_get_nonexistent_key(cards: UUIDModelList[Card]) -> None:
        assert cards.get("uuid2") is None

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
    def test_delitem_nonexistent_key(cards: UUIDModelList[Card]) -> None:
        with pytest.raises(KeyError, match=r"^'uuid2'$"):
            del cards["uuid2"]

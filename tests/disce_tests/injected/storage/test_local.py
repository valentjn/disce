#!/usr/bin/env python
# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from collections.abc import Generator

import pytest
from disce.storage.local import LocalStorage


class TestLocalStorage:
    @staticmethod
    @pytest.fixture
    def storage() -> Generator[LocalStorage]:
        local_storage = LocalStorage()
        yield local_storage
        local_storage.clear()

    @staticmethod
    def test_len(storage: LocalStorage) -> None:
        storage["key1"] = "value1"
        storage["key2"] = "value2"
        assert len(storage) == 2

    @staticmethod
    def test_iter(storage: LocalStorage) -> None:
        storage["key1"] = "value1"
        storage["key2"] = "value2"
        assert set(storage) == {"key1", "key2"}

    @staticmethod
    def test_getitem_setitem(storage: LocalStorage) -> None:
        storage["key"] = "value"
        assert storage["key"] == "value"

    @staticmethod
    def test_getitem_key_error(storage: LocalStorage) -> None:
        with pytest.raises(KeyError, match=r"^'key'$"):
            storage["key"]

    @staticmethod
    def test_delitem(storage: LocalStorage) -> None:
        storage["key"] = "value"
        del storage["key"]
        assert "key" not in storage
        del storage["key"]
        assert "key" not in storage

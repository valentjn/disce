#!/usr/bin/env python
# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.


import pytest


class TestLocalStorage:
    @staticmethod
    def test_len(storage: AbstractStorage) -> None:
        storage["key1"] = "value1"
        storage["key2"] = "value2"
        assert len(storage) == 2

    @staticmethod
    def test_iter(storage: AbstractStorage) -> None:
        storage["key1"] = "value1"
        storage["key2"] = "value2"
        assert set(storage) == {"key1", "key2"}

    @staticmethod
    def test_getitem_setitem(storage: AbstractStorage) -> None:
        storage["key"] = "value"
        assert storage["key"] == "value"

    @staticmethod
    def test_getitem_key_error(storage: AbstractStorage) -> None:
        with pytest.raises(KeyError, match=r"^'key'$"):
            storage["key"]

    @staticmethod
    def test_delitem(storage: AbstractStorage) -> None:
        storage["key"] = "value"
        del storage["key"]
        assert "key" not in storage
        del storage["key"]
        assert "key" not in storage

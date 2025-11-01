#!/usr/bin/env python
# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from collections.abc import Generator
from contextlib import contextmanager

import pytest
from disce.storage.base import AbstractStorage


@contextmanager
def clear_storage[T: AbstractStorage](storage: T) -> Generator[T]:
    try:
        yield storage
    finally:
        storage.clear()


class BaseTestStorage:
    @staticmethod
    def test_len(test_storage: AbstractStorage) -> None:
        test_storage["key1"] = "value1"
        test_storage["key2"] = "value2"
        assert len(test_storage) == 2

    @staticmethod
    def test_iter(test_storage: AbstractStorage) -> None:
        test_storage["key1"] = "value1"
        test_storage["key2"] = "value2"
        assert set(test_storage) == {"key1", "key2"}

    @staticmethod
    def test_getitem_setitem(test_storage: AbstractStorage) -> None:
        test_storage["key"] = "value"
        assert test_storage["key"] == "value"

    @staticmethod
    def test_getitem_key_error(test_storage: AbstractStorage) -> None:
        with pytest.raises(KeyError, match=r"^'key'$"):
            test_storage["key"]

    @staticmethod
    def test_delitem(test_storage: AbstractStorage) -> None:
        test_storage["key"] = "value"
        del test_storage["key"]
        assert "key" not in test_storage
        del test_storage["key"]
        assert "key" not in test_storage

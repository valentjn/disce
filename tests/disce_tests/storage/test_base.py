#!/usr/bin/env python
# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import pytest
from disce.storage.base import AbstractStorage

from disce_tests.storage.dict import DictStorage


class TestAbstractStorage:
    @staticmethod
    @pytest.fixture
    def storage() -> DictStorage:
        return DictStorage()

    @staticmethod
    def test_has(storage: DictStorage) -> None:
        with pytest.raises(NotImplementedError):
            AbstractStorage.has(storage, "key")

    @staticmethod
    def test_load(storage: DictStorage) -> None:
        with pytest.raises(NotImplementedError):
            AbstractStorage.load(storage, "key")

    @staticmethod
    def test_save(storage: DictStorage) -> None:
        with pytest.raises(NotImplementedError):
            AbstractStorage.save(storage, "key", "value")

    @staticmethod
    def test_delete(storage: DictStorage) -> None:
        with pytest.raises(NotImplementedError):
            AbstractStorage.delete(storage, "key")

#!/usr/bin/env python
# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import pytest
from disce.storage.base import AbstractStorage

from disce_tests.unit.storage.dict import DictStorage


class TestAbstractStorage:
    @staticmethod
    @pytest.fixture
    def storage() -> DictStorage:
        return DictStorage()

    @staticmethod
    def test_iter(storage: DictStorage) -> None:
        with pytest.raises(NotImplementedError):
            AbstractStorage.__iter__(storage)

    @staticmethod
    def test_getitem(storage: DictStorage) -> None:
        with pytest.raises(NotImplementedError):
            AbstractStorage.__getitem__(storage, "key")

    @staticmethod
    def test_setitem(storage: DictStorage) -> None:
        with pytest.raises(NotImplementedError):
            AbstractStorage.__setitem__(storage, "key", "value")

    @staticmethod
    def test_delitem(storage: DictStorage) -> None:
        with pytest.raises(NotImplementedError):
            AbstractStorage.__delitem__(storage, "key")

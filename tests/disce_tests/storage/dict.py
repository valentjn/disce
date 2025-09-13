#!/usr/bin/env python
# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from disce.storage.base import AbstractStorage


class DictStorage(AbstractStorage):
    def __init__(self) -> None:
        self._data: dict[str, str] = {}

    def has(self, key: str) -> bool:
        return key in self._data

    def load(self, key: str) -> str:
        return self._data[key]

    def save(self, key: str, value: str) -> None:
        self._data[key] = value

    def delete(self, key: str) -> None:
        self._data.pop(key, None)

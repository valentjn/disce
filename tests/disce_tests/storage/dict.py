#!/usr/bin/env python
# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from collections.abc import Iterator

from disce.storage.base import AbstractStorage


class DictStorage(AbstractStorage):
    def __init__(self) -> None:
        self._data: dict[str, str] = {}

    def __iter__(self) -> Iterator[str]:
        return iter(self._data)

    def __getitem__(self, key: str) -> str:
        return self._data[key]

    def __setitem__(self, key: str, value: str) -> None:
        self._data[key] = value

    def __delitem__(self, key: str) -> None:
        self._data.pop(key, None)

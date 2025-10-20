#!/usr/bin/env python
# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Storage classes."""

from typing import cast, override

from pyscript import window

from disce.storage.base import AbstractStorage


class LocalStorage(AbstractStorage):
    """Local storage implementation using browser's localStorage."""

    @override
    def __contains__(self, key: str) -> bool:
        return any(window.localStorage.key(index) == key for index in range(window.localStorage.length))

    @override
    def __getitem__(self, key: str) -> str:
        value = cast("str", window.localStorage.getItem(key))
        if value is None:
            raise KeyError(key)
        return value

    @override
    def __setitem__(self, key: str, value: str) -> None:
        window.navigator.storage.persist()
        window.localStorage.setItem(key, value)

    @override
    def __delitem__(self, key: str) -> None:
        window.localStorage.removeItem(key)

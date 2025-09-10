#!/usr/bin/env python
# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Storage classes."""

from abc import ABC, abstractmethod
from typing import cast, override

from pyscript import window


class AbstractStorage(ABC):
    """Abstract storage interface for storing strings."""

    @abstractmethod
    def has(self, key: str) -> bool:
        """Check if a key exists in storage."""
        raise NotImplementedError

    @abstractmethod
    def load(self, key: str) -> str:
        """Load a value from storage."""
        raise NotImplementedError

    @abstractmethod
    def save(self, key: str, value: str) -> None:
        """Save a value to storage."""
        raise NotImplementedError

    @abstractmethod
    def delete(self, key: str) -> None:
        """Delete a value from storage."""
        raise NotImplementedError


class LocalStorage(AbstractStorage):
    """Local storage implementation using browser's localStorage."""

    @override
    def has(self, key: str) -> bool:
        return any(window.localStorage.key(index) == key for index in range(window.localStorage.length))

    @override
    def load(self, key: str) -> str:
        value = cast("str", window.localStorage.getItem(key))
        if value is None:
            raise KeyError(key)
        return value

    @override
    def save(self, key: str, value: str) -> None:
        window.navigator.storage.persist()
        window.localStorage.setItem(key, value)

    @override
    def delete(self, key: str) -> None:
        window.localStorage.removeItem(key)

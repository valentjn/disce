#!/usr/bin/env python
# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Base storage classes."""

from abc import ABC, abstractmethod
from collections.abc import Iterator


class AbstractStorage(ABC):
    """Abstract storage interface for storing strings."""

    @abstractmethod
    def __iter__(self) -> Iterator[str]:
        """Get an iterator over all keys in storage."""
        raise NotImplementedError

    @abstractmethod
    def __getitem__(self, key: str) -> str:
        """Load a value from storage."""
        raise NotImplementedError

    @abstractmethod
    def __setitem__(self, key: str, value: str) -> None:
        """Save a value to storage."""
        raise NotImplementedError

    @abstractmethod
    def __delitem__(self, key: str) -> None:
        """Delete a value from storage if it exists (no error if it does not)."""
        raise NotImplementedError

    def __len__(self) -> int:
        """Get the number of items in storage."""
        return sum(1 for _ in self)

    def clear(self) -> None:
        """Clear all items from storage."""
        for key in list(self):
            del self[key]

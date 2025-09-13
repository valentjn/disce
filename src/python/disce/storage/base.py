#!/usr/bin/env python
# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Base storage classes."""

from abc import ABC, abstractmethod


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

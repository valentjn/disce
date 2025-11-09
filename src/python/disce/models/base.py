#!/usr/bin/env python
# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Base data models."""

from abc import ABC, abstractmethod
from collections.abc import Iterator
from typing import Self, overload, override
from uuid import uuid4

from pydantic import BaseModel, Field, RootModel

from disce.storage.base import AbstractStorage
from disce.tools import log_time

type UUID = str


class AbstractStoredModel(BaseModel, ABC):
    """Base model for data that can be stored in a storage backend."""

    @staticmethod
    @abstractmethod
    def get_storage_key(uuid: UUID | None) -> str:
        """Get the key to use for storage."""
        raise NotImplementedError

    @classmethod
    def exists_in_storage(cls, storage: AbstractStorage, uuid: UUID | None = None) -> bool:
        """Check if data exists in storage."""
        storage_key = cls.get_storage_key(uuid)
        return storage_key in storage

    @classmethod
    def load_from_storage(cls, storage: AbstractStorage, uuid: UUID | None = None) -> Self:
        """Load saved data from storage."""
        storage_key = cls.get_storage_key(uuid)
        if not cls.exists_in_storage(storage, uuid):
            raise KeyError(storage_key)
        with log_time("loaded data from storage"):
            json = storage[storage_key]
        with log_time("parsed data"):
            return cls.model_validate_json(json)

    @classmethod
    def load_from_storage_or_create(
        cls, storage: AbstractStorage, uuid: UUID | None = None, default: Self | None = None
    ) -> Self:
        """Load saved data from storage or create a new instance."""
        try:
            return cls.load_from_storage(storage, uuid)
        except KeyError:
            return cls() if default is None else default

    def save_to_storage(self, storage: AbstractStorage) -> None:
        """Save data to storage."""
        with log_time("serialized data"):
            json = self.model_dump_json()
        with log_time("saved data to storage"):
            storage[self.get_storage_key(getattr(self, "uuid", None))] = json

    @classmethod
    def delete_from_storage(cls, storage: AbstractStorage, uuid: UUID | None = None) -> None:
        """Delete data from storage."""
        with log_time("deleted data from storage"):
            del storage[cls.get_storage_key(uuid)]


class UUIDModel(BaseModel):
    """Base model with a UUID."""

    @staticmethod
    def generate_uuid() -> UUID:
        """Generate a new UUID."""
        return str(uuid4())

    uuid: UUID = Field(default_factory=generate_uuid)
    """Unique identifier."""


class UUIDModelList[T: UUIDModel](RootModel[list[T]]):
    """Base model for a list of UUID models."""

    root: list[T] = []
    """List of UUID models."""

    @override
    def __iter__(self) -> Iterator[T]:  # type: ignore[override]
        """Iterate over the items in the list."""
        return iter(self.root)

    def __len__(self) -> int:
        """Get the number of items in the list."""
        return len(self.root)

    def __contains__(self, uuid: UUID) -> bool:
        """Check if an item with the given UUID exists in the list."""
        try:
            self._get_index(uuid)
        except KeyError:
            return False
        return True

    def __getitem__(self, uuid: UUID) -> T:
        """Get an item by its UUID."""
        return self.root[self._get_index(uuid)]

    @overload
    def get(self, uuid: UUID, default: T) -> T: ...

    @overload
    def get(self, uuid: UUID, default: None = None) -> T | None: ...

    def get(self, uuid: UUID, default: T | None = None) -> T | None:
        """Get an item by its UUID, or return a default value if not found."""
        try:
            return self[uuid]
        except KeyError:
            return default

    def set(self, value: T) -> None:
        """Set an item by its UUID (add if it doesn't exist)."""
        try:
            index = self._get_index(value.uuid)
        except KeyError:
            self.root.append(value)
        else:
            self.root[index] = value

    def __delitem__(self, uuid: UUID) -> None:
        """Delete an item by its UUID."""
        del self.root[self._get_index(uuid)]

    def _get_index(self, uuid: UUID) -> int:
        """Get the index of item by its UUID."""
        index = next((index for index, item in enumerate(self.root) if item.uuid == uuid), None)
        if index is None:
            raise KeyError(uuid)
        return index

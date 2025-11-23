#!/usr/bin/env python
# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Data model for the application configuration."""

from typing import override

from pydantic import ConfigDict

from disce.models.base import UUID, AbstractStoredModel, UUIDModelList
from disce.models.deck_metadata import DeckMetadata


class Configuration(AbstractStoredModel):
    """Configuration for the application."""

    model_config = ConfigDict(extra="ignore")

    deck_metadata: UUIDModelList[DeckMetadata] = UUIDModelList()
    """List of metadata for all decks."""
    typewriter_mode: bool = False
    """Whether to enable typewriter mode (requiring full text input for answers)."""

    @staticmethod
    @override
    def get_storage_key(uuid: UUID | None) -> str:
        return "configuration"

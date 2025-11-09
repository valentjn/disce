#!/usr/bin/env python
# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Data model for the application configuration."""

from typing import override

from pydantic import NonNegativeInt

from disce.models.base import UUID, AbstractStoredModel, UUIDModelList
from disce.models.deck_metadata import DeckMetadata


class Configuration(AbstractStoredModel):
    """Configuration for the application."""

    deck_metadata: UUIDModelList[DeckMetadata] = UUIDModelList()
    """List of metadata for all decks."""
    history_length: NonNegativeInt = 3
    """Number of recent answers to consider when selecting the next card to learn."""
    typewriter_mode: bool = False
    """Whether to enable typewriter mode (requiring full text input for answers)."""

    @staticmethod
    @override
    def get_storage_key(uuid: UUID | None) -> str:
        return "configuration"

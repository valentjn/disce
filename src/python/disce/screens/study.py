#!/usr/bin/env python
# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Screen for studying a deck."""

from typing import override

from disce.data import Configuration, DeckData
from disce.screens.base import AbstractScreen, EventBinding
from disce.storage.base import AbstractStorage


class StudyScreen(AbstractScreen):
    """Screen for studying a deck."""

    def __init__(self, deck_uuids: list[str], storage: AbstractStorage) -> None:
        """Initialize the screen."""
        super().__init__("#disce-study-screen")
        self._deck_uuids = deck_uuids
        self._storage = storage
        self._configuration = Configuration.load_from_storage_or_create(self._storage)
        self._deck_data_list = [DeckData.load_from_storage(self._storage, uuid) for uuid in deck_uuids]
        self._merged_deck_data = DeckData.from_merge(self._deck_data_list)
        self._card_uuid_to_deck_uuid = {
            card.uuid: deck_data.uuid for deck_data in self._deck_data_list for card in deck_data.cards
        }

    @override
    def _get_static_event_listeners(self) -> list[EventBinding]:
        return []

    @override
    def render(self) -> None:
        pass

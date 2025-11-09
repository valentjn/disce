#!/usr/bin/env python
# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import pytest
from disce.models.base import UUIDModelList
from disce.models.configs import Configuration
from disce.models.deck_data import DeckData
from disce.models.deck_metadata import DeckMetadata
from disce.screens.decks import DecksScreen
from disce.screens.edit_deck import EditDeckScreen
from disce.screens.load import LoadScreen
from disce.screens.study import StudyScreen
from disce.storage.base import AbstractStorage

from disce_tests.injected.screens.tools import create_decks


@pytest.fixture
def deck_data_list() -> list[DeckData]:
    deck_data_list, _ = create_decks("")
    return deck_data_list.root


@pytest.fixture
def deck_metadata_list() -> list[DeckMetadata]:
    _, deck_metadata_list = create_decks("")
    return deck_metadata_list.root


@pytest.fixture(autouse=True)
def save_decks_and_configuration(
    storage: AbstractStorage, deck_data_list: list[DeckData], deck_metadata_list: list[DeckMetadata]
) -> None:
    for deck_data in deck_data_list:
        deck_data.save_to_storage(storage)
    configuration = Configuration(deck_metadata=UUIDModelList(deck_metadata_list), history_length=10)
    configuration.save_to_storage(storage)


@pytest.fixture(autouse=True)
def hide_all_screens(storage: AbstractStorage, save_decks_and_configuration: None) -> None:
    DecksScreen(storage).hide()
    EditDeckScreen(None, storage).hide()
    LoadScreen().hide()
    StudyScreen(["deck1"], storage).hide()

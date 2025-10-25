#!/usr/bin/env python
# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from collections.abc import Generator

import pytest
from disce.data import Configuration, DeckData, DeckMetadata, UUIDModelList
from disce.storage.local import LocalStorage

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
def decks_and_configuration(deck_data_list: list[DeckData], deck_metadata_list: list[DeckMetadata]) -> Generator[None]:
    local_storage = LocalStorage()
    for deck_data in deck_data_list:
        deck_data.save_to_storage(local_storage)
    configuration = Configuration(deck_metadata=UUIDModelList(deck_metadata_list), history_length=2)
    configuration.save_to_storage(local_storage)
    yield
    local_storage.clear()

#!/usr/bin/env python
# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from collections.abc import Generator

import pytest
from disce.data import Configuration
from disce.storage.local import LocalStorage

from disce_tests.injected.screens.tools import create_decks


@pytest.fixture(autouse=True)
def decks_and_configuration() -> Generator[None]:
    local_storage = LocalStorage()
    deck_data_list, deck_metadata_list = create_decks("")
    for deck_data in deck_data_list:
        deck_data.save_to_storage(local_storage)
    configuration = Configuration(deck_metadata=deck_metadata_list, history_length=2)
    configuration.save_to_storage(local_storage)
    yield
    local_storage.clear()

#!/usr/bin/env python
# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from collections.abc import Generator

import pytest
from disce.data import Card, Configuration, DeckData, DeckMetadata, UUIDModelList
from disce.storage.local import LocalStorage


@pytest.fixture(autouse=True)
def decks_and_configuration() -> Generator[None]:
    local_storage = LocalStorage()
    DeckData(
        uuid="deck1",
        cards=UUIDModelList(
            [
                Card(uuid="deck1_card1", front="deck1_card1_front", back="deck1_card1_back"),
                Card(uuid="deck1_card2", front="deck1_card2_front", back="deck1_card2_back"),
            ]
        ),
    ).save_to_storage(local_storage)
    DeckData(
        uuid="deck2",
        cards=UUIDModelList([Card(uuid="deck2_card1", front="deck2_card1_front", back="deck2_card1_back")]),
    ).save_to_storage(local_storage)
    configuration = Configuration(
        deck_metadata=UUIDModelList(
            [
                DeckMetadata(uuid="deck1", name="Test Deck 1", number_of_cards=2),
                DeckMetadata(uuid="deck2", name="Test Deck 2", number_of_cards=1),
            ]
        ),
        history_length=2,
    )
    configuration.save_to_storage(local_storage)
    yield
    local_storage.clear()

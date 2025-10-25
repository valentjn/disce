#!/usr/bin/env python
# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.


from collections.abc import Sequence

from disce.data import Card, Configuration, DeckData, DeckMetadata, UUIDModel, UUIDModelList
from disce.storage.local import LocalStorage


def create_decks(prefix: str) -> tuple[UUIDModelList[DeckData], UUIDModelList[DeckMetadata]]:
    prefix = prefix.rstrip("_")
    if prefix:
        prefix += "_"
    return UUIDModelList(
        [
            DeckData(
                uuid=f"{prefix}deck1",
                cards=UUIDModelList(
                    [
                        Card(uuid=f"{prefix}deck1_card1", front="deck1_card1_front", back="deck1_card1_back"),
                        Card(uuid=f"{prefix}deck1_card2", front="deck1_card2_front", back="deck1_card2_back"),
                    ]
                ),
            ),
            DeckData(
                uuid=f"{prefix}deck2",
                cards=UUIDModelList(
                    [Card(uuid=f"{prefix}deck2_card1", front="deck2_card1_front", back="deck2_card1_back")]
                ),
            ),
        ]
    ), UUIDModelList(
        [
            DeckMetadata(uuid=f"{prefix}deck1", name=f"{prefix}deck1_name", number_of_cards=2),
            DeckMetadata(uuid=f"{prefix}deck2", name=f"{prefix}deck2_name", number_of_cards=1),
        ]
    )


def assert_decks(expected_deck_data: Sequence[DeckData], expected_deck_metadata: Sequence[DeckMetadata]) -> None:
    local_storage = LocalStorage()
    configuration = Configuration.load_from_storage(local_storage)
    assert_same_elements(configuration.deck_metadata, expected_deck_metadata)
    actual_deck_data = [
        DeckData.load_from_storage(local_storage, deck_metadata.uuid) for deck_metadata in expected_deck_metadata
    ]
    assert_same_elements(actual_deck_data, expected_deck_data)


def assert_same_elements[T: UUIDModel](
    actual: Sequence[T] | UUIDModelList[T], expected: Sequence[T] | UUIDModelList[T]
) -> None:
    if isinstance(actual, UUIDModelList):
        actual = actual.root
    if isinstance(expected, UUIDModelList):
        expected = expected.root
    assert len(actual) == len(expected)
    indices = set(range(len(expected)))
    for actual_element in actual:
        for idx in indices:
            if actual_element == expected[idx]:
                indices.remove(idx)
                break
        else:
            msg = f"actual element {actual_element} not found in expected collection {expected}"
            raise AssertionError(msg)

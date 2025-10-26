#!/usr/bin/env python
# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.


from collections.abc import Sequence
from types import MethodType

from disce.data import Card, Configuration, DeckData, DeckMetadata, UUIDModel, UUIDModelList
from disce.pyscript import Event, EventBinding
from disce.screens.base import AbstractScreen
from disce.storage.local import LocalStorage
from pyscript import window


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
    actual_without_expected = _set_difference(actual, expected)
    expected_without_actual = _set_difference(expected, actual)
    if actual_without_expected or expected_without_actual:
        msg = "actual and expected collections differ:"
        if actual_without_expected:
            msg += f"\n    actual contains unexpected elements: {actual_without_expected}"
        if expected_without_actual:
            msg += f"\n    actual is missing expected elements: {expected_without_actual}"
        raise AssertionError(msg)


def _set_difference[T](sequence1: Sequence[T], sequence2: Sequence[T]) -> list[T]:
    unmatched_indices2 = set(range(len(sequence2)))
    difference = []
    for item1 in sequence1:
        for idx2 in unmatched_indices2:
            if item1 == sequence2[idx2]:
                unmatched_indices2.remove(idx2)
                break
        else:
            difference.append(item1)
    return difference


def assert_event_bindings_registered(bindings: Sequence[EventBinding]) -> None:
    for binding in bindings:
        if not isinstance(binding.listener, MethodType):
            msg = "listener must be an instance method"
            raise TypeError(msg)
        listener_self, listener_func = binding.listener.__self__, binding.listener.__func__
        original_code = binding.listener.__code__
        listener_func.__code__ = _dummy_event_listener.__code__
        listener_self.dummy_event_listener_called = False  # type: ignore[attr-defined]
        try:
            binding.element.dispatchEvent(window.Event.new(binding.event_name))
            assert listener_self.dummy_event_listener_called  # type: ignore[attr-defined]
        finally:
            del listener_self.dummy_event_listener_called  # type: ignore[attr-defined]
            listener_func.__code__ = original_code


def _dummy_event_listener(self: AbstractScreen, _event: Event | None = None) -> None:
    self.dummy_event_listener_called = True  # type: ignore[attr-defined]

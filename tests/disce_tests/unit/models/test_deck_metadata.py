#!/usr/bin/env python
# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.


import pytest
from disce.models.cards import AnswerCounts
from disce.models.deck_metadata import DeckMetadata


class TestDeckMetadata:
    @staticmethod
    @pytest.fixture
    def deck_metadata() -> DeckMetadata:
        return DeckMetadata(
            number_of_cards=2,
            answer_counts={
                1: AnswerCounts(correct=1, wrong=2, missing=1),
                2: AnswerCounts(correct=2, wrong=2, missing=4),
            },
        )

    @staticmethod
    @pytest.mark.parametrize(
        ("history_length", "expected"),
        [
            (0, AnswerCounts()),
            (1, AnswerCounts(correct=1, wrong=2, missing=1)),
            (2, AnswerCounts(correct=2, wrong=2, missing=4)),
            (3, AnswerCounts(correct=2, wrong=2, missing=8)),
        ],
    )
    def test_get_answer_counts(deck_metadata: DeckMetadata, history_length: int, expected: AnswerCounts) -> None:
        assert deck_metadata.get_answer_counts(history_length) == expected

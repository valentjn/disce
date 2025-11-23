#!/usr/bin/env python
# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.


import pytest
from disce.models.cards import AnswerCounts, Card, CardSide


class TestCardSide:
    @staticmethod
    def test_opposite() -> None:
        assert CardSide.FRONT.opposite is CardSide.BACK
        assert CardSide.BACK.opposite is CardSide.FRONT


class TestAnswerCounts:
    @staticmethod
    def test_total() -> None:
        answer_counts = AnswerCounts(correct=3, wrong=2, missing=1)
        assert answer_counts.total == 6

    @staticmethod
    @pytest.mark.parametrize(
        ("answer_counts", "expected"),
        [
            (AnswerCounts(correct=3, wrong=2, missing=1), "50% correct, 33% wrong, 17% missing answers"),
            (AnswerCounts(correct=1, wrong=1, missing=1), "33% correct, 33% wrong, 34% missing answers"),
            (AnswerCounts(correct=0, wrong=0, missing=0), "0% correct, 0% wrong, 100% missing answers"),
        ],
    )
    def test_str(answer_counts: AnswerCounts, expected: str) -> None:
        assert str(answer_counts) == expected

    @staticmethod
    @pytest.mark.parametrize(
        ("answer_counts", "expected"),
        [
            (
                AnswerCounts(correct=3, wrong=2, missing=1),
                "linear-gradient(to right, rgba(var(--bs-success-rgb), 0.4) 0% 50.000%, "
                "rgba(var(--bs-danger-rgb), 0.4) 50.000% 83.333%, rgba(var(--bs-secondary-rgb), 0.4) 83.333% 100%)",
            ),
            (
                AnswerCounts(correct=1, wrong=1, missing=1),
                "linear-gradient(to right, rgba(var(--bs-success-rgb), 0.4) 0% 33.333%, "
                "rgba(var(--bs-danger-rgb), 0.4) 33.333% 66.667%, rgba(var(--bs-secondary-rgb), 0.4) 66.667% 100%)",
            ),
            (
                AnswerCounts(correct=0, wrong=0, missing=0),
                "linear-gradient(to right, rgba(var(--bs-success-rgb), 0.4) 0% 0.000%, "
                "rgba(var(--bs-danger-rgb), 0.4) 0.000% 0.000%, rgba(var(--bs-secondary-rgb), 0.4) 0.000% 100%)",
            ),
        ],
    )
    def test_gradient(answer_counts: AnswerCounts, expected: str) -> None:
        assert answer_counts.gradient == expected


class TestCard:
    @staticmethod
    @pytest.fixture
    def card() -> Card:
        return Card(front="front", back="back", front_answer_history=[True, False], back_answer_history=[False])

    @staticmethod
    def test_get_side(card: Card) -> None:
        assert card.get_side(CardSide.FRONT) == "front"
        assert card.get_side(CardSide.BACK) == "back"

    @staticmethod
    def test_get_answer_history(card: Card) -> None:
        assert card.get_answer_history(CardSide.FRONT) == [True, False]
        assert card.get_answer_history(CardSide.BACK) == [False]

    @staticmethod
    @pytest.mark.parametrize(
        ("side", "history_length", "expected"),
        [
            (CardSide.FRONT, 0, AnswerCounts()),
            (CardSide.FRONT, 1, AnswerCounts(correct=0, wrong=1, missing=0)),
            (CardSide.FRONT, 2, AnswerCounts(correct=1, wrong=1, missing=0)),
            (CardSide.FRONT, 3, AnswerCounts(correct=1, wrong=1, missing=1)),
            (CardSide.BACK, 0, AnswerCounts()),
            (CardSide.BACK, 1, AnswerCounts(correct=0, wrong=1, missing=0)),
            (CardSide.BACK, 2, AnswerCounts(correct=0, wrong=1, missing=1)),
            (CardSide.BACK, 3, AnswerCounts(correct=0, wrong=1, missing=2)),
            (None, 0, AnswerCounts()),
            (None, 1, AnswerCounts(correct=0, wrong=2, missing=0)),
            (None, 2, AnswerCounts(correct=1, wrong=2, missing=1)),
            (None, 3, AnswerCounts(correct=1, wrong=2, missing=3)),
        ],
    )
    def test_get_answer_counts(card: Card, side: CardSide | None, history_length: int, expected: AnswerCounts) -> None:
        assert card.get_answer_counts(side, history_length) == expected

    @staticmethod
    @pytest.mark.parametrize(
        ("side", "history_length", "expected"),
        [
            (CardSide.FRONT, 0, (0, 0)),
            (CardSide.FRONT, 1, (1, 0)),
            (CardSide.FRONT, 2, (2, 1)),
            (CardSide.FRONT, 3, (2, 1)),
            (CardSide.BACK, 0, (0, 0)),
            (CardSide.BACK, 1, (1, 0)),
            (CardSide.BACK, 2, (1, 0)),
            (CardSide.BACK, 3, (1, 0)),
        ],
    )
    def test_get_score(card: Card, side: CardSide, history_length: int, expected: tuple[int, int]) -> None:
        assert card.get_score(side, history_length) == expected

    @staticmethod
    def test_record_answer() -> None:
        card = Card(front="front", back="back")
        card.record_answer(CardSide.FRONT, correct=True)
        card.record_answer(CardSide.FRONT, correct=False)
        card.record_answer(CardSide.BACK, correct=False)
        card.record_answer(CardSide.BACK, correct=True)
        assert card.front_answer_history == [True, False]
        assert card.back_answer_history == [False, True]

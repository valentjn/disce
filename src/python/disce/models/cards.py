#!/usr/bin/env python
# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Data models for flashcards."""

from enum import StrEnum, auto
from typing import override

from pydantic import BaseModel

from disce.models.base import UUIDModel


class CardSide(StrEnum):
    """Side of a flashcard."""

    FRONT = auto()
    """Front side (e.g., question or term in foreign language)."""
    BACK = auto()
    """Back side (e.g., answer or term in native language)."""

    @property
    def opposite(self) -> "CardSide":
        """Get the opposite side."""
        return CardSide.BACK if self is CardSide.FRONT else CardSide.FRONT


class AnswerCounts(BaseModel):
    """Counts of answers."""

    correct: int = 0
    """Number of correct answers."""
    wrong: int = 0
    """Number of wrong answers."""
    missing: int = 0
    """Number of missing answers."""

    @property
    def total(self) -> int:
        """Get the total number of answers."""
        return self.correct + self.wrong + self.missing

    @property
    def _percentages(self) -> tuple[float, float]:
        """Get the percentages of correct and wrong answers."""
        total = self.total
        if total > 0:
            correct_percentage = self.correct / total * 100.0
            wrong_percentage = self.wrong / total * 100.0
        else:
            correct_percentage = wrong_percentage = 0.0
        return correct_percentage, wrong_percentage

    @override
    def __str__(self) -> str:
        correct_percentage, wrong_percentage = self._percentages
        return (
            f"{correct_percentage:.0f}% correct, {wrong_percentage:.0f}% wrong, "
            f"{100.0 - round(correct_percentage) - round(wrong_percentage):.0f}% missing answers"
        )

    @property
    def gradient(self) -> str:
        """Get a CSS gradient representing the answer distribution."""
        correct_percentage, wrong_percentage = self._percentages
        return (
            "linear-gradient(to right, "
            f"rgba(var(--bs-success-rgb), 0.4) 0% {correct_percentage:.3f}%, "
            "rgba(var(--bs-danger-rgb), 0.4) "
            f"{correct_percentage:.3f}% {correct_percentage + wrong_percentage:.3f}%, "
            "rgba(var(--bs-secondary-rgb), 0.4) "
            f"{correct_percentage + wrong_percentage:.3f}% 100%)"
        )


class Card(UUIDModel):
    """A flashcard."""

    front: str = ""
    """Text on the front side of the card (e.g., question or term in foreign language)."""
    back: str = ""
    """Text on the back side of the card (e.g., answer or term in native language)."""
    enabled: bool = True
    """Whether the card is enabled for review."""
    front_answer_history: list[bool] = []  # noqa: RUF012
    """History of answers when asked for front (correct/wrong, most recent last, reset when card is edited)."""
    back_answer_history: list[bool] = []  # noqa: RUF012
    """History of answers when asked for back (correct/wrong, most recent last, reset when card is edited)."""

    def get_side(self, side: CardSide) -> str:
        """Get the text on the specified side of the card."""
        return self.front if side is CardSide.FRONT else self.back

    def get_answer_history(self, side: CardSide) -> list[bool]:
        """Get the answer history for the specified side of the card."""
        return self.front_answer_history if side is CardSide.FRONT else self.back_answer_history

    def get_answer_counts(self, side: CardSide | None, history_length: int) -> AnswerCounts:
        """Get the answer counts for the specified side of the card, or for both sides if side is None."""
        counts = AnswerCounts()
        if history_length == 0:
            return counts
        for current_side in [side] if side else list(CardSide):
            answer_history = self.get_answer_history(current_side)
            relevant_answer_history = answer_history[-history_length:]
            for answer in relevant_answer_history:
                if answer:
                    counts.correct += 1
                else:
                    counts.wrong += 1
            counts.missing += max(0, history_length - len(relevant_answer_history))
        return counts

    def get_score(self, side: CardSide, history_length: int) -> tuple[int, int]:
        """Get the score for a specific side of the card.

        The lower the score, the more the card should be studied.
        """
        answer_history = self.get_answer_history(side)
        relevant_answer_history = answer_history[-history_length:] if history_length > 0 else []
        return (len(relevant_answer_history), sum(relevant_answer_history))

    def record_answer(self, side: CardSide, *, correct: bool) -> None:
        """Record an answer for the specified side of the card."""
        self.get_answer_history(side).append(correct)

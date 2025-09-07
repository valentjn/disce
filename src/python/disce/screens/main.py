#!/usr/bin/env python
# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Screen for the main menu."""

from pyscript import when

from disce import data, tools
from disce.screens import tools as screen_tools
from disce.screens.tools import select_element


@when("click", ".back-to-main-screen-btn")
def show() -> None:
    """Show the main menu screen."""
    saved_data = data.SavedData.load_from_local_storage()
    number_of_cards = sum(len(deck.cards) for deck in saved_data.decks)
    select_element("#main-screen-status-text").innerText = (
        f"Loaded {tools.format_number(len(saved_data.decks), 'deck')} with "
        f"{tools.format_number(number_of_cards, 'card')}."
    )
    screen_tools.hide_all()
    select_element("#main-screen").style.display = "block"


def hide() -> None:
    """Hide the main menu screen."""
    select_element("#main-screen").style.display = "none"

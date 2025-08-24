#!/usr/bin/env python
# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Main module."""

from pyscript import document  # type: ignore[import-not-found]

from disce import data, util

select = document.querySelector


def main() -> None:
    """Run the main application logic."""
    show_main_menu()
    hide_loading_screen()


def show_main_menu() -> None:
    """Show the main menu."""
    saved_data = data.SavedData.load_from_local_storage()
    number_of_cards = sum(len(deck.cards) for deck in saved_data.decks)
    select("#main-menu-status-text").innerText = (
        f"Loaded {util.format_number(len(saved_data.decks), 'deck')} with "
        f"{util.format_number(number_of_cards, 'card')}."
    )
    select("#main-menu").style.display = "block"


def hide_loading_screen() -> None:
    """Hide the loading screen and show the main content."""
    select("#loading-screen").style.display = "none"
    select("#main").style.display = "block"


if __name__ == "__main__":
    main()

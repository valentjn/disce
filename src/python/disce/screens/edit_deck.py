#!/usr/bin/env python
# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Screen for editing a single deck."""

import logging
from typing import Any

from pyscript import when, window

from disce import data
from disce.screens import decks as decks_screen
from disce.screens import tools as screen_tools
from disce.screens.tools import append_child, create_element, select_all_elements, select_element
from disce.tools import format_plural

_logger = logging.getLogger(__name__)


def show(*, deck_uuid: str | None) -> None:
    """Show the edit deck screen for a given deck (or new deck if ``None``)."""
    configuration = data.Configuration.load_from_local_storage()
    deck_metadata = configuration.get_deck_metadata(deck_uuid) if deck_uuid is not None else data.DeckMetadata()
    render_deck(deck_metadata)
    screen_tools.hide_all()
    select_element("#disce-edit-deck-screen").style.display = "block"


def hide() -> None:
    """Hide the edit deck screen."""
    select_element("#disce-edit-deck-screen").style.display = "none"


def render_deck(deck_metadata: data.DeckMetadata) -> None:
    """Render the edit deck screen."""
    select_element("#disce-edit-deck-screen .disce-deck-uuid-hidden").value = deck_metadata.uuid
    select_element("#disce-edit-deck-screen .disce-deck-name-textbox").value = deck_metadata.name
    cards_div = select_element("#disce-edit-deck-screen .disce-cards")
    cards_div.innerHTML = ""
    cards = (
        data.DeckData.load_from_local_storage(deck_metadata.uuid).cards
        if data.DeckData.exists_in_local_storage(deck_metadata.uuid)
        else []
    )
    cards.append(data.Card())
    for card in cards:
        cards_div.appendChild(create_card_div(card))
    update_bulk_buttons()


def create_card_div(card: data.Card) -> Any:  # noqa: ANN401
    """Create a div representing a card for editing."""
    card_div = create_element("div", class_="disce-card row gx-3 align-items-center mb-2", data_card_uuid=card.uuid)
    append_child(
        card_div,
        "div",
        create_element(
            "div",
            create_element(
                "input",
                event_handlers={"change": update_bulk_buttons},
                type="checkbox",
                class_="disce-selected-checkbox form-check-input",
                title="Select this card for bulk actions",
                data_card_uuid=card.uuid,
            ),
            class_="form-check",
        ),
        class_="col-auto",
    )
    append_child(
        card_div,
        "div",
        create_element(
            "input",
            event_handlers={"input": card_text_changed},
            type="text",
            class_="disce-front-textbox form-control",
            value=card.front,
            placeholder="Front",
            data_card_uuid=card.uuid,
        ),
        class_="col-sm",
    )
    append_child(
        card_div,
        "div",
        create_element(
            "input",
            event_handlers={"input": card_text_changed},
            type="text",
            class_="disce-back-textbox form-control",
            value=card.back,
            placeholder="Back",
            data_card_uuid=card.uuid,
        ),
        class_="col-sm",
    )
    append_child(
        card_div,
        "div",
        create_element(
            "div",
            create_element(
                "input",
                id_=f"disce-enabled-checkbox-{card.uuid}",
                type="checkbox",
                class_="disce-enabled-checkbox form-check-input",
                data_card_uuid=card.uuid,
                **({"checked": "checked"} if card.enabled else {}),  # type: ignore[arg-type]
            ),
            create_element(
                "label", class_="form-check-label", text="Enabled", for_=f"disce-enabled-checkbox-{card.uuid}"
            ),
            class_="form-check",
        ),
        class_="col-auto",
    )
    append_child(
        card_div,
        "input",
        type="hidden",
        class_="disce-answer-history-hidden",
        value="".join("Y" if x else "N" for x in card.answer_history),
        data_card_uuid=card.uuid,
    )
    return card_div


@when("input", "#disce-edit-deck-screen .disce-front-textbox, #disce-edit-deck-screen .disce-back-textbox")
def card_text_changed() -> None:
    """Make sure there's always an empty card at the end."""
    cards = select_all_elements("#disce-edit-deck-screen .disce-card")
    if not cards:
        msg = "no cards found in edit deck screen"
        raise RuntimeError(msg)
    last_card_front = cards[-1].querySelector(".disce-front-textbox").value
    last_card_back = cards[-1].querySelector(".disce-back-textbox").value
    if last_card_front or last_card_back:
        cards_div = select_element("#disce-edit-deck-screen .disce-cards")
        cards_div.appendChild(create_card_div(data.Card()))
    update_bulk_buttons()


@when("click", "#disce-edit-deck-screen .disce-save-deck-btn")
def save_deck() -> None:
    """Save the current deck."""
    deck_data, deck_metadata = get_deck()
    if data.DeckData.exists_in_local_storage(deck_data.uuid):
        original_deck_data = data.DeckData.load_from_local_storage(deck_data.uuid)
        original_cards = {card.uuid: card for card in original_deck_data.cards}
        for card in deck_data.cards:
            if (original_card := original_cards.get(card.uuid)) is not None and (
                original_card.front != card.front or original_card.back != card.back
            ):
                card.answer_history.clear()
    configuration = data.Configuration.load_from_local_storage()
    configuration.set_deck_metadata(deck_metadata)
    configuration.save_to_local_storage()
    deck_data.save_to_local_storage()
    window.bootstrap.Toast.new(select_element("#disce-edit-deck-screen .disce-deck-saved-toast")).show()


@when("click", "#disce-edit-deck-screen .disce-select-all-btn")
def select_all_decks() -> None:
    """Select or deselect all decks."""
    card_uuids = get_card_uuids()
    selected_card_uuids = get_selected_card_uuids()
    select_all = len(selected_card_uuids) < len(card_uuids)
    for checkbox in select_all_elements("#disce-edit-deck-screen .disce-selected-checkbox"):
        checkbox.checked = select_all
    update_bulk_buttons()


@when("click", "#disce-edit-deck-screen .disce-delete-cards-btn")
def delete_selected_cards() -> None:
    """Delete the selected cards."""
    selected_card_uuids = set(get_selected_card_uuids())
    if not selected_card_uuids:
        return
    if window.confirm(
        f"Are you sure you want to delete the selected {format_plural(len(selected_card_uuids), 'card')}?"
    ):
        deck_data, deck_metadata = get_deck()
        deck_data.cards = [card for card in deck_data.cards if card.uuid not in selected_card_uuids]
        render_deck(deck_metadata)


@when("change", "#disce-edit-deck-screen .disce-selected-checkbox")
def update_bulk_buttons() -> None:
    """Update the bulk action buttons based on selection."""
    card_uuids = get_card_uuids()
    selected_card_uuids = get_selected_card_uuids()
    select_element("#disce-edit-deck-screen .disce-select-all-btn .disce-btn-text").innerText = (
        " Deselect All" if len(selected_card_uuids) >= len(card_uuids) and card_uuids else " Select All"
    )
    select_element("#disce-edit-deck-screen .disce-delete-cards-btn").disabled = len(selected_card_uuids) == 0


@when("click", "#disce-edit-deck-screen .disce-back-to-decks-screen-btn")
def back_to_decks_screen() -> None:
    """Go back to the edit decks screen."""
    deck_data, deck_metadata = get_deck()
    configuration = data.Configuration.load_from_local_storage()
    if configuration.deck_metadata_exists(deck_metadata.uuid) and data.DeckData.exists_in_local_storage(deck_data.uuid):
        original_deck_metadata = configuration.get_deck_metadata(deck_data.uuid)
        if original_deck_metadata == deck_metadata:
            original_deck_data = data.DeckData.load_from_local_storage(deck_data.uuid)
            unsaved_changes = original_deck_data != deck_data
        else:
            unsaved_changes = True
    else:
        unsaved_changes = len(deck_data.cards) > 0
    if unsaved_changes and not window.confirm("You have unsaved changes. Do you want to discard them?"):
        return
    decks_screen.show()


def get_deck() -> tuple[data.DeckData, data.DeckMetadata]:
    """Get the current deck from the edit deck screen."""
    deck_uuid = select_element("#disce-edit-deck-screen .disce-deck-uuid-hidden").value
    deck_name = select_element("#disce-edit-deck-screen .disce-deck-name-textbox").value
    cards = []
    for card_div in select_all_elements("#disce-edit-deck-screen .disce-card"):
        uuid: str = card_div.getAttribute("data-card-uuid")
        front: str = card_div.querySelector(".disce-front-textbox").value
        back: str = card_div.querySelector(".disce-back-textbox").value
        if not front and not back:
            continue
        enabled = bool(card_div.querySelector(".disce-enabled-checkbox").checked)
        answer_history_str: str = card_div.querySelector(".disce-answer-history-hidden").value
        answer_history = [character.upper() == "Y" for character in answer_history_str]
        cards.append(data.Card(uuid=uuid, front=front, back=back, enabled=enabled, answer_history=answer_history))
    return data.DeckData(uuid=deck_uuid, cards=cards), data.DeckMetadata(
        uuid=deck_uuid, name=deck_name, number_of_cards=len(cards)
    )


def get_card_uuids() -> list[str]:
    """Get the UUIDs of all cards."""
    return [
        card_div.getAttribute("data-card-uuid")
        for card_div in select_all_elements("#disce-edit-deck-screen .disce-card")
    ][:-1]


def get_selected_card_uuids() -> list[str]:
    """Get the UUIDs of the selected cards."""
    checkboxes = list(select_all_elements("#disce-edit-deck-screen .disce-selected-checkbox"))[:-1]
    return [checkbox.getAttribute("data-card-uuid") for checkbox in checkboxes if checkbox.checked]

#!/usr/bin/env python
# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Screen for editing a single deck."""

from typing import override

import disce.screens.decks as decks_screen
from disce.data import UUID, Card, Configuration, DeckData, DeckMetadata, UUIDModelList
from disce.pyscript import (
    Element,
    Event,
    EventBinding,
    append_child,
    confirm,
    create_element,
    show_toast,
)
from disce.screens.base import AbstractScreen
from disce.storage.base import AbstractStorage
from disce.tools import format_plural


class EditDeckScreen(AbstractScreen):
    """Screen for editing a single deck."""

    def __init__(self, deck_uuid: UUID | None, storage: AbstractStorage) -> None:
        """Initialize the screen."""
        super().__init__("#disce-edit-deck-screen")
        self._deck_uuid = deck_uuid
        self._storage = storage

    @override
    def get_static_event_bindings(self) -> list[EventBinding]:
        return [
            EventBinding(self.select_child(".disce-save-deck-btn"), "click", self.save_deck),
            EventBinding(self.select_child(".disce-select-all-btn"), "click", self.select_all_decks),
            EventBinding(self.select_child(".disce-delete-cards-btn"), "click", self.delete_cards),
            EventBinding(self.select_child(".disce-back-to-decks-screen-btn"), "click", self.back_to_decks_screen),
        ]

    @override
    def render(self, deck_data: DeckData | None = None, deck_metadata: DeckMetadata | None = None) -> None:
        if deck_metadata is None:
            configuration = Configuration.load_from_storage_or_create(self._storage)
            deck_metadata = (
                configuration.deck_metadata[self._deck_uuid] if self._deck_uuid is not None else DeckMetadata()
            )
        self.select_child(".disce-deck-name-textbox").value = deck_metadata.name
        self.unregister_event_bindings(dynamic=True)
        cards_div = self.select_child(".disce-cards")
        cards_div.innerHTML = ""
        cards = (deck_data if deck_data else self.load_deck_data(uuid=deck_metadata.uuid)).cards.model_copy()
        cards.set(Card())
        for card in cards:
            cards_div.appendChild(self.create_card_div(card))
        self.update_bulk_buttons()

    def create_card_div(self, card: Card) -> Element:
        """Create a div representing a card for editing."""
        card_div = create_element("div", class_="disce-card row gx-3 align-items-center mb-2", data_card_uuid=card.uuid)
        selected_checkbox = create_element(
            "input",
            type="checkbox",
            class_="disce-selected-checkbox form-check-input",
            title="Select this card for bulk actions",
            data_card_uuid=card.uuid,
        )
        self.register_event_binding(EventBinding(selected_checkbox, "change", self.update_bulk_buttons), dynamic=True)
        append_child(card_div, "div", create_element("div", selected_checkbox, class_="form-check"), class_="col-auto")
        front_textbox = create_element(
            "input",
            type="text",
            class_="disce-front-textbox form-control",
            value=card.front,
            placeholder="Front",
            data_card_uuid=card.uuid,
        )
        self.register_event_binding(EventBinding(front_textbox, "input", self.card_text_changed), dynamic=True)
        append_child(card_div, "div", front_textbox, class_="col-sm")
        back_textbox = create_element(
            "input",
            type="text",
            class_="disce-back-textbox form-control",
            value=card.back,
            placeholder="Back",
            data_card_uuid=card.uuid,
        )
        self.register_event_binding(EventBinding(back_textbox, "input", self.card_text_changed), dynamic=True)
        append_child(card_div, "div", back_textbox, class_="col-sm")
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
        return card_div

    def card_text_changed(self, _event: Event | None = None) -> None:
        """Make sure there's always an empty card at the end."""
        card_divs = self.select_all_children(".disce-card")
        if (
            not card_divs
            or card_divs[-1].querySelector(".disce-front-textbox").value
            or card_divs[-1].querySelector(".disce-back-textbox").value
        ):
            cards_div = self.select_child(".disce-cards")
            cards_div.appendChild(self.create_card_div(Card()))
        self.update_bulk_buttons()

    def save_deck(self, _event: Event | None = None) -> None:
        """Save the current deck."""
        deck_data, deck_metadata = self.get_deck()
        if DeckData.exists_in_storage(self._storage, deck_data.uuid):
            original_deck_data = DeckData.load_from_storage(self._storage, deck_data.uuid)
            original_cards = {card.uuid: card for card in original_deck_data.cards}
            for card in deck_data.cards:
                if (original_card := original_cards.get(card.uuid)) is not None and (
                    original_card.front != card.front or original_card.back != card.back
                ):
                    card.front_answer_history.clear()
                    card.back_answer_history.clear()
        configuration = Configuration.load_from_storage_or_create(self._storage)
        configuration.deck_metadata.set(deck_metadata)
        configuration.save_to_storage(self._storage)
        deck_data.save_to_storage(self._storage)
        show_toast(self.select_child(".disce-deck-saved-toast"))

    def select_all_decks(self, _event: Event | None = None) -> None:
        """Select or deselect all decks."""
        card_uuids = self.get_card_uuids()
        selected_card_uuids = self.get_selected_card_uuids()
        select_all = len(selected_card_uuids) < len(card_uuids)
        for checkbox in self.select_all_children(".disce-selected-checkbox"):
            checkbox.checked = select_all
        self.update_bulk_buttons()

    def delete_cards(self, _event: Event | None = None) -> None:
        """Delete the selected cards."""
        selected_card_uuids = set(self.get_selected_card_uuids())
        if not selected_card_uuids:
            return
        if confirm(f"Are you sure you want to delete the selected {format_plural(len(selected_card_uuids), 'card')}?"):
            deck_data, deck_metadata = self.get_deck()
            deck_data.cards = UUIDModelList([card for card in deck_data.cards if card.uuid not in selected_card_uuids])
            deck_metadata.number_of_cards = len(deck_data.cards)
            self.render(deck_data=deck_data, deck_metadata=deck_metadata)

    def update_bulk_buttons(self, _event: Event | None = None) -> None:
        """Update the bulk action buttons based on selection."""
        card_uuids = self.get_card_uuids()
        selected_card_uuids = self.get_selected_card_uuids()
        self.select_child(".disce-select-all-btn").setAttribute(
            "title", "Deselect all" if len(selected_card_uuids) == len(card_uuids) > 0 else "Select all"
        )
        self.select_child(".disce-select-all-btn .disce-btn-text").innerText = (
            " Deselect All" if len(selected_card_uuids) >= len(card_uuids) > 0 else " Select All"
        )
        self.select_child(".disce-delete-cards-btn").disabled = len(selected_card_uuids) == 0

    def back_to_decks_screen(self, _event: Event | None = None) -> None:
        """Go back to the decks screen."""
        deck_data, deck_metadata = self.get_deck()
        configuration = Configuration.load_from_storage_or_create(self._storage)
        if deck_metadata.uuid in configuration.deck_metadata and DeckData.exists_in_storage(
            self._storage, deck_data.uuid
        ):
            original_deck_metadata = configuration.deck_metadata[deck_data.uuid]
            if original_deck_metadata == deck_metadata:
                original_deck_data = DeckData.load_from_storage(self._storage, deck_data.uuid)
                unsaved_changes = original_deck_data != deck_data
            else:
                unsaved_changes = True
        else:
            unsaved_changes = len(deck_data.cards) > 0
        if unsaved_changes and not confirm("You have unsaved changes. Do you want to discard them?"):
            return
        decks_screen.DecksScreen(self._storage).show()
        self.hide()

    def load_deck_data(self, uuid: UUID | None = None) -> DeckData:
        """Load the deck data from storage."""
        if not uuid:
            uuid = self._deck_uuid
        return (
            DeckData.load_from_storage(self._storage, uuid)
            if uuid and DeckData.exists_in_storage(self._storage, uuid)
            else DeckData()
        )

    def get_deck(self) -> tuple[DeckData, DeckMetadata]:
        """Get the current deck from the edit deck screen."""
        deck_name = self.select_child(".disce-deck-name-textbox").value
        cards = UUIDModelList[Card]()
        for card_div in self.select_all_children(".disce-card"):
            uuid: UUID = card_div.getAttribute("data-card-uuid")
            card = self.load_deck_data().cards.get(uuid, Card(uuid=uuid))
            front: str = card_div.querySelector(".disce-front-textbox").value
            back: str = card_div.querySelector(".disce-back-textbox").value
            if not front and not back:
                continue
            card.front = front
            card.back = back
            card.enabled = bool(card_div.querySelector(".disce-enabled-checkbox").checked)
            cards.set(card)
        deck_data = DeckData(cards=cards)
        deck_metadata = DeckMetadata(name=deck_name, number_of_cards=len(cards))
        if self._deck_uuid is not None:
            deck_data.uuid = self._deck_uuid
            deck_metadata.uuid = self._deck_uuid
        return deck_data, deck_metadata

    def get_card_uuids(self) -> list[UUID]:
        """Get the UUIDs of all cards."""
        return [card_div.getAttribute("data-card-uuid") for card_div in self.select_all_children(".disce-card")][:-1]

    def get_selected_card_uuids(self) -> list[UUID]:
        """Get the UUIDs of the selected cards."""
        checkboxes = list(self.select_all_children(".disce-selected-checkbox"))[:-1]
        return [checkbox.getAttribute("data-card-uuid") for checkbox in checkboxes if checkbox.checked]

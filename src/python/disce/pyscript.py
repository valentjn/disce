#!/usr/bin/env python
# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Screen management."""

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any, cast

from pyodide.ffi import JsNull
from pyodide.ffi.wrappers import add_event_listener, remove_event_listener  # pyright: ignore[reportMissingModuleSource]
from pyscript import document, window

type Element = Any
type Event = Any
type EventListener = Callable[[], None] | Callable[[Event], None]

select_all_elements = document.querySelectorAll
select_element = document.querySelector


@dataclass(frozen=True)
class EventBinding:
    """Data class representing an event binding."""

    element: Element
    """Element to which the event listener is attached."""
    event_name: str
    """Name of the event."""
    listener: EventListener
    """Event listener function."""

    def register(self) -> None:
        """Register the event listener."""
        add_event_listener(self.element, self.event_name, self.listener)

    def unregister(self) -> None:
        """Unregister the event listener."""
        remove_event_listener(self.element, self.event_name, self.listener)


def create_element(
    tag: str,
    *children: Element,
    text: str | None = None,
    html: str | None = None,
    event_listeners: Mapping[str, EventListener | Sequence[EventListener]] | None = None,
    **attributes: str,
) -> Element:
    """Create a new HTML element with given attributes."""
    element = document.createElement(tag)
    for name, value in attributes.items():
        element.setAttribute(name.removesuffix("_").replace("_", "-"), value)
    if text is not None:
        element.innerText = text
    if html is not None:
        element.innerHTML = html
    if event_listeners:
        for event, listeners in event_listeners.items():
            for listener in listeners if isinstance(listeners, Sequence) else [listeners]:
                add_event_listener(element, event, listener)
    for child in children:
        element.appendChild(child)
    return element


def append_child(
    parent: Element,
    tag: str,
    *children: Element,
    text: str | None = None,
    html: str | None = None,
    event_listeners: Mapping[str, EventListener | Sequence[EventListener]] | None = None,
    **attributes: str,
) -> Element:
    """Create a new HTML element with given attributes and append it to the parent."""
    element = create_element(tag, *children, text=text, html=html, event_listeners=event_listeners, **attributes)
    parent.appendChild(element)
    return element


def hide_element(element: Element, *, hide: bool = True) -> None:
    """Hide the given element."""
    if hide:
        element.classList.add("d-none")
    else:
        show_element(element)


def show_element(element: Element, *, show: bool = True) -> None:
    """Show the given element."""
    if show:
        element.classList.remove("d-none")
    else:
        hide_element(element)


def set_theme(theme: str | None = None) -> None:
    """Set the theme of the application."""
    if theme is None:
        theme = "dark" if window.matchMedia("(prefers-color-scheme: dark)").matches else "light"
    document.documentElement.setAttribute("data-bs-theme", theme)


def download_file(filename: str, type_: str, content: str) -> None:
    """Offer a file for download with the given content."""
    blob = window.Blob.new([content], {"type": type_})
    url = window.URL.createObjectURL(blob)
    a_element = create_element("a", href=url, download=filename)
    a_element.click()
    window.URL.revokeObjectURL(url)


def upload_file(accepted_types: str, listener: Callable[[str], None]) -> Element:
    """Open a file dialog and handle the selected file with the given listener."""

    def handle_uploaded_file(event: Event) -> None:
        input_element = event.currentTarget
        for file in input_element.files:
            reader = window.FileReader.new()
            add_event_listener(reader, "load", process_loaded_data)
            reader.readAsText(file)

    def process_loaded_data(event: Event) -> None:  # pragma: no cover
        listener(event.currentTarget.result)

    input_element = create_element(
        "input", event_listeners={"change": handle_uploaded_file}, type="file", accept=accepted_types
    )
    input_element.click()
    return input_element


def show_modal(element: Element) -> None:  # pragma: no cover
    """Show a modal dialog for the given element."""
    window.bootstrap.Modal.new(element).show()


def show_toast(element: Element) -> None:  # pragma: no cover
    """Show a toast notification for the given element."""
    window.bootstrap.Toast.new(element).show()


def alert(message: str) -> None:
    """Show an alert dialog with the given message."""
    window.alert(message)


def confirm(message: str) -> bool:
    """Show a confirmation dialog with the given message."""
    return cast("bool", window.confirm(message))


def prompt(message: str, default: str = "") -> str | None:
    """Show a prompt dialog with the given message and default value."""
    input_ = window.prompt(message, default)
    return None if is_null(input_) else cast("str", input_)


def is_null(value: Any) -> bool:  # noqa: ANN401
    """Check if a value is JavaScript ``null``."""
    return isinstance(value, JsNull)

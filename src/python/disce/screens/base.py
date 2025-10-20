#!/usr/bin/env python
# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Module defining the base class for all screens."""

from abc import ABC, abstractmethod
from dataclasses import dataclass

from pyodide.ffi import JsNull
from pyodide.ffi.wrappers import add_event_listener, remove_event_listener

from disce.screens.tools import Element, EventListener, hide_element, select_element, show_element


@dataclass
class EventBinding:
    """Data class representing an event binding."""

    element: Element
    """Element to which the event listener is attached."""
    event: str
    """Name of the event."""
    listener: EventListener
    """Event listener function."""

    def register(self) -> None:
        """Register the event listener."""
        add_event_listener(self.element, self.event, self.listener)

    def unregister(self) -> None:
        """Unregister the event listener."""
        remove_event_listener(self.element, self.event, self.listener)


class AbstractScreen(ABC):
    """Abstract base class for all screens."""

    def __init__(self, selector: str) -> None:
        """Initialize the screen."""
        self._static_event_bindings: list[EventBinding] = []
        self._dynamic_event_bindings: list[EventBinding] = []
        self._selector = selector

    @property
    def selector(self) -> Element:
        """CSS selector for the screen's root element."""
        return self._selector

    @abstractmethod
    def render(self) -> None:
        """Render the screen."""
        raise NotImplementedError

    def register_static_event_listeners(self) -> None:
        """Register all static event listeners."""
        for binding in self._get_static_event_listeners():
            self.register_event_listener(binding, dynamic=False)

    @abstractmethod
    def _get_static_event_listeners(self) -> list[EventBinding]:
        """Get all static event listeners."""
        raise NotImplementedError

    def register_event_listener(self, binding: EventBinding, *, dynamic: bool) -> None:
        """Register a specific event listener."""
        binding.register()
        event_bindings = self._get_event_bindings(dynamic=dynamic)
        event_bindings.append(binding)

    def unregister_event_listeners(self, *, dynamic: bool) -> None:
        """Unregister all event listeners."""
        event_bindings = self._get_event_bindings(dynamic=dynamic)
        for event_binding in event_bindings.copy():
            event_binding.unregister()

    def unregister_event_listener(self, binding: EventBinding, *, dynamic: bool) -> None:
        """Unregister a specific event listener."""
        event_bindings = self._get_event_bindings(dynamic=dynamic)
        if binding in event_bindings:
            binding.unregister()
            event_bindings.remove(binding)

    def _get_event_bindings(self, *, dynamic: bool) -> list[EventBinding]:
        """Get the list of event bindings."""
        return self._dynamic_event_bindings if dynamic else self._static_event_bindings

    @property
    def element(self) -> Element:
        """Root element of the screen."""
        return select_element(self.selector)

    def select_child(self, selector: str) -> Element:
        """Select a child element within the screen."""
        element = self.element.querySelector(selector)
        if isinstance(element, JsNull):
            msg = f"could not find child element of {self.selector} matching selector: {selector}"
            raise ValueError(msg)  # noqa: TRY004
        return element

    def select_all_children(self, selector: str) -> list[Element]:
        """Select all child elements within the screen."""
        return list(self.element.querySelectorAll(selector))

    def show(self) -> None:
        """Show the screen."""
        self.register_static_event_listeners()
        self.render()
        show_element(self.element)

    def hide(self) -> None:
        """Hide the screen."""
        self.unregister_event_listeners(dynamic=True)
        self.unregister_event_listeners(dynamic=False)
        hide_element(self.element)

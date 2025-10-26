#!/usr/bin/env python
# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from collections.abc import Generator
from typing import override

import pytest
from disce.pyscript import Event, EventBinding, append_child, create_element
from disce.screens.base import AbstractScreen
from pyscript import window

from disce_tests.injected.tools import assert_hidden, assert_visible, insert_element


class DummyScreen(AbstractScreen):
    def __init__(self, selector: str) -> None:
        super().__init__(selector)
        self._clicked = False
        self.rendered = False

    @override
    def render(self) -> None:
        self.rendered = True

    @override
    def get_static_event_bindings(self) -> list[EventBinding]:
        return [EventBinding(self.element, "click", self.set_clicked)]

    def set_clicked(self, _: Event | None = None) -> None:
        self._clicked = True

    def assert_click_works(self, *, expected: bool = True) -> None:
        self._clicked = False
        self.element.dispatchEvent(window.Event.new("click"))
        assert self._clicked == expected


class TestAbstractScreen:
    @staticmethod
    @pytest.fixture
    def screen() -> Generator[DummyScreen]:
        id_ = "dummy-screen"
        element = create_element("div", id=id_)
        with insert_element(element):
            yield DummyScreen(f"#{id_}")

    @staticmethod
    def test_selector(screen: DummyScreen) -> None:
        assert screen.selector == "#dummy-screen"

    @staticmethod
    def test_render(screen: DummyScreen) -> None:
        with pytest.raises(NotImplementedError):
            AbstractScreen.render(screen)

    @staticmethod
    def test_register_static_event_bindings(screen: DummyScreen) -> None:
        screen.register_static_event_bindings()
        screen.assert_click_works()

    @staticmethod
    def test_get_static_event_bindings(screen: DummyScreen) -> None:
        with pytest.raises(NotImplementedError):
            AbstractScreen.get_static_event_bindings(screen)

    @staticmethod
    @pytest.mark.parametrize("dynamic", [True, False])
    def test_register_unregister_event_binding(screen: DummyScreen, *, dynamic: bool) -> None:
        binding = EventBinding(screen.element, "click", screen.set_clicked)
        screen.register_event_binding(binding, dynamic=dynamic)
        screen.assert_click_works()
        screen.unregister_event_binding(binding, dynamic=not dynamic)
        screen.assert_click_works()
        screen.unregister_event_binding(binding, dynamic=dynamic)
        screen.assert_click_works(expected=False)

    @staticmethod
    @pytest.mark.parametrize("dynamic", [True, False])
    def test_unregister_event_bindings(screen: DummyScreen, *, dynamic: bool) -> None:
        binding = EventBinding(screen.element, "click", screen.set_clicked)
        screen.register_event_binding(binding, dynamic=dynamic)
        screen.assert_click_works()
        screen.unregister_event_bindings(dynamic=not dynamic)
        screen.assert_click_works()
        screen.unregister_event_bindings(dynamic=dynamic)
        screen.assert_click_works(expected=False)

    @staticmethod
    def test_element(screen: DummyScreen) -> None:
        assert screen.element.id == "dummy-screen"

    @staticmethod
    def test_select_child(screen: DummyScreen) -> None:
        id_ = "dummy-screen-child"
        child = append_child(screen.element, "span", id=id_)
        selected_child = screen.select_child(f"#{id_}")
        assert selected_child.isSameNode(child)

    @staticmethod
    def test_select_child_not_found(screen: DummyScreen) -> None:
        with pytest.raises(
            ValueError, match=r"^could not find child element of #dummy-screen matching selector: #nonexistent-child$"
        ):
            screen.select_child("#nonexistent-child")

    @staticmethod
    def test_select_all_children(screen: DummyScreen) -> None:
        class_ = "dummy-screen-child"
        child1 = append_child(screen.element, "span", class_=class_)
        child2 = append_child(screen.element, "p", class_=class_)
        selected_children = screen.select_all_children(f".{class_}")
        assert len(selected_children) == 2
        assert any(child.isSameNode(child1) for child in selected_children)
        assert any(child.isSameNode(child2) for child in selected_children)

    @staticmethod
    def test_show_hide(screen: DummyScreen) -> None:
        screen.show()
        screen.assert_click_works()
        assert screen.rendered
        assert_visible(screen)
        screen.hide()
        screen.assert_click_works(expected=False)
        assert_hidden(screen)

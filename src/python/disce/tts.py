# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Speech synthesis/text-to-speech (TTS)."""

from dataclasses import dataclass
from typing import override

from pyscript import window


@dataclass(frozen=True)
class Voice:
    """Speech synthesis voice."""

    name: str
    """Name of the voice."""
    language: str
    """BCP 47 language tag (e.g. ``en-US``)."""

    @override
    def __str__(self) -> str:
        return f"{self.language}: {self.name}"


def get_available_voices() -> list[Voice]:
    """Get the list of available speech synthesis voices."""
    voices = [Voice(voice.name, voice.lang) for voice in window.speechSynthesis.getVoices()]
    voices.sort(key=lambda v: (v.language, v.name))
    return voices


def speak(text: str, voice_name: str | None, *, pitch: float = 1.0, rate: float = 1.0, volume: float = 1.0) -> None:
    """Speak the given text using the specified voice.

    :param text: Text to speak.
    :param voice_name: Name of the voice to use for speaking. If ``None``, the default voice will be used.
    :param pitch: Pitch of the speech, between 0.0 and 2.0.
    :param rate: Rate (speed) of the speech, between 0.1 and 10.0.
    :param volume: Volume of the speech, between 0.0 and 1.0.
    """
    utterance = window.SpeechSynthesisUtterance.new(text)
    if voice_name:  # pragma: no cover
        voice = next((v for v in window.speechSynthesis.getVoices() if v.name == voice_name), None)
        if not voice:
            msg = f"voice {voice_name} not found among available voices: {get_available_voices()}"
            raise ValueError(msg)
        utterance.voice = voice
    utterance.pitch = pitch
    utterance.rate = rate
    utterance.volume = volume
    window.speechSynthesis.speak(utterance)

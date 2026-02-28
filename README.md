<!-- Copyright (C) 2025 Julian Valentin
   -
   - This Source Code Form is subject to the terms of the Mozilla Public
   - License, v. 2.0. If a copy of the MPL was not distributed with this
   - file, You can obtain one at https://mozilla.org/MPL/2.0/.
   -->

# Disce

Disce (Latin for &ldquo;learn!&rdquo;) is a lightweight flashcard application that runs entirely in the browser. There is no server component, and all data is stored locally on the user's device.

## Features

- Serverless: No need for a server, all data is stored locally in the browser
- Deck management: Create, edit, and delete decks of flashcards
- Import and export decks as JSON
- Visual progress tracking with progress bars for each deck and card
- Study flashcards endlessly with a simple algorithm ([see below](#study-algorithm)) by either typing the answer or just flipping the card
- Support for ruby characters for learning East Asian languages (e.g., furigana for Japanese)
- Optionally use text-to-speech (TTS) to read flashcards aloud while studying

## Usage

To use Disce, simply open <https://valentjn.github.io/disce/> in a modern web browser.

If you want to run Disce locally, you need to serve the files in `src/` using a web server.

Disce uses the browser's local storage to save decks and configuration. While the data will be retained for a while, browsers may remove the data without notice if the application has not been used for an extended period (e.g., one month). To prevent data loss, it is recommended to regularly export your decks.

## Study Algorithm

Other systems like Anki use sophisticated spaced repetition algorithms to determine which flashcards to show during a study session. Once all cards the system thinks the user should review have been shown, the session ends. This approach is not well suited for people who study in short breaks or in long sessions, since there may be no cards to review. In addition, complex algorithms can make it difficult to understand why certain cards are shown.

Disce uses a simple study algorithm:

1. From the set of all cards of the decks being studied, remove the cards that have been studied in the last 5 cards shown if there are more than 5 cards in total.
2. For each possible pair of card and side (front or back), compute the number of consecutive times the user has answered that side of the card correctly (the &ldquo;run length&rdquo;), up to a maximum of 5.
3. Find the minimum run length among all pairs of card and side.
4. From the pairs of card and side that have that minimum run length, randomly select one and show that side of the card to the user.

This algorithm has the following advantages:

- It is simple and easy to understand. There is no time-based scheduling or complex scoring system.
- There are always cards to study.
- Cards that the user has not answered correctly recently are prioritized.
- Cards can be added later and will be shown immediately due to their run length of 0.
- Immediate repetition (which would only test the user's short-term memory) is avoided.

## Development

Disce is built using PyScript, which runs Python code in the browser using Pyodide, a Python distribution compiled to WebAssembly.

### Contributing

To set up a development environment and contribute to Disce, follow these steps:

1. Fork and clone the repository.
2. Install the following dependencies:
   - [uv](https://docs.astral.sh/uv/)
   - [npm](https://www.npmjs.com/) (only used for formatting and development scripts)
3. Run `uv sync` and `npm install` to install the dependencies.
4. Run `npm run serve` to start a local web server and open `http://127.0.0.1:8000/` in your browser to see the application.
5. Implement your changes.
6. Run `npm run fmt:fix` to format the code and `npm run lint` to check for linting errors.
7. Run `npm test` (short `npm t`) to run the tests.
8. Create a pull request.

On each push to the `main` branch, a GitHub Action will build the project and deploy it to GitHub Pages.

### Tests

Tests are written using pytest and split into native and injected tests:

- Native tests run in the normal Python environment and currently comprise unit tests for the modules that do not depend on the browser environment. There is also the possibility to run end-to-end (E2E) tests in a headless browser environment using Selenium, but there are currently none implemented.
- Injected tests run directly in the browser by calling pytest inside Pyodide. They are used to test the UI and other browser-specific functionality.

Running `npm test` automatically runs first the injected tests and then the native tests, and combines the coverage reports to ensure that the entire codebase is covered. You can also run the tests separately using `npm run test:injected` and `npm run test:native`.

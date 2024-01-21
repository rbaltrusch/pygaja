# PyGaJa

Pygame Game Jam engine, a small, fully type-hinted game engine using pygame, intended to be used for short game jams.

Contains implementations for:
- a particle system
- animations
- basic scene and entity handling
- coordinate handling
- sound and music handling
- WASM builds
- icon handling
- utilities for fonts and text rendering
- `config.json` file loading
- load and save functionality
- logging and error fallbacks

## How to use

Clone the repository, then update the `main.py` file with your own code.

### WASM builds

To build the WebAssembly build of the game, install pygbag, then run:

python -m pygbag .

The game should run on `localhost:8000`.

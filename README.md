# Tile-Game

A tile-based multiplayer game with procedural terrain generation (using the Perlin Noise algorithm).

Currently in development.

Pre-release **v0.0.1a** is now **[available](https://github.com/SammygoodTunes/Tile-Game/releases/tag/alpha)**.

## Table of contents:
- [Preview](#preview)
- [Controls](#controls)
- [Setup](#setup)
  - [Debug mode](#debug-mode)
- [Documentation](#documentation)
- [Information](#information)
  - [Contributors](#contributors-a-z-)
  - [Credits](#credits)

## Preview

![Preview](https://raw.githubusercontent.com/SammygoodTunes/Tile-Game/main/docs/ss.png)

[*Back to TOC*](#table-of-contents)

## Controls

| Key(s)                            | Action                  |
|-----------------------------------|-------------------------|
| <kbd>Z/Q/S/D</kbd>                | Move player (temporary) |
| LMB                               | Break breakable tiles   |
| Mouse Wheel                       | Switch item in hotbar   |
| <kbd>Space</kbd>                  | Show map                |
| <kbd>Esc</kbd>                    | Pause menu/Main menu    |
| <kbd>Alt</kbd> + <kbd>Enter</kbd> | Fullscreen mode         |

[*Back to TOC*](#table-of-contents)

## Setup

> **<ins>Requires:</ins>** Python 3.11 or later
> 
> Before installing the necessary modules, it is recommended to set up a virtual environment. This allows for a clean workspace and avoids installing packages to your global environment.

Set up a new virtual environment. For the sake of conventions, we'll call ours `venv`:

```bash
python -m venv venv   # Windows
python3 -m venv venv  # MacOS / Unix	
```

Activate it using:

```bash
venv\Scripts\activate     # Windows
source venv/bin/activate  # MacOS / Unix
```

In order to install the necessary modules, Poetry is required. You can install it using the following:

```bash
pip install poetry
```

Install the pre-requisites:

```bash
poetry install
```

> If you prefer not to install the development dependencies, then feel free to use the ```--only main``` flag.

Run the game using:

```bash
python -m game  # Windows
python3 -m game # MacOS / Unix
```

### Debug mode

If you wish to launch the game with extra debugging information, use the `--debug` or `-d` flag:

```bash
python -m game --debug   # Windows
python3 -m game --debug  # MacOS / Unix
```

> Note that using this mode will significantly impact the performance of the game, and therefore should not be used when playing normally.

[*Back to TOC*](#table-of-contents)

## Documentation

Documentation for this repository has been generated by Doxygen.

To view the HTML version, you must run the following URL address in the browser of your choosing:

`file:///[path/to/repo]/docs/game/html/index.html`

[*Back to TOC*](#table-of-contents)

## Information

Current Game Version: [v0.0.1a](https://github.com/SammygoodTunes/Tile-Game/releases/tag/alpha)

---

### Contributors [A-Z]: 
- [Jatzylap](https://github.com/Jatzylap/) (art, alpha-testing)
- Pickmonde (art)

### Credits:
- Original ["Pixeled"](https://www.dafont.com/pixeled.font) typeface by OmegaPC777 
  - Edited to support more characters

Developed by [SammygoodTunes](https://github.com/SammygoodTunes)

Tested on Debian 12 and Windows 10

Libraries used: Pygame 2.6.1, Numpy 1.26.4

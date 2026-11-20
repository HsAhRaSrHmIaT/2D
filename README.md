# Bounce Harmony

Bounce Harmony is a small 2D physics and music game. A double pendulum swings
through rings of blocks, and each block it hits falls into a V-shaped funnel
and plays a synthesized note.

## Requirements

- Python 3.13
- A desktop environment capable of opening a Pygame window

The game uses Pygame for graphics and audio, NumPy to generate note samples,
and Pymunk for the falling-block physics.

## Install and run on Windows

Open PowerShell in the project folder (the folder containing `app.py` and this
README), then create and activate a virtual environment:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install the dependencies and start the game:

```powershell
python -m pip install --upgrade pip
python -m pip install pygame numpy pymunk
python app.py
```

If PowerShell blocks the activation script, allow it for the current terminal
session and activate again:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

If `py -3.13` is not recognized, install Python 3.13 and make sure the Python
Launcher is available. You can check installed Python versions with `py -0p`.

## Install and run on macOS or Linux

From the project folder, create and activate a virtual environment:

```bash
python3.13 -m venv .venv
source .venv/bin/activate
```

Install the dependencies and run the game:

```bash
python -m pip install --upgrade pip
python -m pip install pygame numpy pymunk
python app.py
```

## Playing

The simulation starts automatically. Close the game window to exit.
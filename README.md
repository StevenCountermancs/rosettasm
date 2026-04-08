# RosettASM

RosettASM is a pedagogical system for visualizing how high-level code executes at the machine level.

## Features

- Custom high-level language
- Compilation to x86 assembly
- Step-by-step execution visualization
- Register and stack tracking
- Interactive GUI built with PyQt

## Running the Application

### Option 1: Executable
Download the latest release and run `RosettASM.exe`.

### Option 2: From Source
```bash
python launch_rosettasm.py
```

## Usage

See full guide:
- [How to Use](rosettasm/docs/how_to_use.md)
- [Language Specification](rosettasm/docs/language_spec_v1.md)

## Project Structure

- `rosettasm/` – core compiler, UI, and execution engine
- `launch_rosettasm.py` – application entry point
- `docs/` – documentation files

## Technologies

- Python
- PyQt6
- QScintilla
- x86 Assembly (educational model)

## Motivation

RosettASM was designed to help students understand how high-level code translates to machine-level execution by making program behavior visible and interactive.

## Dependencies & Licensing

This project uses the following open-source libraries:

- PyQt (GPL licensed)
- QScintilla (GPL licensed)

RosettASM is distributed for educational purposes and includes source code in compliance with GPL requirements.

For more information:
- https://www.riverbankcomputing.com/software/pyqt/
- https://www.riverbankcomputing.com/software/qscintilla/

# Installation

## Using the packaged application (recommended)
1. Download the compressed zip from the `release` folder for your operating system. This is `release/windows.zip` for Windows and `release/linux.zip` for Linux. For macOS, you must build the application yourself.
2. Extract it then run the executable `Not so Dead Cells` to run the game.

## Building from source

> Requires Python 3.12 or newer. This will NOT work with any version of python 2 or below 3.12.

1. Clone this repo and open a terminal in the folder.
2. Run `python3 -m venv .venv` to create a virtual environment.
3. Activate the venv using `. .venv/bin/activate` if on Linux or macOS. If using `fish` shell, use `activate.fish` instead. If on Windows, use `.venv/Scripts/activate`.
4. Install the dependencies via `pip install -r requirements.txt` and `pyinstaller` using `pip install -U pyinstaller`.
5. Package the application using `pyinstaller main.spec`. There should now be a `dist` folder and `build` folder.
6. Run the application via the `main` executable in the `dist` folder. The folder and executable can be renamed as you wish.

## Troubleshooting
If you get permission denied error when running the executable on macOS or Linux, use `chmod +x <FILE_NAME>` (where `<FILE_NAME>` is the name of the executable file) to give the file execute permission for all users.

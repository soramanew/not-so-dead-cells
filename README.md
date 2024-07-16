# Installation

## Using the packaged application (recommended)
1. Download the compressed tarball from the `release` folder for your operating system. This is `release/windows.tar.gz` for Windows and `release/linux.tar.gz` for Linux. For macOS, you must build the application yourself.
2. Extract it then run the executable `Not so Dead Cells` to run the game.

## Building from source

> Requires Python 3.12 or newer. This will NOT work with any version of python 2 or below 3.12.

1. Clone this repo
    ```sh
    git clone https://github.com/soramanew/not-so-dead-cells.git
    ```
2. Run `install.bat` if on Windows otherwise `install.sh`
3. If the install script didn't work:
    1. Open a terminal in the folder
    2. Create a virtual environment
        ```sh
        python3 -m venv .venv
        ```
    3. Activate the venv
        ```sh
        . .venv/bin/activate  # Linux or macOS (.fish if using fish shell, .csh for c shell)
        .venv/Scripts/activate  # Windows
        ```
    4. Install dependencies and `pyinstaller`
        ```sh
        pip install -r requirements.txt
        pip install -U pyinstaller
        ```
    5. Package the application
        ```sh
        pyinstaller main.spec
        ```
4. Run the application via the executable in the `dist/main` folder (`Not so Dead Cells` if using the install script otherwise `main`). The folder and executable can be renamed as you wish.

# Updating

## Using the packaged application (recommended)
Download the new release and replace the old release.

## Building from source

> The install script requires git in the PATH for updating.

Just run the install script again.
If it doesn't work, use `git pull origin master` or re-download the repo then build it again manually.

# Troubleshooting
If you get permission denied error when running the executable on macOS or Linux, use `chmod u+x <FILE_NAME>` (where `<FILE_NAME>` is the name of the executable file) to give the file execute permission for the current user.

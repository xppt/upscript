Upscript
===

This cli tool installs and updates python scripts for you.

Tested on: Linux, Windows.

Install
---
`pip install --user upscript`

Usage
---
`upscript fetch <name> [<destination-dir>] [--index-url <index-url>]`

This command will create a folder with all the package's console entry points.
There also will be `.files/` folder inside it, containing embedded venv.

Any time you'll start some of these entry point, upscript will check for a package update in an index. It is possible
to suppress an update check via `UPSCRIPT_AUTO_UPDATE=0` env-var.

"""
Thin source-tree launcher.

Use this before installing the package, or install with `pip install -e .` and
run the shorter `exactbt search ...` command.
"""

from exactbt.cli import main

if __name__ == "__main__":
    main()

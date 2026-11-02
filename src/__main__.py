"""Permite ejecutar la aplicación con ``python -m src``."""

import sys

from .controller.app import main


if __name__ == "__main__":
    sys.exit(main())

"""Punto de entrada y composición de la aplicación MVC."""

import sys

from PyQt6.QtWidgets import QApplication

from src.view.main_window import MainWindow


def main(argv=None):
    """Crea la aplicación, carga el archivo opcional y ejecuta Qt."""
    args = sys.argv if argv is None else argv
    app = QApplication(args)
    win = MainWindow()
    if len(args) > 1:
        win.open_path(args[1])
    win.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())

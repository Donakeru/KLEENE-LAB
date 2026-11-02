"""Controladores de la aplicación."""

from .automata_controller import AutomataController


def main(argv=None):
    """Compatibilidad para invocar el punto de entrada del controlador."""
    from .app import main as run
    return run(argv)


__all__ = ["AutomataController", "main"]

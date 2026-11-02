"""Fachada de compatibilidad para la conversión de ER a autómata."""

from .re_to_af import ErrorSintaxis, regex_to_automaton


def regex_a_automata(texto):
    """Alias histórico de ``regex_to_automaton``."""
    return regex_to_automaton(texto)


def automata_a_regex(automata):
    """Punto de extensión para la conversión de autómata a ER."""
    raise NotImplementedError("automata_a_regex: pendiente de implementar")


__all__ = [
    "ErrorSintaxis",
    "automata_a_regex",
    "regex_a_automata",
    "regex_to_automaton",
]

"""Fachada de compatibilidad para la conversión entre ER y autómatas."""

from .af_to_re import automaton_to_regex
from .re_to_af import ErrorSintaxis, regex_to_automaton


def regex_a_automata(texto):
    """Alias histórico de ``regex_to_automaton``."""
    return regex_to_automaton(texto)


def automata_a_regex(automata):
    """Convierte un ``Automata`` en su ER equivalente (lema de Arden)."""
    return automaton_to_regex(automata)


__all__ = [
    "ErrorSintaxis",
    "automata_a_regex",
    "regex_a_automata",
    "regex_to_automaton",
]

"""
Freedeon Engine v0.1

Validación operacional de la ontología de Phase 16 (Topology of State Space).

Connectivity, Reachability y Discoverability son tres preguntas distintas
y permanecen desacopladas en código:

    exists_path(A, B)                  -> Connectivity   (objetiva)
    can_reach(eon, A, B)                -> Reachability   (Capability)
    can_discover(eon, info_set, A, B)   -> Discoverability (Knowledge)

Invariante: can_discover() NUNCA llama a exists_path().
"""

from dataclasses import dataclass, field
from typing import Callable, List, Set


# ---------------------------------------------------------------------------
# ENTIDADES
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class State:
    id: str


@dataclass(frozen=True)
class Transition:
    from_state: str
    to_state: str
    required_capability: str = None  # capability necesaria para recorrerla


@dataclass(frozen=True)
class Information:
    id: str
    content: str


# inference_rule: (known_information, from_id, to_id) -> bool
InferenceRule = Callable[[Set[Information], str, str], bool]


@dataclass
class EON:
    capabilities: Set[str] = field(default_factory=set)
    known_information: Set[Information] = field(default_factory=set)
    inference_rules: List[InferenceRule] = field(default_factory=list)


# ---------------------------------------------------------------------------
# FUNCIONES
# ---------------------------------------------------------------------------

def exists_path(transitions: List[Transition], a: str, b: str) -> bool:
    """Connectivity. Solo State + Transition. No recibe EON."""
    if a == b:
        return True
    adjacency = {}
    for t in transitions:
        adjacency.setdefault(t.from_state, set()).add(t.to_state)

    visited = {a}
    frontier = [a]
    while frontier:
        current = frontier.pop()
        for neighbor in adjacency.get(current, ()):
            if neighbor == b:
                return True
            if neighbor not in visited:
                visited.add(neighbor)
                frontier.append(neighbor)
    return False


def can_reach(eon: EON, transitions: List[Transition], a: str, b: str) -> bool:
    """
    Reachability. Depende del State Space + eon.capabilities.
    Recorre el grafo verificando, en cada paso, que el EON tenga la
    capability requerida por esa Transition.
    """
    if a == b:
        return True
    adjacency = {}
    for t in transitions:
        adjacency.setdefault(t.from_state, []).append(t)

    visited = {a}
    frontier = [a]
    while frontier:
        current = frontier.pop()
        for t in adjacency.get(current, ()):
            if t.required_capability is not None and t.required_capability not in eon.capabilities:
                continue  # el EON no puede recorrer esta transición
            if t.to_state == b:
                return True
            if t.to_state not in visited:
                visited.add(t.to_state)
                frontier.append(t.to_state)
    return False


def can_discover(eon: EON, information_set: Set[Information], a: str, b: str) -> bool:
    """
    Discoverability. Depende de Information + eon.known_information +
    eon.inference_rules. NO llama a exists_path().
    """
    knowable = eon.known_information & information_set
    return any(rule(knowable, a, b) for rule in eon.inference_rules)
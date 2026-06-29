"""
scenario.py — Demo scenario for State Space Visualizer v0.1

This file defines a concrete State/Transition/Information/EON setup
using the classes from engine.py. It introduces no new ontology: no
new functions, no new rules about what connectivity, reachability,
or discoverability mean. It only instantiates data.

Graph: A - B - C | D   (D is disconnected => Abyss)

Information content is structured as "claims_path:<from>:<to>" so that
inference rules can check whether a piece of information actually
refers to the (a, b) pair being asked about. This matters: a rule
that ignores (a, b) can't make a real claim about any specific path
-- it can only be universally credulous, which isn't an epistemic
position about anything in particular. See ARCHITECTURE_NOTES.md.

EON "Wanderer"  -- Test Visual 001
    Lacks the "jump" capability needed for A->B, so it cannot
    physically reach B or C. But it knows accurate information
    that specifically claims a path from A to C, and its inference
    rule correctly checks that the information names this exact
    pair. Result for A->C: can_reach=False, can_discover=True.
    This isolates Discoverability from Reachability for one
    specific, correctly-evaluated pair -- nothing more.

EON "Capable"
    Has the "jump" capability, can physically traverse A->B->C,
    has no information and never infers anything. Demonstrates
    Reachable without needing Discoverability at all.

EON "Blind"
    Has the capability but no inference_rules at all: cannot
    discover anything, only reach what it can physically reach.

EON "Misled"  -- Error Epistemologico (separate from Test Visual 001)
    Destination-aware and methodologically sound (it correctly
    checks that information names the (a, b) pair in question),
    but the information itself is false: it knows a claim that
    specifically names A->D, and D is actually unreachable by any
    path (Abyss). Result for A->D: exists_path=False, can_discover=True.
    This is the real Discoverability != Truth case: the rule isn't
    sloppy, the world just didn't match the belief.
"""

states = [
    State("A"),
    State("B"),
    State("C"),
    State("D"),
    State("E"),
    State("F"),
    State("G"),
]

transitions = [
    Transition("A", "B", required_capability="jump"),
    Transition("B", "C"),
    Transition("A", "E", required_capability="jump"),
    Transition("E", "F"),
    Transition("B", "G"),
]

info_af = Information(
    id="info_af",
    content="claims_path:A:F"
)

information_set = {info_af}

def _claims_pair(info, a, b):
    return info.content == f"claims_path:{a}:{b}"


def rule_destination_aware(known, a, b):
    """Infers a path exists only if known information specifically
    names this (a, b) pair. Does not consult exists_path."""
    return any(_claims_pair(info, a, b) for info in known)


def rule_never_infers(known, a, b):
    return False


eons = {
    "ALPHA": EON(
        capabilities=set(),
        known_information=set(),
        inference_rules=[rule_never_infers],
    ),

    "BETA": EON(
        capabilities={"jump"},
        known_information=set(),
        inference_rules=[rule_never_infers],
    ),

    "GAMMA": EON(
        capabilities=set(),
        known_information={info_af},
        inference_rules=[rule_destination_aware],
    ),
}

state_ids = [s.id for s in states]

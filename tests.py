"""
Tests — Phase 16.
Validan que Connectivity != Reachability != Discoverability
permanecen separados en código.
"""

from engine import State, Transition, Information, EON, exists_path, can_reach, can_discover


def test_1_ghost_entity():
    """exists_path(A,B) == True, can_reach(EON,A,B) == False."""
    transitions = [Transition("A", "B", required_capability="fly")]
    eon = EON(capabilities=set())  # no tiene "fly"

    assert exists_path(transitions, "A", "B") is True
    assert can_reach(eon, transitions, "A", "B") is False
    print("Test 1 — Ghost Entity: OK")


def test_2_inferencia_ciega():
    """Information existe, pero inference_rules son insuficientes -> can_discover == False."""
    info_ab = Information(id="info_ab", content="existe un camino de A a B")
    information_set = {info_ab}

    def rule_insuficiente(known, a, b):
        return False  # ninguna regla logra confirmar el camino

    eon = EON(
        known_information={info_ab},  # la conoce, pero no alcanza
        inference_rules=[rule_insuficiente],
    )

    assert can_discover(eon, information_set, "A", "B") is False
    print("Test 2 — Inferencia Ciega: OK")


def test_3_matematico_perfecto():
    """Information disponible, inference_rules suficientes -> can_discover == True."""
    info_ab = Information(id="info_ab", content="existe un camino de A a B")
    information_set = {info_ab}

    def rule_suficiente(known, a, b):
        return any(i.id == "info_ab" for i in known)

    eon = EON(
        known_information={info_ab},
        inference_rules=[rule_suficiente],
    )

    assert can_discover(eon, information_set, "A", "B") is True
    print("Test 3 — Matemático Perfecto: OK")


def test_4_abyss():
    """exists_path(A,B) == False."""
    transitions = [Transition("A", "C"), Transition("C", "D")]

    assert exists_path(transitions, "A", "B") is False
    print("Test 4 — Abyss: OK")


def test_2b_sin_exposure():
    """
    Information ≠ Knowledge.
    information_set tiene info relevante sobre A->B, inference_rules son
    válidas y suficientes, pero eon.known_information está vacío (el EON
    nunca tuvo Exposure). Esperado: can_discover == False.
    """
    info_ab = Information(id="info_ab", content="existe un camino de A a B")
    information_set = {info_ab}  # existe objetivamente

    def rule_valida(known, a, b):
        return any(i.id == "info_ab" for i in known)

    eon = EON(
        known_information=set(),  # sin Exposure: nunca llegó al EON
        inference_rules=[rule_valida],
    )

    assert can_discover(eon, information_set, "A", "B") is False
    print("Test 2B — Sin Exposure: OK")


def test_5_error_epistemologico():
    """
    Discoverability != Truth.
    exists_path(A,B) == False en el tablero real, pero information_set
    contiene información incorrecta (afirma que A->B existe), el EON la
    conoce, y sus inference_rules le permiten inferir el camino.
    Esperado: exists_path == False, can_discover == True.
    """
    transitions = [Transition("A", "C")]  # no hay transición real A->B

    info_falsa = Information(id="info_falsa_ab", content="rumor: A conecta con B")
    information_set = {info_falsa}

    def rule_credula(known, a, b):
        return any(i.id == "info_falsa_ab" for i in known)

    eon = EON(
        known_information={info_falsa},
        inference_rules=[rule_credula],
    )

    real = exists_path(transitions, "A", "B")
    inferido = can_discover(eon, information_set, "A", "B")

    assert real is False
    assert inferido is True
    print("Test 5 — Error Epistemológico: OK (exists_path=False, can_discover=True)")


if __name__ == "__main__":
    test_1_ghost_entity()
    test_2_inferencia_ciega()
    test_2b_sin_exposure()
    test_3_matematico_perfecto()
    test_4_abyss()
    test_5_error_epistemologico()
    print("\nTodos los tests pasaron. Connectivity, Reachability y Discoverability permanecen desacoplados.")
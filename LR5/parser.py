from pathlib import Path
import json
import numpy
from components.elements import Resistor, Inductor, Capacitor, VoltageSource, CurrentSource

def make_component(cfg, dt):
    t = cfg.get("type")
    b = cfg.get("branch")
    nb = cfg.get("node_begin")
    ne = cfg.get("node_end")

    # Берём первую букву типа, чтобы игнорировать порядковые номера (R1, E2 -> R, E)
    base_type = t[0].upper() if t else ""

    if base_type == "R":
        R_val = cfg.get("resistance") or cfg.get("R", 1.0)
        return Resistor(b, nb, ne, R_val)
        
    elif base_type == "L":
        L_val = cfg.get("inductance") or cfg.get("L", 1e-3)
        return Inductor(b, nb, ne, L_val, dt)
        
    elif base_type == "C":
        C_val = cfg.get("capacitance") or cfg.get("C", 1e-6)
        return Capacitor(b, nb, ne, C_val, dt)
        
    elif base_type in ("E", "V"):
        return VoltageSource(
            b, nb, ne,
            voltage = cfg.get("voltage", 0.0),
            frequency = cfg.get("frequency", 0.0),
            phase_deg = cfg.get("phase_deg", 0.0),
            r_internal = cfg.get("impedans") or cfg.get("r_internal", 1e-10)
        )
        
    elif base_type == "J":
        return CurrentSource(b, nb, ne, cfg.get("current", 0.0))

def Parser(path):
    file_path = Path(path)
    if not file_path.is_absolute():
        file_path = Path(__file__).parent / "tests" / file_path

    if not file_path.exists():
        raise FileNotFoundError(f"Файл схемы не найден: {file_path}")

    with open(file_path, "r", encoding = "utf-8") as f:
        data = json.load(f)

    dt = float(data["dt"])
    n_nodes = int(data["nodes"])
    n_free_nodes = n_nodes - 1  # исключаем узел земли (0)

    components = []
    for element_json in data["elements"]:
        components.append(make_component(element_json, dt))

    n_branches = len(components)

    # Матрица инцидентности A: строки - ветви, столбцы - узлы (без земли)
    A = numpy.zeros((n_branches, n_free_nodes), dtype = int)
    for i, elem in enumerate(components):
        nb = elem.get_node_begin()
        ne = elem.get_node_end()
        if nb != 0:
            A[i, nb - 1] = 1   # ветвь выходит из узла
        if ne != 0:
            A[i, ne - 1] = -1  # ветвь входит в узел

    # Диагональная матрица проводимостей ветвей Y
    Y = numpy.zeros((n_branches, n_branches), dtype = float)
    for i, elem in enumerate(components):
        R = elem.get_R()
        # Защита от деления на ноль (актуально для идеальных источников)
        Y[i, i] = 1.0 / R if R != 0 else 0.0

    # Вектор ЭДС ветвей E
    E = numpy.zeros((n_branches, 1), dtype = float)
    for i, elem in enumerate(components):
        E[i, 0] = elem.get_E()

    # Вектор токовых источников ветвей J
    J = numpy.zeros((n_branches, 1), dtype = float)
    for i, elem in enumerate(components):
        J[i, 0] = elem.get_J()

    return A, Y, E, J, components, dt
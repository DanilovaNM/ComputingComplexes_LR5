from math import pi, sin
from abc import ABC, abstractmethod

class Element(ABC):
    def __init__(self, branch, node_begin, node_end):
        self.branch = branch
        self.node_begin = node_begin  # начальный узел
        self.node_end = node_end      # конечный узел
        self.fi_begin = 0.0           # потенциал начального узла
        self.fi_end = 0.0             # потенциал конечного узла
        self.current = 0.0            # ток через ветвь

    @abstractmethod
    def get_E(self): pass

    @abstractmethod
    def get_R(self): pass

    @abstractmethod
    def get_J(self): pass

    def update(self): pass

    # --- Геттеры и сеттеры ---
    def set_fi_begin(self, value): self.fi_begin = value
    def set_fi_end(self, value): self.fi_end = value
    def set_current(self, value): self.current = value

    def get_node_begin(self): return self.node_begin
    def get_node_end(self): return self.node_end
    def get_branch(self): return self.branch
    def get_current(self): return self.current
    def get_fi_begin(self): return self.fi_begin
    def get_fi_end(self): return self.fi_end


class Resistor(Element):
    def __init__(self, branch, node_begin, node_end, R):
        super().__init__(branch, node_begin, node_end)
        self.R = R

    def get_E(self): return 0.0
    def get_R(self): return self.R
    def get_J(self): return 0.0
    def update(self): pass


class Inductor(Element):
    def __init__(self, branch, node_begin, node_end, L, dt):
        super().__init__(branch, node_begin, node_end)
        self.L = L
        self.dt = dt
        self.E_L = 0.0

    def get_E(self): return self.E_L
    def get_R(self): return 2 * self.L / self.dt
    def get_J(self): return 0.0

    def update(self):
        # Метод трапеций: расчёт эквивалентной ЭДС для следующего шага
        U_L = self.fi_begin - self.fi_end
        self.E_L = (2 * self.L / self.dt) * self.current + U_L


class Capacitor(Element):
    def __init__(self, branch, node_begin, node_end, C, dt):
        super().__init__(branch, node_begin, node_end)
        self.C = C
        self.dt = dt
        self.E_C = 0.0

    def get_E(self): return self.E_C
    def get_R(self): return self.dt / (2 * self.C)
    def get_J(self): return 0.0

    def update(self):
        # Метод трапеций: расчёт эквивалентной ЭДС для следующего шага
        U_C = self.fi_begin - self.fi_end
        self.E_C = -(self.dt / (2 * self.C) * self.current + U_C)


class VoltageSource(Element):
    def __init__(self, branch, node_begin, node_end,
                 voltage, frequency = 0.0, phase_deg = 0.0,
                 r_internal = 1e-10):
        super().__init__(branch, node_begin, node_end)
        self.volt = voltage
        self.freq = frequency
        self.phase = phase_deg * pi / 180  # перевод градусов в радианы
        self.r_int = r_internal
        self.time = 0.0

    def get_E(self):
        if self.freq == 0:
            return self.volt
        return self.volt * sin(2 * pi * self.freq * self.time + self.phase)

    def get_R(self): return self.r_int
    def get_J(self): return 0.0

    def set_time(self, t): self.time = t
    def update(self): pass


class CurrentSource(Element):
    def __init__(self, branch, node_begin, node_end, current):
        super().__init__(branch, node_begin, node_end)
        self.J0 = current

    def get_E(self): return 0.0
    def get_R(self): return 1e10  # большое сопротивление для аппроксимации ИТ
    def get_J(self): return self.J0
    def update(self): pass
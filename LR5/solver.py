import numpy as np
from components.elements import VoltageSource  # проверьте путь импорта в вашем проекте

class DommelSolver:
    def __init__(self, A, Y, E, J, components, dt):
        self.A = A.copy()
        self.Y = Y.copy()          # диагональная матрица проводимостей ветвей
        self.E_ref = E.copy()
        self.J_ref = J.copy()
        self.components = components
        self.dt = dt
        self.t = 0.0

        self.nb = A.shape[0]       # кол-во ветвей
        self.nn = A.shape[1]       # кол-во узлов (без земли)

        # Узловая матрица проводимостей: G = A^T * Y * A
        # Вычисляется один раз, т.к. топология и dt не меняются
        self.G = self.A.T @ self.Y @ self.A

    def step(self):
        """Выполняет один шаг расчёта по времени."""
        self.t += self.dt

        # 1. Обновляем время для переменных источников ЭДС
        for comp in self.components:
            if isinstance(comp, VoltageSource):
                comp.set_time(self.t)

        # 2. Формируем векторы E и J на текущий момент времени t
        E = np.zeros((self.nb, 1), dtype=float)
        J = np.zeros((self.nb, 1), dtype=float)
        for i, comp in enumerate(self.components):
            E[i, 0] = comp.get_E()
            J[i, 0] = comp.get_J()

        # 3. Правая часть СЛАУ: b = -A^T * (J + Y * E)
        # Уравнение узлов: G * U_node = b
        rhs = -self.A.T @ (J + self.Y @ E)

        # 4. Решаем СЛАУ
        try:
            U_node = np.linalg.solve(self.G, rhs)
        except np.linalg.LinAlgError:
            raise ValueError("Матрица G вырождена. Проверьте заземление цепи или наличие изолированных узлов.")

        # 5. Находим напряжения и токи ветвей
        U_branch = self.A @ U_node               # U_branch = A * U_node
        I_branch = self.Y @ (E + U_branch) + J   # I_branch = Y*(E+U) + J

        # Преобразуем к 1D массивам
        U_node_flat = U_node.flatten()
        I_branch_flat = I_branch.flatten()

        # 6. Обновляем состояния элементов
        for i, comp in enumerate(self.components):
            nb = comp.get_node_begin()
            ne = comp.get_node_end()

            # Потенциалы (0.0 для узла земли)
            v_begin = U_node_flat[nb - 1] if nb != 0 else 0.0
            v_end   = U_node_flat[ne - 1] if ne != 0 else 0.0

            comp.set_fi_begin(v_begin)
            comp.set_fi_end(v_end)
            comp.set_current(I_branch_flat[i])

        # 7. Обновляем историю (компенсационные ЭДС/токи для следующего шага)
        for comp in self.components:
            comp.update()

        return U_node_flat, I_branch_flat

    def get_time(self): return self.t
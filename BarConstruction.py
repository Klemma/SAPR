import numpy as np


class BarConstruction:
    def __init__(self):
        self.bars = []
        self.forces = []
        self.terminations = {"left": True, "right": True}
        self.movements_vector = None
        self.computed = False

    def add_bar(self, properties: dict):
        self.bars.append(properties)
        if len(self.bars) == 1:
            self.forces.extend([0, 0])
        else:
            self.forces.append(0)
        self.computed = False

    def del_bar(self):
        if self.bars:
            self.bars.pop()
            if len(self.bars) > 0:
                self.forces.pop()
            else:
                self.forces.clear()
            self.computed = False

    def change_force(self, node: int, force: float):
        if self.bars:
            self.forces[node - 1] = force
            self.computed = False

    def change_terminations(self, terminations: dict):
        self.terminations = terminations
        self.computed = False

    def compute_movements_vector(self):
        if self.computed:
            return

        E = np.array([properties['E'] for properties in self.bars])
        L = np.array([properties['L'] for properties in self.bars])
        A = np.array([properties['A'] for properties in self.bars])
        F = np.array(self.forces)
        q = np.array([properties['q'] for properties in self.bars])
        nodes_count = len(self.bars) + 1
        reactions_matrix = np.zeros((nodes_count, nodes_count))
        reactions_vector = np.zeros((nodes_count, 1))

        for i in range(nodes_count - 1):
            for j in range(i, i + 2):
                for k in range(i, i + 2):
                    if j != k:
                        reactions_matrix[j, k] -= E[i] * A[i] / L[i]
                    else:
                        reactions_matrix[j, k] += E[i] * A[i] / L[i]

        for i in range(nodes_count):
            reactions_vector[i] = F[i]

        for i in range(nodes_count - 1):
            L = np.array([properties['L'] for properties in self.bars])
            reactions_vector[i] += q[i] * L[i] / 2
            reactions_vector[i + 1] += q[i] * L[i] / 2

        if self.terminations["left"]:
            reactions_matrix[0, 1:] = 0
            reactions_matrix.transpose()[0, 1:] = 0
            reactions_vector[0] = 0
        if self.terminations["right"]:
            reactions_matrix[-1, :-1] = 0
            reactions_matrix.transpose()[-1, :-1] = 0
            reactions_vector[-1] = 0

        self.movements_vector = np.linalg.solve(reactions_matrix, reactions_vector)
        print("Вектор перемещений:\n", self.movements_vector, '\n')
        self.computed = True

    def compute_Nx(self, n_bar: int, x: float) -> float:
        E = np.array([properties['E'] for properties in self.bars])[n_bar]
        L = np.array([properties['L'] for properties in self.bars])[n_bar]
        A = np.array([properties['A'] for properties in self.bars])[n_bar]
        q = np.array([properties['q'] for properties in self.bars])[n_bar]
        U = self.movements_vector

        Nx = (E * A / L) * (U[n_bar + 1] - U[n_bar]) + (q * L / 2) * (1 - 2 * x / L)
        return np.round(Nx[0], 4)

    def compute_Ux(self, n_bar: int, x: float) -> float:
        E = np.array([properties['E'] for properties in self.bars])[n_bar]
        L = np.array([properties['L'] for properties in self.bars])[n_bar]
        A = np.array([properties['A'] for properties in self.bars])[n_bar]
        q = np.array([properties['q'] for properties in self.bars])[n_bar]
        U = self.movements_vector

        Ux = U[n_bar] + (x / L) * (U[n_bar + 1] - U[n_bar]) + ((q * L ** 2 * x) / (2 * E * A * L)) * (1 - x / L)
        return np.round(Ux[0], 4)

    def compute_Sx(self, n_bar: int, x: float) -> float:
        Nx = self.compute_Nx(n_bar, x)
        A = np.array([properties['A'] for properties in self.bars])[n_bar]

        Sx = Nx / A
        return np.round(Sx, 4)

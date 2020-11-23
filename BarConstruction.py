class BarConstruction:
    def __init__(self):
        self.bars = []
        self.forces = []
        self.terminations = {"left": True, "right": True}

    def add_bar(self, properties: dict):
        self.bars.append(properties)
        if len(self.bars) == 1:
            self.forces.extend([0, 0])
        else:
            self.forces.append(0)

    def del_bar(self):
        if self.bars:
            self.bars.pop()
            if len(self.bars) > 0:
                self.forces.pop()
            else:
                self.forces.clear()

    def change_force(self, node: int, force: float):
        print(self.forces)
        if self.bars:
            self.forces[node - 1] = force

    def change_terminations(self, terminations: dict):
        self.terminations = terminations

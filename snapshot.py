import copy

class SnapshotSimulacao:
    def __init__(self, relogio, processadores, tarefas, fila_prontos):
        self.relogio = relogio
        # UMA chamada para o conjunto, o mesmo TCB continua sendo um objeto só
        self.processadores, self.tarefas, self.fila_prontos = copy.deepcopy(
            (processadores, tarefas, fila_prontos))

    def copiar_estado(self):
        return copy.deepcopy((self.processadores, self.tarefas, self.fila_prontos))
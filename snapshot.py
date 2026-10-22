import copy

class SnapshotSimulacao:
    """
    Guarda uma cópia completa do estado do simulador num determinado tick.
    Útil para permitir que o usuário volte no tempo ou edite cenários sem perder o que já foi feito.
    """
    def __init__(self, relogio, processadores, tarefas, fila_prontos):
        self.relogio = relogio
        # Cria uma cópia profunda (deep copy) para isolar os objetos do estado atual
        self.processadores, self.tarefas, self.fila_prontos = copy.deepcopy(
            (processadores, tarefas, fila_prontos))

    def copiar_estado(self):
        # Retorna uma cópia independente de todo o estado guardado neste snapshot
        return copy.deepcopy((self.processadores, self.tarefas, self.fila_prontos))
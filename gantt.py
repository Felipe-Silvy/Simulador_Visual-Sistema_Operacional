class EventoGantt:
    def __init__(self, tipo, tempo_inicio, tempo_fim, cpu_id=None, houve_sorteio=False):
        self.tipo = tipo                    # "EXECUCAO", "CHEGADA", "FIM", ...
        self.tempo_inicio = tempo_inicio    # instante em que começou
        self.tempo_fim = tempo_fim          # instante em que acabou
        self.cpu_id = cpu_id                # em qual CPU (None se não se aplica)
        self.houve_sorteio = houve_sorteio  # True se um sorteio escolheu esta tarefa
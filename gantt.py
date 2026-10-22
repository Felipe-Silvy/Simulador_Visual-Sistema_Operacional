class EventoGantt:
    """
    Representa um evento ocorrido no gráfico de Gantt da simulação,
    permitindo rastrear o histórico visual e temporal das tarefas.
    """
    def __init__(self, tipo, tempo_inicio, tempo_fim, cpu_id=None, houve_sorteio=False):
        self.tipo = tipo                    # Tipo do evento (ex: "EXECUCAO", "CHEGADA", "FIM", "DEADLINE_MISS", etc.)[cite: 6]
        self.tempo_inicio = tempo_inicio    # Instante de tempo (tick) em que o evento começou[cite: 6]
        self.tempo_fim = tempo_fim          # Instante de tempo (tick) em que o evento terminou[cite: 6]
        self.cpu_id = cpu_id                # Identificador da CPU onde ocorreu (None se não alocado a uma CPU)[cite: 6]
        self.houve_sorteio = houve_sorteio  # Booleano indicando se a tarefa foi escolhida através de um sorteio[cite: 6]
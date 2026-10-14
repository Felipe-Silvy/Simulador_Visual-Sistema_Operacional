from gantt import EventoGantt

class TCB:
    def __init__(self, id, cor, ingresso, duracao, periodo, prazo, eventos):
        # Dados "Estáticos"
        self.id = id
        self.cor = cor
        self.ingresso = ingresso
        self.duracao = duracao
        self.periodo = periodo
        self.prazo = prazo
        self.eventos = eventos   # fica guardado para o Projeto B

        # Estado da simulação (muda a cada tick) 
        self.estado = "AGUARDANDO"    # AGUARDANDO, PRONTA, EXECUTANDO ou TERMINADA
        self.tempo_executado = 0      # ticks de CPU já usados na instância atual
        self.deadline_absoluto = 0    # instante limite da instância atual
        self.execucoes_concluidas = 0 # instâncias terminadas (para no 10 [req. 4.4])
        self.historico_eventos = []   # eventos para o Gantt (chegada, execução, fim...)
        
    def ativar_tarefa(self, tempo):
        # Começa uma nova rodada (ativação) desta tarefa (é periódica)
        self.estado = "PRONTA"
        self.tempo_executado = 0
        self.deadline_absoluto = tempo + self.prazo

    def adicionar_evento(self, tipo, tempo_inicio, tempo_fim, cpu_id=None, houve_sorteio=False):
        self.historico_eventos.append(EventoGantt(tipo, tempo_inicio, tempo_fim, cpu_id, houve_sorteio))
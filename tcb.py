from gantt import EventoGantt

class TCB:
    """
    Bloco de Controlo de Tarefa (Task Control Block).
    Armazena todas as informações estáticas e o estado atual de execução de cada tarefa.
    """
    def __init__(self, id, cor, ingresso, duracao, periodo, prazo, eventos):
        # Configurações básicas informadas no arquivo de entrada
        self.id = id
        self.cor = cor
        self.ingresso = ingresso
        self.duracao = duracao
        self.periodo = periodo
        self.prazo = prazo
        self.eventos = eventos   # Reservado para funcionalidades futuras (Projeto B)

        # Variáveis que mudam dinamicamente durante a simulação
        self.estado = "AGUARDANDO"    # AGUARDANDO, PRONTA, EXECUTANDO ou TERMINADA
        self.tempo_executado = 0      # Quantos ticks a tarefa já rodou na instância atual
        self.deadline_absoluto = 0    # Instante limite exato para concluir esta instância
        self.execucoes_concluidas = 0 # Quantas vezes a tarefa já terminou com sucesso
        self.historico_eventos = []   # Linha do tempo de eventos para desenhar no gráfico de Gantt
        
    def ativar_tarefa(self, tempo):
        # Prepara a tarefa para uma nova rodada periódica
        self.estado = "PRONTA"
        self.tempo_executado = 0
        self.deadline_absoluto = tempo + self.prazo

    def adicionar_evento(self, tipo, tempo_inicio, tempo_fim, cpu_id=None, houve_sorteio=False):
        # Regista um novo acontecimento relevante no histórico da tarefa
        self.historico_eventos.append(EventoGantt(tipo, tempo_inicio, tempo_fim, cpu_id, houve_sorteio))

    def concluir_execucao(self):
        # Chamado quando a tarefa atinge o tempo necessário de execução
        self.execucoes_concluidas += 1
        if self.execucoes_concluidas >= 10:
            self.estado = "TERMINADA"       # Atingiu o limite de instâncias e encerra de vez
        else:
            self.estado = "AGUARDANDO"      # Volta a esperar pelo próximo ciclo do seu período
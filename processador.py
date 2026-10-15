class Processador:
    def __init__(self, id):
        self.id = id
        self.estado = "DESLIGADO"        # "ATIVO" ou "DESLIGADO"
        self.tarefa_atual = None         # TCB que está rodando aqui (None se nenhum)
        self.tempo_desligado_acumulado = 0   # ticks em que ficou sem tarefa (req. 1.2)

    def alocar_tarefa(self, tcb):
        # Coloca uma tarefa nesta CPU e a liga
        self.tarefa_atual = tcb
        self.estado = "ATIVO"
        tcb.estado = "EXECUTANDO"

    def desalocar_tarefa(self):
        # Tira a tarefa da CPU e devolve ela ao chamador.
        # O processador NÃO muda o estado do TCB aqui, porque o motivo da saída
        # decide o novo estado: preempção -> PRONTA, terminou -> AGUARDANDO.
        # Quem sabe o motivo é o simulador.
        tcb = self.tarefa_atual
        self.tarefa_atual = None
        return tcb

    def desligar(self):
        # Sem tarefa para executar: a CPU é desligada (req. 1.2)
        self.tarefa_atual = None
        self.estado = "DESLIGADO"
class Processador:
    """
    Representa uma unidade de processamento (CPU) física do sistema.
    """
    def __init__(self, id):
        self.id = id
        self.estado = "DESLIGADO"        # Indica se a CPU está "ATIVO" ou "DESLIGADO"
        self.tarefa_atual = None         # Tarefa que está rodando neste núcleo no momento
        self.tempo_desligado_acumulado = 0   # Tempo total que a CPU ficou ociosa/desligada

    def alocar_tarefa(self, tcb):
        # Atribui uma tarefa a este núcleo e muda o estado de ambos para ativos
        self.tarefa_atual = tcb
        self.estado = "ATIVO"
        tcb.estado = "EXECUTANDO"

    def desalocar_tarefa(self):
        # Remove a tarefa atual da CPU e a devolve (o destino dela é decidido pelo simulador)
        tcb = self.tarefa_atual
        self.tarefa_atual = None
        return tcb

    def desligar(self):
        # Coloca a CPU em repouso quando não há tarefas para rodar
        self.tarefa_atual = None
        self.estado = "DESLIGADO"
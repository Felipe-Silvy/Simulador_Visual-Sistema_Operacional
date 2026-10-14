class Simulador:
    def __init__(self, cpus, escalonador):
        self.cpus = cpus
        self.escalonador = escalonador
        self.tarefas = []              # lista de TCBs, o simulador é o dono

        self.relogio = 0   # relógio global (ticks)

    def adicionar_tarefa(self, tcb):
        self.tarefas.append(tcb)

    def executar(self):
        limite = 20 # Provisório, só pra ir testando
        while self.relogio < limite:
            self.tick()

    def tick(self):
        # 1. Ativar tarefas cujo período começa neste instante
        for tcb in self.tarefas:
            if self._deve_ativar(tcb):
                if tcb.estado in ("PRONTA", "EXECUTANDO"):
                    print(f"AVISO tick {self.relogio}: tarefa {tcb.id} ainda não terminou a instância anterior; nova ativação ignorada.")
                else:
                    tcb.ativar(self.relogio)
                    tcb.adicionar_evento("CHEGADA", self.relogio, self.relogio)
                    print(f"tick {self.relogio}: tarefa {tcb.id} chegou deadline absoluto = {tcb.deadline_absoluto})")

        # 2. Avança o relógio (sempre por último, para o tick atual usar o valor atual)
        self.relogio += 1

    def _deve_ativar(self, tcb):
        if tcb.estado == "TERMINADA":
            return False                       # tarefa que já fez as 10 execuções
        if self.relogio < tcb.ingresso:
            return False                       # ainda não chegou o instante de ingresso
        # Está num múltiplo do período contado a partir do ingresso?
        return (self.relogio - tcb.ingresso) % tcb.periodo == 0
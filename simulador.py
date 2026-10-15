from processador import Processador

class Simulador:
    def __init__(self, num_cpus, tarefas, escalonador):
        self.processadores = [Processador(i) for i in range(num_cpus)]
        self.escalonador = escalonador
        self.tarefas = tarefas              # lista de TCBs, o simulador é o dono
        self.fila_prontos = []              # fila global: só tarefas PRONTA, esperando CPU

        self.relogio = 0   # relógio global (ticks)

    def adicionar_tarefa(self, tcb):
        self.tarefas.append(tcb)

    def executar(self):
        limite = 1000 # Para evitar laços infinitos
        while self.relogio < limite and any(task.estado != "TERMINADA" for task in self.tarefas):
            self.tick()

    def tick(self):
        self._ativar_tarefas()                 # passo 1: 
        escolhidas = self._escolher()          # passo 3: pergunta ao escalonador
        self._aplicar_decisao(escolhidas)      # passo 4: preempção e distribuição nas CPUs
        self._executar_tick()                  # passo 5: consome 1 tick e conclui instâncias
        
        # 2. Avança o relógio (sempre por último, para o tick atual usar o valor atual)
        self.relogio += 1  # Modificar depois, avançar apenas quando o usuário clilcar na seta de avançar

    def _ativar_tarefas(self):
    # 1. Ativar tarefas cujo período começa neste instante
            for tcb in self.tarefas:
                if self._deve_ativar(tcb):
                    if tcb.estado in ("PRONTA", "EXECUTANDO"):
                        print(f"AVISO tick {self.relogio}: tarefa {tcb.id} ainda não terminou a instância anterior; nova ativação ignorada.")
                    else:
                        tcb.ativar_tarefa(self.relogio)
                        self.fila_prontos.append(tcb)
                        tcb.adicionar_evento("CHEGADA", self.relogio, self.relogio)
                        print(f"tick {self.relogio}: tarefa {tcb.id} chegou (deadline absoluto = {tcb.deadline_absoluto})")
    

    def _deve_ativar(self, tcb):
        if tcb.estado == "TERMINADA":
            return False                       # tarefa que já fez as 10 execuções
        if self.relogio < tcb.ingresso:
            return False                       # ainda não chegou o instante de ingresso
        # Está num múltiplo do período contado a partir do ingresso
        return (self.relogio - tcb.ingresso) % tcb.periodo == 0

    def _escolher(self):
        em_execucao = [cpu.tarefa_atual for cpu in self.processadores
                    if cpu.tarefa_atual is not None]
        candidatas = self.fila_prontos + em_execucao
        return self.escalonador.selecionar(candidatas, len(self.processadores), self.relogio)

    def _aplicar_decisao(self, escolhidas):
        # Preempção: quem está numa CPU mas NÃO foi escolhido perde a vaga
        for cpu in self.processadores:
            if cpu.tarefa_atual is not None and cpu.tarefa_atual not in escolhidas:
                tcb = cpu.desalocar_tarefa()
                tcb.estado = "PRONTA"       # o tempo_executado é preservado
                self.fila_prontos.append(tcb)
                print(f"tick {self.relogio}: tarefa {tcb.id} sofreu preempção "
                    f"(CPU {cpu.id})")

        # Escolhidas que ainda não estão em nenhuma CPU (as que já estão ficam onde estão)
        novas = [t for t in escolhidas if t.estado != "EXECUTANDO"]

        # CPUs livres recebem as novas; CPUs sem tarefa nenhuma são desligadas
        for cpu in self.processadores:
            if cpu.tarefa_atual is None:
                if novas:
                    task = novas.pop(0)
                    cpu.alocar_tarefa(task)
                    self.fila_prontos.remove(task)
                else:
                    cpu.desligar()

    def _executar_tick(self):
        for cpu in self.processadores:
            tcb = cpu.tarefa_atual

            if tcb is None:                                    # CPU desligada
                cpu.tempo_desligado_acumulado += 1
                print(f"tick {self.relogio}: CPU {cpu.id} desligada")
                continue

            tcb.tempo_executado += 1
            tcb.adicionar_evento("EXECUCAO", self.relogio, self.relogio + 1, cpu.id)
            print(f"tick {self.relogio}: CPU {cpu.id} executa tarefa {tcb.id} "
                f"({tcb.tempo_executado}/{tcb.duracao})")

            if tcb.tempo_executado >= tcb.duracao:             # instância terminou
                tcb.adicionar_evento("FIM", self.relogio + 1, self.relogio + 1)
                cpu.desalocar_tarefa()
                tcb.concluir_execucao()
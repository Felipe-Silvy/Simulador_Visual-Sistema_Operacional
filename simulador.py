from processador import Processador
from snapshot import SnapshotSimulacao
from historico import HistoricoSimulacao

class Simulador:
    def __init__(self, num_cpus, tarefas, escalonador):
        self.processadores = [Processador(i) for i in range(num_cpus)]
        self.escalonador = escalonador
        self.tarefas = tarefas              # lista de TCBs, o simulador é o dono
        self.fila_prontos = []              # fila global: só tarefas PRONTA, esperando CPU

        self.relogio = 0   # relógio global (ticks)

        # Inicializa o gestor do Padrão Memento (Histórico)
        self.historico = HistoricoSimulacao()
        # Salva o estado inicial (tick 0)
        self._salvar_snapshot()

    def executar(self):
        limite = 1000 # Para evitar laços infinitos
        while self.relogio < limite and self.avancar():
            pass

        # aqui chamar o gerador de imagem gantt sla o nome

    def avancar(self):
            snap = self.historico.refazer()          # há futuro já calculado?
            if snap:
                self.restaurar_estado(snap)
                return True
            if self._terminou():
                return False
            self.tick()                              # o tick() já salva o snapshot
            return True

    def restaurar_estado(self, snapshot):
        if snapshot:
            self.relogio = snapshot.relogio
            self.processadores, self.tarefas, self.fila_prontos = snapshot.copiar_estado()

    def _terminou(self):
            return all(t.estado == "TERMINADA" for t in self.tarefas)

    """""
    Adicionar se o usuário puder adicionar tarefas durante a execução
    def adicionar_tarefa(self, tcb):
            self.tarefas.append(tcb)
            self.historico.invalidar_futuro_por_edicao()
            self.historico.substituir_atual(SnapshotSimulacao(
            self.relogio, self.processadores, self.tarefas, self.fila_prontos))
    """
    def tick(self):
        self._ativar_tarefas()                 
        escolhidas, sorteadas = self._escolher()          # pergunta ao escalonador
        self._aplicar_decisao(escolhidas, sorteadas)      # preempção e distribuição nas CPUs
        self._executar_tick()                             # consome 1 tick e conclui instâncias
        
        # Avança o relógio 
        self.relogio += 1  # Modificar depois, avançar apenas quando o usuário clilcar na seta de avançar

        # Salva o novo estado gerado no histórico
        self._salvar_snapshot()
        
    def _ativar_tarefas(self):
    # Ativar tarefas cujo período começa neste instante
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

    def _aplicar_decisao(self, escolhidas, sorteadas):
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
            # Sorteadas que ficaram numa CPU: tanto as que acabaram de entrar quanto as que já estavam
            if cpu.tarefa_atual in sorteadas:
                    cpu.tarefa_atual.adicionar_evento("SORTEIO", self.relogio, self.relogio, cpu.id)

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

    def _salvar_snapshot(self):
            snapshot = SnapshotSimulacao(
                relogio=self.relogio,
                processadores=self.processadores,
                tarefas=self.tarefas,
                fila_prontos=self.fila_prontos
            )
            self.historico.salvar(snapshot)

    def modificar_tarefa_retroativa(self, tarefa_id, novas_propriedades):
        tcb = next((t for t in self.tarefas if t.id == tarefa_id), None)
        if tcb is None:
            return False

        # valida ANTES de alterar: a edição é tudo ou nada
        if not novas_propriedades or any(not hasattr(tcb, chave) for chave in novas_propriedades):
            return False

        for chave, valor in novas_propriedades.items():
            setattr(tcb, chave, valor)

        self.historico.invalidar_futuro_por_edicao()
        self.historico.substituir_atual(SnapshotSimulacao(
            self.relogio, self.processadores, self.tarefas, self.fila_prontos))
        return True

    def retroceder(self):
        snap = self.historico.desfazer()
        if snap is None:
            return False
        self.restaurar_estado(snap)
        return True

    
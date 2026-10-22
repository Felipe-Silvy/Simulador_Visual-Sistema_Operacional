from processador import Processador
from snapshot import SnapshotSimulacao
from historico import HistoricoSimulacao


class Simulador:
    def __init__(self, num_cpus, tarefas, escalonador):
        self.processadores = [Processador(i) for i in range(num_cpus)]
        self.escalonador = escalonador
        self.tarefas = tarefas
        self.fila_prontos = []
        self.relogio = 0

        self.historico = HistoricoSimulacao()
        self._salvar_snapshot()

    def executar(self):
        while self.avancar():
            pass

    def avancar(self):
        snap = self.historico.refazer()
        if snap:
            self.restaurar_estado(snap)
            return True
        if self._terminou():
            return False
        self.tick()
        return True

    def restaurar_estado(self, snapshot):
        if snapshot:
            self.relogio = snapshot.relogio
            self.processadores, self.tarefas, self.fila_prontos = (
                snapshot.copiar_estado()
            )

    def _terminou(self):
        return all(t.estado == "TERMINADA" for t in self.tarefas)

    def tick(self):
        self._ativar_tarefas()  # Ativa tarefas com ingresso no tick atual[cite: 1]
        self._verificar_deadlines()
        escolhidas, sorteadas = self._escolher()
        self._aplicar_decisao(escolhidas, sorteadas)
        self._executar_tick()

        self.relogio += 1  # Incrementa o relógio global[cite: 1]
        self._salvar_snapshot()  # Registra o Memento[cite: 1]

    def _ativar_tarefas(self):
            for tcb in self.tarefas:
                if self._deve_ativar(tcb):
                    if tcb.estado in ("PRONTA", "EXECUTANDO"):
                        tcb.adicionar_evento(
                            "ATIVACAO_IGNORADA", self.relogio, self.relogio
                        )
                    else:
                        tcb.ativar_tarefa(self.relogio)
                        self.fila_prontos.append(tcb)
                        tcb.adicionar_evento("CHEGADA", self.relogio, self.relogio)

    def _verificar_deadlines(self):
        """Métrica visual: registra o evento de perda de deadline."""
        for tcb in self.tarefas:
            if (
                tcb.estado in ("PRONTA", "EXECUTANDO")
                and self.relogio == tcb.deadline_absoluto
            ):
                tcb.adicionar_evento("DEADLINE_MISS", self.relogio, self.relogio)

    def _deve_ativar(self, tcb):
        if tcb.estado == "TERMINADA":
            return False
        if self.relogio < tcb.ingresso:
            return False
        return (self.relogio - tcb.ingresso) % tcb.periodo == 0

    def _escolher(self):
        em_execucao = [
            cpu.tarefa_atual
            for cpu in self.processadores
            if cpu.tarefa_atual is not None
        ]
        candidatas = self.fila_prontos + em_execucao
        return self.escalonador.selecionar(
            candidatas, len(self.processadores), self.relogio
        )

    def _aplicar_decisao(self, escolhidas, sorteadas):
        for cpu in self.processadores:
            if (
                cpu.tarefa_atual is not None
                and cpu.tarefa_atual not in escolhidas
            ):
                tcb = cpu.desalocar_tarefa()
                tcb.estado = "PRONTA"
                self.fila_prontos.append(tcb)

        novas = [t for t in escolhidas if t.estado != "EXECUTANDO"]

        for cpu in self.processadores:
            if cpu.tarefa_atual is None:
                if novas:
                    task = novas.pop(0)
                    cpu.alocar_tarefa(task)
                    self.fila_prontos.remove(task)
                else:
                    cpu.desligar()

            if cpu.tarefa_atual in sorteadas:
                cpu.tarefa_atual.adicionar_evento(
                    "SORTEIO", self.relogio, self.relogio, cpu.id
                )

    def _executar_tick(self):
        for cpu in self.processadores:
            tcb = cpu.tarefa_atual

            if tcb is None:
                cpu.tempo_desligado_acumulado += 1
                continue

            tcb.tempo_executado += 1
            tcb.adicionar_evento(
                "EXECUCAO", self.relogio, self.relogio + 1, cpu.id
            )

            if tcb.tempo_executado >= tcb.duracao:
                tcb.adicionar_evento("FIM", self.relogio + 1, self.relogio + 1)
                cpu.desalocar_tarefa()
                cpu.desligar() 
                tcb.concluir_execucao()

    def _salvar_snapshot(self):
        snapshot = SnapshotSimulacao(
            relogio=self.relogio,
            processadores=self.processadores,
            tarefas=self.tarefas,
            fila_prontos=self.fila_prontos,
        )
        self.historico.salvar(snapshot)

    def modificar_tarefa_retroativa(self, tarefa_id, novas_propriedades):
        tcb = next((t for t in self.tarefas if t.id == tarefa_id), None)
        if tcb is None:
            return False

        for chave, valor in novas_propriedades.items():
            if hasattr(tcb, chave):
                setattr(tcb, chave, valor)

        if tcb.estado == "PRONTA" and tcb not in self.fila_prontos:
            self.fila_prontos.append(tcb)

        if "duracao" in novas_propriedades and tcb.tempo_executado >= tcb.duracao:
            tcb.tempo_executado = 0

        self.historico.invalidar_futuro_por_edicao()
        self.historico.substituir_atual(
            SnapshotSimulacao(
                self.relogio,
                self.processadores,
                self.tarefas,
                self.fila_prontos,
            )
        )
        return True

    def retroceder(self):
        snap = self.historico.desfazer()
        if snap is None:
            return False
        self.restaurar_estado(snap)
        return True
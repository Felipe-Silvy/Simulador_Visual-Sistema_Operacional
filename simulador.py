from processador import Processador
from snapshot import SnapshotSimulacao
from historico import HistoricoSimulacao
from escalonador import ESCALONADORES

class Simulador:
    """
    O motor principal da simulação. É responsável por gerir o relógio global,
    ativar as tarefas nos momentos certos, chamar o escalonador e avançar os ticks.
    """
    def __init__(self, num_cpus, tarefas, escalonador):
        # Cria os processadores, define a política, guarda as tarefas e inicializa o histórico
        self.processadores = [Processador(i) for i in range(num_cpus)]
        self.escalonador = escalonador
        self.tarefas = tarefas
        self.fila_prontos = []
        self.relogio = 0

        self.historico = HistoricoSimulacao()
        self._salvar_snapshot()

    def executar(self):
        # Corre a simulação de uma só vez até ao fim
        while self.avancar():
            pass

    def avancar(self):
        # Tenta avançar na linha do tempo (ou refazer caso tenha retrocedido antes)
        snap = self.historico.refazer()
        if snap:
            self.restaurar_estado(snap)
            return True
        if self._terminou():
            return False
        self.tick()
        return True

    def restaurar_estado(self, snapshot):
        # Restaura o simulador para um estado guardado anteriormente (usado no desfazer/refazer)
        if snapshot:
            self.relogio = snapshot.relogio
            self.processadores, self.tarefas, self.fila_prontos = (
                snapshot.copiar_estado()
            )

    def _terminou(self):
        # Verifica se todas as tarefas já concluíram o seu ciclo de vida
        return all(t.estado == "TERMINADA" for t in self.tarefas)

    def tick(self):
        # Executa um ciclo completo (tick) da simulação
        self._ativar_tarefas()  
        self._verificar_deadlines()
        escolhidas, sorteadas = self._escolher()
        self._aplicar_decisao(escolhidas, sorteadas)
        self._executar_tick()

        self.relogio += 1  
        self._salvar_snapshot()  # Guarda o estado atual no histórico para permitir retroceder

    def _ativar_tarefas(self):
            # Verifica quais tarefas devem ser ativadas no tick atual com base no seu período
            for tcb in self.tarefas:
                if self._deve_ativar(tcb):
                    if tcb.estado in ("PRONTA", "EXECUTANDO"):
                        # Se a tarefa ainda não terminou a instância anterior, a nova ativação é ignorada
                        tcb.adicionar_evento(
                            "ATIVACAO_IGNORADA", self.relogio, self.relogio
                        )
                    else:
                        tcb.ativar_tarefa(self.relogio)
                        self.fila_prontos.append(tcb)
                        tcb.adicionar_evento("CHEGADA", self.relogio, self.relogio)

    def _verificar_deadlines(self):
        # Regista se alguma tarefa estourou o prazo limite no tick atual
        for tcb in self.tarefas:
            if (
                tcb.estado in ("PRONTA", "EXECUTANDO")
                and self.relogio == tcb.deadline_absoluto
            ):
                tcb.adicionar_evento("DEADLINE_MISS", self.relogio, self.relogio)

    def _deve_ativar(self, tcb):
        # Regra matemática para saber se o tick atual coincide com uma nova ativação periódica
        if tcb.estado == "TERMINADA":
            return False
        if self.relogio < tcb.ingresso:
            return False
        return (self.relogio - tcb.ingresso) % tcb.periodo == 0

    def _escolher(self):
        # Junta as tarefas prontas com as que já estão a executar e pede ao escalonador uma seleção
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
        # Tira da CPU as tarefas que perderam a prioridade e coloca as novas escolhidas
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
        # Avança o tempo de execução das tarefas que estão ativas nas CPUs
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
        # Tira uma "fotografia" do estado atual e guarda no histórico
        snapshot = SnapshotSimulacao(
            relogio=self.relogio,
            processadores=self.processadores,
            tarefas=self.tarefas,
            fila_prontos=self.fila_prontos,
        )
        self.historico.salvar(snapshot)

    def modificar_tarefa_retroativa(self, tarefa_id, novas_propriedades):
        # Permite alterar parâmetros de uma tarefa (ex: duração ou prazo) em tempo de execução
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
        # Volta um passo no tempo usando o histórico
        snap = self.historico.desfazer()
        if snap is None:
            return False
        self.restaurar_estado(snap)
        return True

    def trocar_escalonador(self, nome):
        # Altera a política de escalonamento dinamicamente a partir do momento atual
        classe = ESCALONADORES.get(nome)
        if classe is None:
            return False, f"Algoritmo '{nome}' desconhecido."
        self.escalonador = classe()
        self.historico.invalidar_futuro_por_edicao()
        self.historico.substituir_atual(
            SnapshotSimulacao(
                self.relogio, self.processadores, self.tarefas, self.fila_prontos
            )
        )
        return True, f"Algoritmo alterado para {nome}."
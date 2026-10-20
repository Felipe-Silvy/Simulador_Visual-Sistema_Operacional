import os
import sys
import tkinter as tk
from dataclasses import dataclass, field
from typing import Dict, Optional

# Garante que o Python encontre o módulo na mesma pasta
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from GerenciadorGrafico import GerenciadorGrafico


# ==========================================
# ESTRUTURAS FAKE PARA TESTE COMPLETO
# ==========================================
@dataclass
class TaskFake:
    id: str
    color: str
    release_time: int
    duration: int
    period: int
    deadline: int
    state: str = "READY"
    completed_tick: Optional[int] = None
    deadline_missed_tick: Optional[int] = None


@dataclass
class EstadoSimulacaoFake:
    tick: int
    algoritmo: str
    cpus: int
    tarefas: Dict[str, TaskFake]
    gantt_history: Dict[int, Dict[int, Optional[str]]] = field(
        default_factory=dict
    )


def main():
    # 1. Instancia a GUI
    gui = GerenciadorGrafico(
        titulo="Simulador SO - Teste Avançado com Todos os Recursos",
        largura=1100,
        altura=700,
    )

    # 2. Define tarefas de teste com propriedades de eventos
    tarefas = {
        "T1": TaskFake("T1", "#4CAF50", release_time=0, duration=3, period=6, deadline=5),
        "T2": TaskFake("T2", "#2196F3", release_time=1, duration=2, period=8, deadline=4),
        "T3": TaskFake("T3", "#FF9800", release_time=2, duration=4, period=10, deadline=6),
    }

    # Histórico de Gantt simular eventos
    historico_completo = {
        0: {0: "T1", 1: None},
        1: {0: "T1", 1: "T2"},
        2: {0: "T1", 1: "T2"},        # T2 conclui (✓) no tick 2
        3: {0: "T3", 1: None},
        4: {0: "T3", 1: "T1"},        # T1 estoura deadline (X) no tick 4/5
        5: {0: "T3", 1: None},
    }

    # Estado inicial
    estado = EstadoSimulacaoFake(
        tick=0,
        algoritmo="EDF",
        cpus=2,
        tarefas=tarefas,
        gantt_history={0: historico_completo[0]},
    )

    # ==========================================
    # HANDLERS DE COMUNICAÇÃO (MOTOR -> GUI)
    # ==========================================
    def carregar_ficheiro_handler(caminho):
        gui.criar_mensagem_aviso(f"Ficheiro selecionado:\n{caminho}")
        estado.tick = 0
        estado.gantt_history = {0: historico_completo[0]}
        gui.renderizar_estado(estado)

    def avancar_handler():
        if estado.tick < max(historico_completo.keys()):
            estado.tick += 1
            estado.gantt_history[estado.tick] = historico_completo[estado.tick]

            # Simulando atualizações de eventos visuais no tempo
            if estado.tick == 2:
                tarefas["T2"].completed_tick = 2
                tarefas["T2"].state = "COMPLETED"
            elif estado.tick == 4:
                tarefas["T1"].deadline_missed_tick = 4

            gui.renderizar_estado(estado)
        else:
            if gui.em_execucao:
                gui.alternar_play_pausa()  # Pausa a animação ao chegar no fim
            gui.criar_mensagem_aviso("Fim da simulação de teste!")

    def retroceder_handler():
        if estado.tick > 0:
            if estado.tick in estado.gantt_history:
                del estado.gantt_history[estado.tick]
            estado.tick -= 1

            if estado.tick < 2:
                tarefas["T2"].completed_tick = None
                tarefas["T2"].state = "RUNNING"
            if estado.tick < 4:
                tarefas["T1"].deadline_missed_tick = None

            gui.renderizar_estado(estado)

    def editar_tarefa_handler(task_id, novos_dados):
        if task_id in tarefas:
            tarefas[task_id].duration = novos_dados["duration"]
            tarefas[task_id].deadline = novos_dados["deadline"]
            tarefas[task_id].state = novos_dados["state"]
            gui.renderizar_estado(estado)

    # Conecta as funções à GUI
    gui.on_carregar_ficheiro = carregar_ficheiro_handler
    gui.on_avancar = avancar_handler
    gui.on_retroceder = retroceder_handler
    gui.on_editar_tarefa = editar_tarefa_handler

    # Renderiza estado inicial no Tick 0
    gui.renderizar_estado(estado)

    # Inicia o loop da aplicação
    gui.iniciar_loop()


if __name__ == "__main__":
    main()
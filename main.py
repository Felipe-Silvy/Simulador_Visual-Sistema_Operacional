import os
import sys
import tkinter as tk
from dataclasses import dataclass
from typing import Dict, Optional

# Garante que o Python encontre o módulo na mesma pasta
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from GerenciadorGrafico import GerenciadorGrafico


# ==========================================
# ESTRUTURAS SIMULADAS (MOCK) PARA TESTE
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


@dataclass
class EstadoSimulacaoFake:
    tick: int
    algoritmo: str
    cpus: int
    tarefas: Dict[str, TaskFake]
    gantt_history: Dict[int, Dict[int, Optional[str]]]


def main():
    # 1. Instancia o Gerenciador Gráfico
    gui = GerenciadorGrafico(
        titulo="Simulador SO - Teste Completo do Dashboard",
        largura=1000,
        altura=650,
    )

    # 2. Criar tarefas simuladas com cores diferentes
    tarefas = {
        "T1": TaskFake("T1", "#4CAF50", 0, 3, 6, 6, "READY"),
        "T2": TaskFake("T2", "#2196F3", 1, 2, 8, 8, "READY"),
        "T3": TaskFake("T3", "#FF9800", 2, 4, 10, 10, "READY"),
    }

    # Histórico de Gantt construído passo a passo para o teste
    # Formato: { tick: { cpu_id: task_id } }
    historico_completo = {
        0: {0: "T1", 1: None},
        1: {0: "T1", 1: "T2"},
        2: {0: "T1", 1: "T2"},
        3: {0: "T3", 1: None},
        4: {0: "T3", 1: "T1"},
    }

    # Estado inicial da simulação no Tick 0
    estado = EstadoSimulacaoFake(
        tick=0,
        algoritmo="EDF",
        cpus=2,
        tarefas=tarefas,
        gantt_history={0: historico_completo[0]},
    )

    # ==========================================
    # LÓGICA DE TESTE DOS BOTÕES (HANDLERS)
    # ==========================================

    def carregar_ficheiro_handler(caminho_ficheiro):
        """Disparado ao selecionar um arquivo no botão '📁 Abrir Ficheiro'."""
        gui.criar_mensagem_aviso(
            f"Ficheiro carregado com sucesso:\n{caminho_ficheiro}"
        )
        # Reseta a simulação de teste para o Tick 0
        estado.tick = 0
        estado.gantt_history = {0: historico_completo[0]}
        tarefas["T1"].state = "RUNNING"
        gui.renderizar_estado(estado)

    def avancar_handler():
        """Disparado ao clicar no botão 'Avançar ►'."""
        if estado.tick < max(historico_completo.keys()):
            estado.tick += 1
            # Adiciona o novo tick ao histórico visível do Gantt
            estado.gantt_history[estado.tick] = historico_completo[estado.tick]

            # Atualiza estados das tarefas de teste
            if estado.tick == 1:
                tarefas["T1"].state = "RUNNING"
                tarefas["T2"].state = "RUNNING"
            elif estado.tick == 3:
                tarefas["T1"].state = "COMPLETED"
                tarefas["T3"].state = "RUNNING"

            gui.renderizar_estado(estado)
        else:
            gui.criar_mensagem_aviso("Fim da simulação de teste atingido!")

    def retroceder_handler():
        """Disparado ao clicar no botão '◄ Retroceder'."""
        if estado.tick > 0:
            # Remove o tick atual do histórico para recuar no tempo
            del estado.gantt_history[estado.tick]
            estado.tick -= 1

            # Restaura os estados
            if estado.tick == 0:
                tarefas["T1"].state = "READY"
                tarefas["T2"].state = "READY"
                tarefas["T3"].state = "READY"

            gui.renderizar_estado(estado)
        else:
            gui.criar_mensagem_aviso("Já está no tick inicial (0)!")

    # 3. Conecta as funções de teste aos botões do Gerenciador Gráfico
    gui.on_carregar_ficheiro = carregar_ficheiro_handler
    gui.on_avancar = avancar_handler
    gui.on_retroceder = retroceder_handler

    # 4. Renderiza o estado inicial na tela
    gui.renderizar_estado(estado)

    # 5. Inicia o loop da interface gráfica
    gui.iniciar_loop()


if __name__ == "__main__":
    main()
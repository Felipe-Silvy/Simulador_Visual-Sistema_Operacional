import os
import sys

from escalonador import ESCALONADORES
from GerenciadorGrafico import GerenciadorGrafico
from leitor import LeitorConfiguracao
from simulador import Simulador


def extrair_estado_para_gui(simulador):
    dict_tarefas = {str(t.id): t for t in simulador.tarefas}
    gantt_history = {}

    for tick in range(simulador.relogio + 1):
        gantt_history[tick] = {cpu.id: None for cpu in simulador.processadores}

    for t in simulador.tarefas:
        for ev in getattr(t, "historico_eventos", []):
            if ev.tipo == "EXECUCAO" and ev.cpu_id is not None:
                for t_tick in range(ev.tempo_inicio, ev.tempo_fim):
                    if t_tick in gantt_history:
                        gantt_history[t_tick][ev.cpu_id] = str(t.id)

    class EstadoGUI:

        def __init__(self, tick, algoritmo, cpus, tarefas, gantt_history):
            self.tick = tick
            self.algoritmo = algoritmo
            self.cpus = cpus
            self.tarefas = tarefas
            self.gantt_history = gantt_history

    nome_politica = getattr(simulador.escalonador, "nome_politica", "RM")

    return EstadoGUI(
        simulador.relogio,
        nome_politica,
        len(simulador.processadores),
        dict_tarefas,
        gantt_history,
    )


def main():
    gui = GerenciadorGrafico(
        titulo="Simulador SO - Visualizador", largura=1100, altura=700
    )
    simulador_container = {"instance": None}

    def carregar_arquivo_handler(caminho):
        print(f"[DEBUG] Lendo arquivo: {caminho}")
        configuracao = LeitorConfiguracao()
        configuracao.ler(caminho)

        # IMPRIMA ESTES DADOS PARA CONFERIR NO TERMINAL:
        print(f"[DEBUG] Algoritmo lido: {configuracao.escalonador}")
        print(f"[DEBUG] Num CPUs: {configuracao.num_cpus}")
        print(f"[DEBUG] Total de tarefas lidas: {len(configuracao.tarefas)}")
        for t in configuracao.tarefas:
            print(
                f"   -> Tarefa ID={t.id} | Duracao={t.duracao} | Periodo={t.periodo}"
            )

        if configuracao.erros:
            msg_erro = "\n".join(configuracao.erros)
            gui.criar_mensagem_erro(
                f"Erros no arquivo de configuração:\n{msg_erro}"
            )
            return

        if configuracao.avisos:
            msg_aviso = "\n".join(configuracao.avisos)
            gui.criar_mensagem_aviso(f"Avisos:\n{msg_aviso}")

        nome_algo = configuracao.escalonador
        classe_algo = ESCALONADORES[nome_algo]

        simulador_container["instance"] = Simulador(
            num_cpus=configuracao.num_cpus,
            tarefas=configuracao.tarefas,
            escalonador=classe_algo(),
        )

        gui.renderizar_estado(
            extrair_estado_para_gui(simulador_container["instance"])
        )

    def avancar_handler():
        sim = simulador_container["instance"]
        if not sim:
            gui.paresar_animacao()
            gui.criar_mensagem_aviso(
                "Abra um arquivo de configuração primeiro."
            )
            return

        pode_avancar = sim.avancar()
        print(f"[DEBUG] Executou avancar() -> Tick: {sim.relogio}")

        if pode_avancar:
            gui.renderizar_estado(extrair_estado_para_gui(sim))
        else:
            gui.paresar_animacao()
            gui.criar_mensagem_aviso("Simulação finalizada!")

    def retroceder_handler():
        sim = simulador_container["instance"]
        if not sim:
            return

        deu_certo = sim.retroceder()
        if deu_certo:
            print(f"[DEBUG] Retrocedeu para o Tick: {sim.relogio}")
            gui.renderizar_estado(extrair_estado_para_gui(sim))
        else:
            gui.criar_mensagem_aviso("Já está no tick inicial (0)!")

    def editar_tarefa_handler(task_id, novos_dados):
        sim = simulador_container["instance"]
        if not sim:
            return

        t_id_num = int(task_id) if str(task_id).isdigit() else task_id
        sucesso = sim.modificar_tarefa_retroativa(t_id_num, novos_dados)
        if sucesso:
            gui.renderizar_estado(extrair_estado_para_gui(sim))
        else:
            gui.criar_mensagem_erro(
                "Não foi possível editar a tarefa selecionada."
            )

    gui.on_carregar_ficheiro = carregar_arquivo_handler
    gui.on_avancar = avancar_handler
    gui.on_retroceder = retroceder_handler
    gui.on_editar_tarefa = editar_tarefa_handler

    gui.iniciar_loop()


if __name__ == "__main__":
    main()
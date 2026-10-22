import os
import sys

from escalonador import ESCALONADORES
from GerenciadorGrafico import GerenciadorGrafico
from leitor import LeitorConfiguracao
from simulador import Simulador


def extrair_estado_para_gui(simulador):
    # Traduz o estado interno do simulador para um objeto simples que a interface gráfica consegue desenhar
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

    fila_prontos_ids = [str(t.id) for t in simulador.fila_prontos]

    cpus_estado = []
    for cpu in simulador.processadores:
        cpus_estado.append({
            "id": cpu.id,
            "tarefa_atual": str(cpu.tarefa_atual.id) if cpu.tarefa_atual else None,
            "tempo_desligado": getattr(cpu, "tempo_desligado_acumulado", 0)
        })

    class EstadoGUI:
        def __init__(self, tick, algoritmo, cpus, tarefas, gantt_history, fila_prontos, cpus_estado):
            self.tick = tick
            self.algoritmo = algoritmo
            self.cpus = cpus
            self.tarefas = tarefas
            self.gantt_history = gantt_history
            self.fila_prontos = fila_prontos
            self.cpus_estado = cpus_estado

    nome_politica = getattr(simulador.escalonador, "nome_politica", "RM")

    return EstadoGUI(
        simulador.relogio,
        nome_politica,
        len(simulador.processadores),
        dict_tarefas,
        gantt_history,
        fila_prontos_ids,
        cpus_estado,
    )


def main():
    # Ponto de entrada da aplicação. Inicializa a janela gráfica e o contentor do simulador.
    gui = GerenciadorGrafico(
        titulo="Simulador SO - Visualizador", largura=1200, altura=750
    )
    simulador_container = {"instance": None}

    def carregar_arquivo_handler(caminho):
        # Lê o ficheiro de configuração escolhido e arranca com a simulação
        print(f"[DEBUG] Lendo arquivo: {caminho}")
        configuracao = LeitorConfiguracao()
        configuracao.ler(caminho)

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
        # Avança um tick na simulação e atualiza a interface. Se terminar, abre o diálogo de exportação SVG.
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
            
            gui.ultimo_estado = extrair_estado_para_gui(sim)
            gui._acao_exportar_svg()

            gui.criar_mensagem_aviso("Simulação finalizada!")

    def retroceder_handler():
        # Botão de desfazer: volta para o tick anterior
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
        # Atualiza os dados de uma tarefa caso o usuário edite pelo painel
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

    def trocar_algoritmo_handler(nome):
        # Trata a troca dinâmica de algoritmo solicitada na interface
        sim = simulador_container["instance"]
        if not sim:
            gui.criar_mensagem_aviso("Abra um arquivo de configuração primeiro.")
            return
        ok, mensagem = sim.trocar_escalonador(nome)
        if not ok:
            gui.criar_mensagem_erro(mensagem)
        gui.renderizar_estado(extrair_estado_para_gui(sim))

    # Associa os callbacks da interface gráfica às funções de controlo
    gui.on_carregar_ficheiro = carregar_arquivo_handler
    gui.on_avancar = avancar_handler
    gui.on_retroceder = retroceder_handler
    gui.on_editar_tarefa = editar_tarefa_handler
    gui.on_trocar_algoritmo = trocar_algoritmo_handler

    gui.iniciar_loop()


if __name__ == "__main__":
    main()
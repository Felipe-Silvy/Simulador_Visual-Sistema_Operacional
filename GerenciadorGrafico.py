import tkinter as tk
from tkinter import filedialog, messagebox, ttk


class GerenciadorGrafico:
    """Gerenciador gráfico completo do Simulador de SO.

    Gerencia a janela do Dashboard, renderização do Gráfico de Gantt
    (com marcadores de eventos), Tabela TCB com edição passo a passo,
    controle de animação (Play/Pausa), legenda de cores e exportação SVG.
    """

    def __init__(
        self, titulo="Simulador de SO - Dashboard", largura=1100, altura=700
    ):
        self.root = tk.Tk()
        self.root.title(titulo)
        self.root.geometry(f"{largura}x{altura}")

        # Callbacks de comunicação desacoplada com o Motor
        self.on_carregar_ficheiro = None
        self.on_avancar = None
        self.on_retroceder = None
        self.on_editar_tarefa = None  # Recebe (task_id, novos_dados)

        # Controle de Animação (Play / Pausa)
        self.em_execucao = False
        self.delay_ms = 500  # Velocidade padrao (ms por tick)

        # Guardar último estado para exportação e edição
        self.ultimo_estado = None

        self._setup_layout()

    # =======================================================
    # CONSTRUÇÃO DA INTERFACE GRÁFICA
    # =======================================================
    def _setup_layout(self):
        """Cria os containers visuais, barras de navegação e componentes."""
        # 1. Barra superior de Controles
        self.frame_controles = tk.Frame(self.root, bg="#f0f0f0", height=50)
        self.frame_controles.pack(fill=tk.X, side=tk.TOP, padx=10, pady=5)

        # Botões de navegação e arquivo
        self.btn_abrir = tk.Button(
            self.frame_controles,
            text="📁 Abrir Ficheiro",
            command=self._acao_abrir_ficheiro,
            bg="#e1e1e1",
            font=("Arial", 9, "bold"),
        )
        self.btn_abrir.pack(side=tk.LEFT, padx=3)

        self.btn_retroceder = tk.Button(
            self.frame_controles,
            text="◄ Retroceder",
            command=self._acao_retroceder,
            bg="#e1e1e1",
        )
        self.btn_retroceder.pack(side=tk.LEFT, padx=3)

        self.btn_play = tk.Button(
            self.frame_controles,
            text="▶ Play",
            command=self.alternar_play_pausa,
            bg="#d4edda",
        )
        self.btn_play.pack(side=tk.LEFT, padx=3)

        self.btn_avancar = tk.Button(
            self.frame_controles,
            text="Avançar ►",
            command=self._acao_avancar,
            bg="#e1e1e1",
        )
        self.btn_avancar.pack(side=tk.LEFT, padx=3)

        self.btn_exportar = tk.Button(
            self.frame_controles,
            text="💾 Exportar SVG",
            command=self._acao_exportar_svg,
            bg="#e1e1e1",
        )
        self.btn_exportar.pack(side=tk.LEFT, padx=10)

        # Controle de Velocidade
        lbl_vel = tk.Label(
            self.frame_controles, text="Velocidade:", bg="#f0f0f0"
        )
        lbl_vel.pack(side=tk.LEFT, padx=(10, 2))

        self.slider_velocidade = tk.Scale(
            self.frame_controles,
            from_=100,
            to=1500,
            orient=tk.HORIZONTAL,
            showvalue=False,
            length=80,
            command=self._atualizar_velocidade,
        )
        self.slider_velocidade.set(500)
        self.slider_velocidade.pack(side=tk.LEFT, padx=2)

        # Label de Status (Tick, Algoritmo, CPUs)
        self.lbl_status = tk.Label(
            self.frame_controles,
            text="Tick: 0 | Algo: - | CPUs: -",
            font=("Arial", 10, "bold"),
            bg="#f0f0f0",
        )
        self.lbl_status.pack(side=tk.RIGHT, padx=10)

        # 2. Container Central Dividido (Gantt + Legenda)
        self.frame_corpo = tk.Frame(self.root, bg="white")
        self.frame_corpo.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Área do Gantt com Scrollbars
        self.frame_gantt = tk.Frame(self.frame_corpo, bg="white")
        self.frame_gantt.pack(
            side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5)
        )

        scroll_x = ttk.Scrollbar(self.frame_gantt, orient=tk.HORIZONTAL)
        scroll_y = ttk.Scrollbar(self.frame_gantt, orient=tk.VERTICAL)

        self.canvas_gantt = tk.Canvas(
            self.frame_gantt,
            bg="white",
            xscrollcommand=scroll_x.set,
            yscrollcommand=scroll_y.set,
        )

        scroll_x.config(command=self.canvas_gantt.xview)
        scroll_y.config(command=self.canvas_gantt.yview)

        scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas_gantt.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Painel Lateral de Legenda de Cores
        self.frame_legenda = tk.LabelFrame(
            self.frame_corpo, text="Legenda", bg="#f9f9f9", width=120
        )
        self.frame_legenda.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))

        # 3. Área Inferior para Tabela TCB
        self.frame_tcb = tk.Frame(self.root, height=150)
        self.frame_tcb.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=5)

        self.tabela_tcb = ttk.Treeview(
            self.frame_tcb,
            columns=(
                "ID",
                "Ingresso",
                "Duração",
                "Período",
                "Deadline",
                "Estado",
            ),
            show="headings",
            height=5,
        )
        for col in (
            "ID",
            "Ingresso",
            "Duração",
            "Período",
            "Deadline",
            "Estado",
        ):
            self.tabela_tcb.heading(col, text=col)
            self.tabela_tcb.column(col, anchor="center")
        self.tabela_tcb.pack(fill=tk.X)

        # Duplo clique na tabela para abrir a janela de edição
        self.tabela_tcb.bind("<Double-1>", self._on_double_click_tcb)

    # =======================================================
    # AÇÕES E NAVEGAÇÃO
    # =======================================================
    def _acao_abrir_ficheiro(self):
        caminho = filedialog.askopenfilename(
            title="Selecionar Ficheiro de Configuração",
            filetypes=[
                ("Ficheiros de Texto", "*.txt"),
                ("Todos os Ficheiros", "*.*"),
            ],
        )
        if caminho and self.on_carregar_ficheiro:
            self.on_carregar_ficheiro(caminho)

    def _acao_avancar(self):
        if self.on_avancar:
            self.on_avancar()

    def _acao_retroceder(self):
        if self.on_retroceder:
            self.on_retroceder()

    def _atualizar_velocidade(self, val):
        self.delay_ms = int(val)

    def alternar_play_pausa(self):
        """Alterna a execução automática contínua da simulação."""
        self.em_execucao = not self.em_execucao
        if self.em_execucao:
            self.btn_play.config(text="⏸ Pausa", bg="#f8d7da")
            self._loop_animacao()
        else:
            self.btn_play.config(text="▶ Play", bg="#d4edda")

    def _loop_animacao(self):
        if self.em_execucao:
            self._acao_avancar()
            self.root.after(self.delay_ms, self._loop_animacao)

    # =======================================================
    # RENDERIZAÇÃO E DESENHO DO GANTT
    # =======================================================
    def renderizar_estado(self, estado_simulacao):
        """Método principal chamado a cada tick para atualizar a tela inteira."""
        self.ultimo_estado = estado_simulacao

        self.atualizar_status(
            estado_simulacao.tick,
            estado_simulacao.algoritmo,
            estado_simulacao.cpus,
        )
        self.atualizar_tabela_tcb(estado_simulacao.tarefas)
        self.atualizar_legenda(estado_simulacao.tarefas)

        if hasattr(estado_simulacao, "gantt_history"):
            self.desenhar_gantt(
                estado_simulacao.gantt_history, estado_simulacao.tarefas
            )

    def atualizar_status(self, tick, algoritmo, cpus):
        self.lbl_status.config(
            text=f"Tick: {tick} | Algo: {algoritmo} | CPUs: {cpus}"
        )

    def atualizar_tabela_tcb(self, tarefas):
        for item in self.tabela_tcb.get_children():
            self.tabela_tcb.delete(item)
        for t in tarefas.values():
            self.tabela_tcb.insert(
                "",
                tk.END,
                values=(
                    t.id,
                    t.release_time,
                    getattr(t, "duration", getattr(t, "burst", "-")),
                    getattr(t, "period", "-"),
                    getattr(t, "deadline", "-"),
                    getattr(t, "state", "READY"),
                ),
            )

    def atualizar_legenda(self, tarefas):
        """Desenha a lista de tarefas com suas respectivas cores no painel lateral."""
        for widget in self.frame_legenda.winfo_children():
            widget.destroy()

        for t_id, task in tarefas.items():
            cor = getattr(task, "color", "#888888")
            item_frame = tk.Frame(self.frame_legenda, bg="#f9f9f9")
            item_frame.pack(fill=tk.X, padx=5, pady=2)

            box_cor = tk.Label(
                item_frame, bg=cor, width=2, height=1, relief="solid", bd=1
            )
            box_cor.pack(side=tk.LEFT, padx=(0, 5))

            lbl_id = tk.Label(
                item_frame,
                text=t_id,
                bg="#f9f9f9",
                font=("Arial", 8, "bold"),
            )
            lbl_id.pack(side=tk.LEFT)

    def desenhar_gantt(self, gantt_history: dict, tarefas: dict):
        """Desenha o Gráfico de Gantt no Canvas com marcadores de eventos.

        Eventos: Setas de Chegada (↑), Término (✓), CPU Ociosa e Perda de
        Deadline (X).
        """
        self.canvas_gantt.delete("all")
        if not tarefas:
            return

        cell_w = 32
        cell_h = 38
        margin_x = 75
        margin_y = 45

        # Requisito: IDs ordenados de forma DECRESCENTE no eixo Y
        sorted_task_ids = sorted(list(tarefas.keys()), reverse=True)

        # 1. Rótulos do Eixo Y
        for idx, task_id in enumerate(sorted_task_ids):
            y_pos = margin_y + (idx * cell_h)
            self.canvas_gantt.create_text(
                margin_x - 15,
                y_pos + (cell_h / 2),
                text=task_id,
                font=("Arial", 10, "bold"),
                anchor="e",
            )

            max_grid_x = margin_x + (len(gantt_history) * cell_w) + 80
            self.canvas_gantt.create_line(
                margin_x, y_pos + cell_h, max_grid_x, y_pos + cell_h, fill="#f0f0f0"
            )

        # 2. Blocos de Execução e Marcadores
        for tick, cpu_map in gantt_history.items():
            x0 = margin_x + (tick * cell_w)
            x1 = x0 + cell_w

            # Eixo X (Tick)
            self.canvas_gantt.create_text(
                x0 + (cell_w / 2),
                margin_y - 15,
                text=str(tick),
                font=("Arial", 8),
                anchor="center",
            )

            # Verifica quais tarefas foram alocadas
            tarefas_executadas_no_tick = set()

            for cpu_id, task_id in cpu_map.items():
                if task_id and task_id in sorted_task_ids:
                    tarefas_executadas_no_tick.add(task_id)
                    task = tarefas[task_id]
                    y_idx = sorted_task_ids.index(task_id)
                    y0 = margin_y + (y_idx * cell_h) + 3
                    y1 = y0 + cell_h - 6

                    # Bloco principal de execução
                    cor = getattr(task, "color", "#2196F3")
                    self.canvas_gantt.create_rectangle(
                        x0, y0, x1, y1, fill=cor, outline="black"
                    )

                    # ID da CPU dentro do bloco (se houver múltiplas)
                    if len(cpu_map) > 1:
                        self.canvas_gantt.create_text(
                            x0 + (cell_w / 2),
                            y0 + ((y1 - y0) / 2),
                            text=f"C{cpu_id}",
                            fill="white",
                            font=("Arial", 7, "bold"),
                        )

            # --- MARCADORES DE EVENTOS ---
            for task_id in sorted_task_ids:
                task = tarefas[task_id]
                y_idx = sorted_task_ids.index(task_id)
                y0 = margin_y + (y_idx * cell_h) + 3
                y1 = y0 + cell_h - 6

                # Chegada / Ingresso (Seta para cima ↑)
                release_time = getattr(task, "release_time", 0)
                if tick == release_time:
                    self.canvas_gantt.create_text(
                        x0 + 4,
                        y1 + 4,
                        text="↑",
                        fill="green",
                        font=("Arial", 9, "bold"),
                    )

                # Estouro de Deadline (Linha e X vermelho)
                deadline = getattr(task, "deadline", None)
                estourou_dl = getattr(task, "deadline_missed_tick", None)
                if estourou_dl == tick or (
                    deadline and tick == deadline and getattr(task, "state", "") != "COMPLETED"
                ):
                    self.canvas_gantt.create_line(
                        x1, y0 - 2, x1, y1 + 2, fill="red", width=2
                    )
                    self.canvas_gantt.create_text(
                        x1,
                        y0 - 8,
                        text="✕",
                        fill="red",
                        font=("Arial", 10, "bold"),
                    )

                # Conclusão / Término (✓)
                completed_tick = getattr(task, "completed_tick", None)
                if completed_tick == tick:
                    self.canvas_gantt.create_text(
                        x1 - 4,
                        y0 + 4,
                        text="✓",
                        fill="blue",
                        font=("Arial", 8, "bold"),
                    )

        max_x = margin_x + (len(gantt_history) * cell_w) + 100
        max_y = margin_y + (len(sorted_task_ids) * cell_h) + 50
        self.canvas_gantt.config(scrollregion=(0, 0, max_x, max_y))

    # =======================================================
    # JANELA DE EDIÇÃO DE TAREFA (DEBUGGER)
    # =======================================================
    def _on_double_click_tcb(self, event):
        item = self.tabela_tcb.selection()
        if not item:
            return
        val = self.tabela_tcb.item(item[0], "values")
        task_id = val[0]
        self._abrir_janela_edicao_tarefa(task_id, val)

    def _abrir_janela_edicao_tarefa(self, task_id, val_atuais):
        """Abre caixa de diálogo para alterar parâmetros de uma tarefa no passo a passo."""
        top = tk.Toplevel(self.root)
        top.title(f"Editar Tarefa - {task_id}")
        top.geometry("280x220")
        top.resizable(False, False)

        tk.Label(top, text=f"Alterar Parâmetros ({task_id})", font=("Arial", 10, "bold")).pack(pady=5)

        frame_form = tk.Frame(top)
        frame_form.pack(pady=5, padx=10)

        tk.Label(frame_form, text="Duração:").grid(row=0, column=0, sticky="e", pady=2)
        ent_dur = tk.Entry(frame_form, width=10)
        ent_dur.insert(0, str(val_atuais[2]))
        ent_dur.grid(row=0, column=1, pady=2)

        tk.Label(frame_form, text="Deadline:").grid(row=1, column=0, sticky="e", pady=2)
        ent_dl = tk.Entry(frame_form, width=10)
        ent_dl.insert(0, str(val_atuais[4]))
        ent_dl.grid(row=1, column=1, pady=2)

        tk.Label(frame_form, text="Estado:").grid(row=2, column=0, sticky="e", pady=2)
        cb_estado = ttk.Combobox(
            frame_form,
            values=["READY", "RUNNING", "WAITING", "COMPLETED"],
            width=10,
            state="readonly",
        )
        cb_estado.set(val_atuais[5])
        cb_estado.grid(row=2, column=1, pady=2)

        def salvar():
            try:
                novos_dados = {
                    "duration": int(ent_dur.get()),
                    "deadline": int(ent_dl.get()),
                    "state": cb_estado.get(),
                }
                if self.on_editar_tarefa:
                    self.on_editar_tarefa(task_id, novos_dados)
                top.destroy()
                self.criar_mensagem_aviso(f"Tarefa {task_id} atualizada!")
            except ValueError:
                self.criar_mensagem_erro("Por favor, insira números válidos!")

        tk.Button(top, text="Salvar Alterações", command=salvar, bg="#d1ecf1").pack(pady=10)

    # =======================================================
    # EXPORTAÇÃO SVG NATIVA
    # =======================================================
    def _acao_exportar_svg(self):
        if not self.ultimo_estado or not hasattr(self.ultimo_estado, "gantt_history"):
            self.criar_mensagem_erro("Não há dados de simulação para exportar!")
            return

        caminho = filedialog.asksaveasfilename(
            title="Salvar Gráfico de Gantt como SVG",
            defaultextension=".svg",
            filetypes=[("Arquivo SVG", "*.svg")],
        )
        if caminho:
            self.exportar_gantt_svg(
                self.ultimo_estado.gantt_history,
                self.ultimo_estado.tarefas,
                caminho,
            )

    def exportar_gantt_svg(
        self, gantt_history: dict, tarefas: dict, caminho_arquivo: str
    ):
        """Gera um arquivo físico vetorial em formato SVG nativo com o Gantt completo."""
        cell_w = 30
        cell_h = 35
        margin_x = 80
        margin_y = 50

        sorted_task_ids = sorted(list(tarefas.keys()), reverse=True)
        num_ticks = len(gantt_history)

        width = margin_x + (num_ticks * cell_w) + 100
        height = margin_y + (len(sorted_task_ids) * cell_h) + 60

        # Início do documento SVG
        svg = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" style="background-color:white; font-family:Arial, sans-serif;">'
        ]

        # Título
        svg.append(
            '<text x="20" y="30" font-size="16" font-weight="bold">Gráfico de Gantt - Simulador SO</text>'
        )

        # Eixo Y (Tarefas)
        for idx, task_id in enumerate(sorted_task_ids):
            y_pos = margin_y + (idx * cell_h)
            svg.append(
                f'<text x="{margin_x - 10}" y="{y_pos + 22}" font-size="12" font-weight="bold" text-anchor="end">{task_id}</text>'
            )
            svg.append(
                f'<line x1="{margin_x}" y1="{y_pos + cell_h}" x2="{width - 20}" y2="{y_pos + cell_h}" stroke="#f0f0f0" stroke-width="1" />'
            )

        # Eixo X e Blocos
        for tick, cpu_map in gantt_history.items():
            x0 = margin_x + (tick * cell_w)

            # Texto do Tick
            svg.append(
                f'<text x="{x0 + (cell_w / 2)}" y="{margin_y - 10}" font-size="10" text-anchor="middle">{tick}</text>'
            )

            # Blocos
            for cpu_id, task_id in cpu_map.items():
                if task_id and task_id in sorted_task_ids:
                    task = tarefas[task_id]
                    y_idx = sorted_task_ids.index(task_id)
                    y0 = margin_y + (y_idx * cell_h) + 3
                    cor = getattr(task, "color", "#2196F3")

                    svg.append(
                        f'<rect x="{x0}" y="{y0}" width="{cell_w}" height="{cell_h - 6}" fill="{cor}" stroke="black" stroke-width="1" />'
                    )

        svg.append("</svg>")

        with open(caminho_arquivo, "w", encoding="utf-8") as f:
            f.write("\n".join(svg))

        self.criar_mensagem_aviso(f"Gráfico exportado em SVG:\n{caminho_arquivo}")

    # =======================================================
    # MENSAGENS E POPUPS
    # =======================================================
    def criar_mensagem_erro(self, mensagem: str) -> None:
        print(f"[ERRO] {mensagem}")
        messagebox.showerror("Erro do Sistema", mensagem, parent=self.root)

    def criar_mensagem_aviso(self, mensagem: str) -> None:
        print(f"[AVISO] {mensagem}")
        messagebox.showwarning("Aviso do Sistema", mensagem, parent=self.root)

    def iniciar_loop(self):
        self.root.mainloop()
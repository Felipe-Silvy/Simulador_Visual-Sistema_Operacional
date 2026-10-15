import tkinter as tk
from tkinter import filedialog, messagebox, ttk


class GerenciadorGrafico:
    """Gerenciador gráfico responsável pela janela principal (Dashboard),

    desenho do Gráfico de Gantt, tabela TCB e mensagens do sistema.
    """

    def __init__(
        self, titulo="Simulador de SO - Dashboard", largura=1000, altura=650
    ):
        self.root = tk.Tk()
        self.root.title(titulo)
        self.root.geometry(f"{largura}x{altura}")

        # Callbacks de eventos para comunicação desacoplada com o Motor
        self.on_carregar_ficheiro = None
        self.on_avancar = None
        self.on_retroceder = None

        self._setup_layout()

    def _setup_layout(self):
        """Cria os containers visuais e os botões de controlo do dashboard."""
        # 1. Barra superior para botões e informações gerais
        self.frame_controles = tk.Frame(self.root, bg="#f0f0f0", height=50)
        self.frame_controles.pack(fill=tk.X, side=tk.TOP, padx=10, pady=5)

        # --- BOTÕES DE CONTROLO NA BARRA SUPERIOR ---
        self.btn_abrir_ficheiro = tk.Button(
            self.frame_controles,
            text="📁 Abrir Ficheiro",
            command=self._acao_abrir_ficheiro,
            bg="#e1e1e1",
            font=("Arial", 9, "bold"),
        )
        self.btn_abrir_ficheiro.pack(side=tk.LEFT, padx=5)

        self.btn_retroceder = tk.Button(
            self.frame_controles,
            text="◄ Retroceder",
            command=self._acao_retroceder,
            bg="#e1e1e1",
        )
        self.btn_retroceder.pack(side=tk.LEFT, padx=5)

        self.btn_avancar = tk.Button(
            self.frame_controles,
            text="Avançar ►",
            command=self._acao_avancar,
            bg="#e1e1e1",
        )
        self.btn_avancar.pack(side=tk.LEFT, padx=5)

        # Label de Status (Tick global, Algoritmo, CPUs)
        self.lbl_status = tk.Label(
            self.frame_controles,
            text="Tick: 0 | Algo: - | CPUs: -",
            font=("Arial", 10, "bold"),
            bg="#f0f0f0",
        )
        self.lbl_status.pack(side=tk.RIGHT, padx=10)

        # 2. Área central para o Gráfico de Gantt (Canvas com Scrollbars)
        self.frame_gantt = tk.Frame(self.root, bg="white")
        self.frame_gantt.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Scrollbars para navegação no Gantt
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

        # 3. Área inferior para a tabela TCB
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

    # --- AÇÕES DOS BOTÕES DE CONTROLO ---
    def _acao_abrir_ficheiro(self):
        caminho = filedialog.askopenfilename(
            title="Selecionar Ficheiro de Configuração",
            filetypes=[
                ("Ficheiros de Texto", "*.txt"),
                ("Todos os Ficheiros", "*.*"),
            ],
        )
        if caminho:
            if self.on_carregar_ficheiro:
                self.on_carregar_ficheiro(caminho)
            else:
                self.criar_mensagem_aviso(f"Ficheiro selecionado: {caminho}")

    def _acao_avancar(self):
        if self.on_avancar:
            self.on_avancar()
        else:
            self.criar_mensagem_aviso("Ação de Avançar disparada!")

    def _acao_retroceder(self):
        if self.on_retroceder:
            self.on_retroceder()
        else:
            self.criar_mensagem_aviso("Ação de Retroceder disparada!")

    # --- MÉTODOS DE RENDERIZAÇÃO E DESENHO ---
    def renderizar_estado(self, estado_simulacao):
        """Atualiza todos os componentes visuais do dashboard a cada tick."""
        self.atualizar_status(
            estado_simulacao.tick,
            estado_simulacao.algoritmo,
            estado_simulacao.cpus,
        )
        self.atualizar_tabela_tcb(estado_simulacao.tarefas)

        # Chama a renderização do Gantt se o estado contiver o histórico
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
                    t.duration,
                    t.period,
                    t.deadline,
                    t.state,
                ),
            )

    def desenhar_gantt(self, gantt_history: dict, tarefas: dict):
        """Redesenha todo o gráfico de Gantt no Canvas com base no histórico.

        - gantt_history: {tick: {cpu_id: task_id}}
        - tarefas: {task_id: objeto_task}
        """
        self.canvas_gantt.delete("all")

        if not tarefas:
            return

        # Dimensões e margens do gráfico
        cell_w = 30
        cell_h = 35
        margin_x = 70
        margin_y = 40

        # Ordena IDs das tarefas em ORDEM DECRESCENTE para o eixo Y
        sorted_task_ids = sorted(list(tarefas.keys()), reverse=True)

        # 1. Desenhar Eixo Y (Rótulos dos IDs das tarefas)
        for idx, task_id in enumerate(sorted_task_ids):
            y_pos = margin_y + (idx * cell_h)

            self.canvas_gantt.create_text(
                margin_x - 15,
                y_pos + (cell_h / 2),
                text=task_id,
                font=("Arial", 10, "bold"),
                anchor="e",
            )

            # Linha horizontal de fundo
            max_grid_x = margin_x + (len(gantt_history) * cell_w) + 100
            self.canvas_gantt.create_line(
                margin_x, y_pos + cell_h, max_grid_x, y_pos + cell_h, fill="#f0f0f0"
            )

        # 2. Desenhar Histórico de Execução (Eixo X e Blocos)
        for tick, cpu_map in gantt_history.items():
            x0 = margin_x + (tick * cell_w)
            x1 = x0 + cell_w

            # Número do Tick no topo
            self.canvas_gantt.create_text(
                x0 + (cell_w / 2),
                margin_y - 15,
                text=str(tick),
                font=("Arial", 8),
                anchor="center",
            )

            # Blocos das tarefas em cada CPU
            for cpu_id, task_id in cpu_map.items():
                if task_id and task_id in sorted_task_ids:
                    task = tarefas[task_id]
                    y_idx = sorted_task_ids.index(task_id)
                    y0 = margin_y + (y_idx * cell_h) + 3
                    y1 = y0 + cell_h - 6

                    self.canvas_gantt.create_rectangle(
                        x0, y0, x1, y1, fill=task.color, outline="black"
                    )

                    # Se houver múltiplas CPUs, identifica qual executou
                    if len(cpu_map) > 1:
                        self.canvas_gantt.create_text(
                            x0 + (cell_w / 2),
                            y0 + ((y1 - y0) / 2),
                            text=f"C{cpu_id}",
                            fill="white",
                            font=("Arial", 7, "bold"),
                        )

        # Atualiza a área de scroll do Canvas
        max_x = margin_x + (len(gantt_history) * cell_w) + 100
        max_y = margin_y + (len(sorted_task_ids) * cell_h) + 50
        self.canvas_gantt.config(scrollregion=(0, 0, max_x, max_y))

    # --- MENSAGENS E POPUPS ---
    def criar_mensagem_erro(self, mensagem: str) -> None:
        print(f"[ERRO] {mensagem}")
        messagebox.showerror("Erro do Sistema", mensagem, parent=self.root)

    def criar_mensagem_aviso(self, mensagem: str) -> None:
        print(f"[AVISO] {mensagem}")
        messagebox.showwarning("Aviso do Sistema", mensagem, parent=self.root)

    def iniciar_loop(self):
        self.root.mainloop()
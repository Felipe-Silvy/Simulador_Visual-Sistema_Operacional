import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk


class GerenciadorGrafico:
    """Gerenciador gráfico do Simulador de SO com execução em alta velocidade e exportação SVG."""

    def __init__(
        self, titulo="Simulador de SO - Dashboard", largura=1100, altura=700
    ):
        self.root = tk.Tk()
        self.root.title(titulo)
        self.root.geometry(f"{largura}x{altura}")

        self.on_carregar_ficheiro = None
        self.on_avancar = None
        self.on_retroceder = None
        self.on_editar_tarefa = None

        self.em_execucao = False
        self.delay_ms = 1  # Execução na velocidade máxima (1ms por tick)
        self.ultimo_estado = None

        self._setup_layout()

    def _setup_layout(self):
        self.frame_controles = tk.Frame(self.root, bg="#f0f0f0", height=50)
        self.frame_controles.pack(fill=tk.X, side=tk.TOP, padx=10, pady=5)

        self.btn_abrir = tk.Button(
            self.frame_controles,
            text="📁 Abrir Ficheiro",
            command=self._acao_abrir_ficheiro,
            bg="#e1e1e1",
            font=("Arial", 9, "bold"),
        )
        self.btn_abrir.pack(side=tk.LEFT, padx=3)

        self.lbl_arquivo = tk.Label(
            self.frame_controles,
            text="Ficheiro: (nenhum)",
            font=("Arial", 8, "italic"),
            bg="#f0f0f0",
            fg="#555555",
        )
        self.lbl_arquivo.pack(side=tk.LEFT, padx=(2, 10))

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
            font=("Arial", 9, "bold"),
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

        self.lbl_status = tk.Label(
            self.frame_controles,
            text="Tick: 0 | Algo: - | CPUs: -",
            font=("Arial", 10, "bold"),
            bg="#f0f0f0",
        )
        self.lbl_status.pack(side=tk.RIGHT, padx=10)

        self.frame_corpo = tk.Frame(self.root, bg="white")
        self.frame_corpo.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

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

        self.frame_legenda = tk.LabelFrame(
            self.frame_corpo, text="Legenda", bg="#f9f9f9", width=120
        )
        self.frame_legenda.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))

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

        self.tabela_tcb.bind("<Double-1>", self._on_double_click_tcb)

    def _acao_abrir_ficheiro(self):
        caminho = filedialog.askopenfilename(
            title="Selecionar Ficheiro de Configuração",
            filetypes=[
                ("Ficheiros de Texto", "*.txt"),
                ("Todos os Ficheiros", "*.*"),
            ],
        )
        if caminho and callable(self.on_carregar_ficheiro):
            nome_arquivo = os.path.basename(caminho)
            self.lbl_arquivo.config(
                text=f"Ficheiro: {nome_arquivo}", fg="#0066cc"
            )
            self.paresar_animacao()
            self.on_carregar_ficheiro(caminho)

    def _acao_avancar(self):
        if callable(self.on_avancar):
            self.on_avancar()

    def _acao_retroceder(self):
        if callable(self.on_retroceder):
            self.on_retroceder()

    def alternar_play_pausa(self):
        self.em_execucao = not self.em_execucao
        if self.em_execucao:
            self.btn_play.config(text="⏸ Pausa", bg="#f8d7da")
            self._loop_animacao()
        else:
            self.btn_play.config(text="▶ Play", bg="#d4edda")

    def paresar_animacao(self):
        self.em_execucao = False
        self.btn_play.config(text="▶ Play", bg="#d4edda")

    def _loop_animacao(self):
        if self.em_execucao:
            self._acao_avancar()
            if self.em_execucao:
                self.root.after(self.delay_ms, self._loop_animacao)

    def renderizar_estado(self, estado_simulacao):
        self.ultimo_estado = estado_simulacao

        tick = getattr(estado_simulacao, "tick", 0)
        algoritmo = getattr(estado_simulacao, "algoritmo", "-")
        cpus = getattr(estado_simulacao, "cpus", 1)
        tarefas = getattr(estado_simulacao, "tarefas", {})
        gantt_history = getattr(estado_simulacao, "gantt_history", {})

        self.atualizar_status(tick, algoritmo, cpus)
        self.atualizar_tabela_tcb(tarefas)
        self.atualizar_legenda(tarefas)
        self.desenhar_gantt(gantt_history, tarefas, cpus)
        self.root.update()

    def atualizar_status(self, tick, algoritmo, cpus):
        self.lbl_status.config(
            text=f"Tick: {tick} | Algo: {algoritmo} | CPUs: {cpus}"
        )

    def atualizar_tabela_tcb(self, tarefas: dict):
        for item in self.tabela_tcb.get_children():
            self.tabela_tcb.delete(item)

        for t_id, t in tarefas.items():
            ingresso = getattr(t, "ingresso", 0)
            duracao = getattr(t, "duracao", "-")
            periodo = getattr(t, "periodo", "-")
            prazo = getattr(t, "prazo", "-")
            estado = getattr(t, "estado", "AGUARDANDO")

            self.tabela_tcb.insert(
                "",
                tk.END,
                values=(t_id, ingresso, duracao, periodo, prazo, estado),
            )

    def atualizar_legenda(self, tarefas: dict):
        for widget in self.frame_legenda.winfo_children():
            widget.destroy()

        for t_id, task in tarefas.items():
            cor_hex = getattr(task, "cor", "2196F3")
            cor = f"#{cor_hex}" if not cor_hex.startswith("#") else cor_hex

            item_frame = tk.Frame(self.frame_legenda, bg="#f9f9f9")
            item_frame.pack(fill=tk.X, padx=5, pady=2)

            box_cor = tk.Label(
                item_frame, bg=cor, width=2, height=1, relief="solid", bd=1
            )
            box_cor.pack(side=tk.LEFT, padx=(0, 5))

            lbl_id = tk.Label(
                item_frame,
                text=f"T{t_id}",
                bg="#f9f9f9",
                font=("Arial", 8, "bold"),
            )
            lbl_id.pack(side=tk.LEFT)

    def desenhar_gantt(self, gantt_history: dict, tarefas: dict, total_cpus=1):
        self.canvas_gantt.delete("all")
        if not tarefas:
            return

        cell_w = 32
        cell_h = 38
        margin_x = 75
        margin_y = 45

        sorted_task_ids = sorted(
            list(tarefas.keys()), key=lambda x: str(x), reverse=True
        )

        for idx, task_id in enumerate(sorted_task_ids):
            y_pos = margin_y + (idx * cell_h)
            self.canvas_gantt.create_text(
                margin_x - 15,
                y_pos + (cell_h / 2),
                text=f"T{task_id}",
                font=("Arial", 10, "bold"),
                anchor="e",
            )
            max_grid_x = margin_x + (len(gantt_history) * cell_w) + 80
            self.canvas_gantt.create_line(
                margin_x,
                y_pos + cell_h,
                max_grid_x,
                y_pos + cell_h,
                fill="#f0f0f0",
            )

        for tick, cpu_map in gantt_history.items():
            x0 = margin_x + (tick * cell_w)
            x1 = x0 + cell_w

            self.canvas_gantt.create_text(
                x0 + (cell_w / 2),
                margin_y - 15,
                text=str(tick),
                font=("Arial", 8),
                anchor="center",
            )

            for cpu_id, task_id in cpu_map.items():
                if task_id is not None and str(task_id) in sorted_task_ids:
                    task_key = str(task_id)
                    task = tarefas[task_key]
                    y_idx = sorted_task_ids.index(task_key)
                    y0 = margin_y + (y_idx * cell_h) + 3
                    y1 = y0 + cell_h - 6

                    cor_hex = getattr(task, "cor", "2196F3")
                    cor = (
                        f"#{cor_hex}"
                        if not cor_hex.startswith("#")
                        else cor_hex
                    )

                    self.canvas_gantt.create_rectangle(
                        x0, y0, x1, y1, fill=cor, outline="black"
                    )

                    if total_cpus > 1:
                        self.canvas_gantt.create_text(
                            x0 + (cell_w / 2),
                            y0 + ((y1 - y0) / 2),
                            text=f"C{cpu_id}",
                            fill="white",
                            font=("Arial", 7, "bold"),
                        )

            for task_id in sorted_task_ids:
                task = tarefas[task_id]
                y_idx = sorted_task_ids.index(task_id)
                y0 = margin_y + (y_idx * cell_h) + 3
                y1 = y0 + cell_h - 6

                for ev in getattr(task, "historico_eventos", []):
                    if ev.tempo_inicio == tick:
                        if ev.tipo == "CHEGADA":
                            self.canvas_gantt.create_text(
                                x0 + 4,
                                y1 + 4,
                                text="↑",
                                fill="green",
                                font=("Arial", 10, "bold"),
                            )
                        elif ev.tipo == "FIM":
                            self.canvas_gantt.create_text(
                                x1 - 4,
                                y0 + 4,
                                text="✓",
                                fill="blue",
                                font=("Arial", 8, "bold"),
                            )
                        elif ev.tipo == "DEADLINE_MISS":
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

        max_x = margin_x + (len(gantt_history) * cell_w) + 100
        max_y = margin_y + (len(sorted_task_ids) * cell_h) + 50
        self.canvas_gantt.config(scrollregion=(0, 0, max_x, max_y))

    def _on_double_click_tcb(self, event):
        item = self.tabela_tcb.selection()
        if not item:
            return
        val = self.tabela_tcb.item(item[0], "values")
        task_id = val[0]
        self._abrir_janela_edicao_tarefa(task_id, val)

    def _abrir_janela_edicao_tarefa(self, task_id, val_atuais):
        top = tk.Toplevel(self.root)
        top.title(f"Editar Tarefa - T{task_id}")
        top.geometry("280x220")
        top.resizable(False, False)

        tk.Label(
            top,
            text=f"Alterar Parâmetros (T{task_id})",
            font=("Arial", 10, "bold"),
        ).pack(pady=5)

        frame_form = tk.Frame(top)
        frame_form.pack(pady=5, padx=10)

        tk.Label(frame_form, text="Duração:").grid(
            row=0, column=0, sticky="e", pady=2
        )
        ent_dur = tk.Entry(frame_form, width=10)
        ent_dur.insert(0, str(val_atuais[2]))
        ent_dur.grid(row=0, column=1, pady=2)

        tk.Label(frame_form, text="Deadline:").grid(
            row=1, column=0, sticky="e", pady=2
        )
        ent_dl = tk.Entry(frame_form, width=10)
        ent_dl.insert(0, str(val_atuais[4]))
        ent_dl.grid(row=1, column=1, pady=2)

        tk.Label(frame_form, text="Estado:").grid(
            row=2, column=0, sticky="e", pady=2
        )
        cb_estado = ttk.Combobox(
            frame_form,
            values=["AGUARDANDO", "PRONTA", "EXECUTANDO", "TERMINADA"],
            width=10,
            state="readonly",
        )
        cb_estado.set(val_atuais[5])
        cb_estado.grid(row=2, column=1, pady=2)

        def salvar():
            try:
                novos_dados = {
                    "duracao": int(ent_dur.get()),
                    "prazo": int(ent_dl.get()),
                    "estado": cb_estado.get(),
                }
                if self.on_editar_tarefa:
                    self.on_editar_tarefa(task_id, novos_dados)
                top.destroy()
                self.criar_mensagem_aviso(f"Tarefa T{task_id} atualizada!")
            except ValueError:
                self.criar_mensagem_erro("Por favor, insira números válidos!")

        tk.Button(
            top, text="Salvar Alterações", command=salvar, bg="#d1ecf1"
        ).pack(pady=10)

    def _acao_exportar_svg(self):
        if not self.ultimo_estado:
            self.criar_mensagem_erro(
                "Não há dados de simulação para exportar!"
            )
            return

        gantt_history = getattr(self.ultimo_estado, "gantt_history", {})
        tarefas = getattr(self.ultimo_estado, "tarefas", {})
        cpus = getattr(self.ultimo_estado, "cpus", 1)

        caminho = filedialog.asksaveasfilename(
            title="Salvar Gráfico de Gantt como SVG",
            defaultextension=".svg",
            filetypes=[("Arquivo SVG", "*.svg")],
        )
        if caminho:
            self.exportar_gantt_svg(caminho, gantt_history, tarefas, cpus)

    def exportar_gantt_svg(
        self,
        caminho_arquivo: str,
        gantt_history: dict,
        tarefas: dict,
        total_cpus: int = 1,
    ):
        cell_w = 36
        cell_h = 40
        margin_x = 90
        margin_y = 60

        tarefas_norm = {str(k): v for k, v in tarefas.items()}
        sorted_task_ids = sorted(
            list(tarefas_norm.keys()), key=lambda x: str(x), reverse=True
        )
        num_ticks = max(len(gantt_history), 1)

        width = margin_x + (num_ticks * cell_w) + 120
        height = margin_y + (len(sorted_task_ids) * cell_h) + 80

        svg = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
            f'  <rect width="{width}" height="{height}" fill="#ffffff" />',
            '  <!-- Titulo -->',
            '  <text x="20" y="30" font-size="16" font-weight="bold" fill="#000000" font-family="sans-serif">Grafico de Gantt - Simulador SO</text>',
        ]

        # 1. Rótulos Eixo Y
        for idx, task_id in enumerate(sorted_task_ids):
            y_pos = margin_y + (idx * cell_h)
            svg.append(
                f'  <rect x="{margin_x - 45}" y="{y_pos + 6}" width="35" height="22" rx="4" fill="#222222" />'
            )
            svg.append(
                f'  <text x="{margin_x - 27}" y="{y_pos + 22}" font-size="12" font-weight="bold" fill="#ffffff" font-family="sans-serif" text-anchor="middle">T{task_id}</text>'
            )
            svg.append(
                f'  <line x1="{margin_x}" y1="{y_pos + cell_h}" x2="{width - 30}" y2="{y_pos + cell_h}" stroke="#d0d0d0" stroke-width="1" />'
            )

        # 2. Marcadores Eixo X
        for tick in range(num_ticks):
            cpu_map = gantt_history.get(
                tick, {c: None for c in range(total_cpus)}
            )
            x0 = margin_x + (tick * cell_w)
            x1 = x0 + cell_w

            svg.append(
                f'  <text x="{x0 + (cell_w / 2)}" y="{margin_y - 12}" font-size="11" font-weight="bold" fill="#000000" font-family="sans-serif" text-anchor="middle">{tick}</text>'
            )
            svg.append(
                f'  <line x1="{x0}" y1="{margin_y - 5}" x2="{x0}" y2="{margin_y}" stroke="#888888" stroke-width="1" />'
            )

            for cpu_id, task_id in cpu_map.items():
                if task_id is not None:
                    task_key = str(task_id)
                    if task_key in sorted_task_ids:
                        task = tarefas_norm[task_key]
                        y_idx = sorted_task_ids.index(task_key)
                        y0 = margin_y + (y_idx * cell_h) + 4

                        cor_hex = getattr(task, "cor", "2196F3")
                        cor = (
                            f"#{cor_hex}"
                            if not str(cor_hex).startswith("#")
                            else str(cor_hex)
                        )

                        svg.append(
                            f'  <rect x="{x0}" y="{y0}" width="{cell_w}" height="{cell_h - 8}" fill="{cor}" stroke="#000000" stroke-width="1" />'
                        )

                        if total_cpus > 1:
                            svg.append(
                                f'  <text x="{x0 + (cell_w / 2)}" y="{y0 + 20}" font-size="9" font-weight="bold" fill="#ffffff" font-family="sans-serif" text-anchor="middle">C{cpu_id}</text>'
                            )

            # 3. Eventos Vetoriais
            for task_id in sorted_task_ids:
                task = tarefas_norm.get(str(task_id))
                if not task:
                    continue

                y_idx = sorted_task_ids.index(str(task_id))
                y0 = margin_y + (y_idx * cell_h) + 4
                y1 = y0 + cell_h - 8

                for ev in getattr(task, "historico_eventos", []):
                    if ev.tempo_inicio == tick:
                        if ev.tipo == "CHEGADA":
                            svg.append(
                                f'  <path d="M{x0+5} {y1+14} L{x0+5} {y1+2} M{x0+2} {y1+6} L{x0+5} {y1+2} L{x0+8} {y1+6}" stroke="#008000" stroke-width="2" fill="none" />'
                            )
                        elif ev.tipo == "FIM":
                            svg.append(
                                f'  <path d="M{x1-10} {y0-6} L{x1-6} {y0-2} L{x1-1} {y0-9}" stroke="#0000FF" stroke-width="2" fill="none" />'
                            )
                        elif ev.tipo == "DEADLINE_MISS":
                            svg.append(
                                f'  <line x1="{x1}" y1="{y0 - 4}" x2="{x1}" y2="{y1 + 4}" stroke="#FF0000" stroke-width="2" />'
                            )
                            svg.append(
                                f'  <path d="M{x1-4} {y0-8} L{x1+4} {y0-2} M{x1+4} {y0-8} L{x1-4} {y0-2}" stroke="#FF0000" stroke-width="2" fill="none" />'
                            )

        svg.append("</svg>")

        with open(caminho_arquivo, "w", encoding="utf-8") as f:
            f.write("\n".join(svg))

        self.criar_mensagem_aviso(
            f"Gráfico exportado em SVG:\n{caminho_arquivo}"
        )

    def criar_mensagem_erro(self, mensagem: str) -> None:
        print(f"[ERRO] {mensagem}")
        messagebox.showerror("Erro do Sistema", mensagem, parent=self.root)

    def criar_mensagem_aviso(self, mensagem: str) -> None:
        print(f"[AVISO] {mensagem}")
        messagebox.showwarning("Aviso do Sistema", mensagem, parent=self.root)

    def iniciar_loop(self):
        self.root.mainloop()
import os
import re
import tkinter as tk
from tkinter import filedialog, messagebox, ttk


def chave_ordenacao_y(x):
    """Ordena numericamente usando int(x) (Req. 2.5)."""
    try:
        return int(x)
    except (ValueError, TypeError):
        return 0


class GerenciadorGrafico:
    """Gerenciador gráfico do Simulador de SO com painéis de Fila de Prontos, Estado das CPUs, TCB detalhado e SVG."""

    def __init__(
        self, titulo="Simulador de SO - Dashboard", largura=1250, altura=780
    ):
        self.root = tk.Tk()
        self.root.title(titulo)
        self.root.geometry(f"{largura}x{altura}")

        self.on_carregar_ficheiro = None
        self.on_avancar = None
        self.on_retroceder = None
        self.on_editar_tarefa = None

        self.em_execucao = False
        self.delay_ms = 1
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

        # Painel Lateral expandido (Fila de Prontos, Estado das CPUs e Legenda)
        self.frame_lateral = tk.LabelFrame(
            self.frame_corpo, text="Depurador & Legenda", bg="#f9f9f9", width=220
        )
        self.frame_lateral.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))
        self.frame_lateral.pack_propagate(False)

        # Subpainel para Fila de Prontos
        self.lbl_sec_prontos = tk.Label(
            self.frame_lateral, text="📌 Fila de Prontos", font=("Arial", 9, "bold"), bg="#f9f9f9"
        )
        self.lbl_sec_prontos.pack(anchor="w", padx=5, pady=(5, 2))
        
        self.txt_prontos = tk.Label(
            self.frame_lateral, text="[ ]", font=("Consolas", 9), bg="#ffffff", relief="sunken", anchor="w", justify="left", width=26
        )
        self.txt_prontos.pack(padx=5, pady=2, fill=tk.X)

        # Subpainel para Estado das CPUs
        self.lbl_sec_cpus = tk.Label(
            self.frame_lateral, text="💻 Estado das CPUs", font=("Arial", 9, "bold"), bg="#f9f9f9"
        )
        self.lbl_sec_cpus.pack(anchor="w", padx=5, pady=(8, 2))

        self.txt_cpus_estado = tk.Label(
            self.frame_lateral, text="Nenhuma CPU ativa", font=("Consolas", 8), bg="#ffffff", relief="sunken", anchor="w", justify="left", width=26, height=4
        )
        self.txt_cpus_estado.pack(padx=5, pady=2, fill=tk.X)

        ttk.Separator(self.frame_lateral, orient="horizontal").pack(
            fill=tk.X, padx=5, pady=6
        )

        # Legenda existente
        self.frame_sub_legenda = tk.Frame(self.frame_lateral, bg="#f9f9f9")
        self.frame_sub_legenda.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        # Tabela TCB Detalhada na parte inferior (com coluna de Concluídas adicionada)
        self.frame_tcb = tk.LabelFrame(
            self.root, text="Bloco de Controlo de Tarefas (TCB Detalhado)", height=160
        )
        self.frame_tcb.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=5)
        self.frame_tcb.pack_propagate(False)

        colunas_tcb = (
            "ID",
            "Ingresso",
            "Duração",
            "Restante",
            "Período",
            "Deadline",
            "Concluídas",
            "Misses",
            "CPU",
            "Estado",
        )
        self.tabela_tcb = ttk.Treeview(
            self.frame_tcb, columns=colunas_tcb, show="headings", height=5
        )
        for col in colunas_tcb:
            self.tabela_tcb.heading(col, text=col)
            self.tabela_tcb.column(col, anchor="center", width=75)
        
        scroll_tcb_y = ttk.Scrollbar(self.frame_tcb, orient=tk.VERTICAL, command=self.tabela_tcb.yview)
        self.tabela_tcb.configure(yscrollcommand=scroll_tcb_y.set)
        
        self.tabela_tcb.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll_tcb_y.pack(side=tk.RIGHT, fill=tk.Y)

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
        fila_prontos = getattr(estado_simulacao, "fila_prontos", [])
        cpus_estado = getattr(estado_simulacao, "cpus_estado", [])

        self.atualizar_status(tick, algoritmo, cpus)
        self.atualizar_tabela_tcb(tarefas, gantt_history, tick)
        self.atualizar_painel_lateral(tarefas, fila_prontos, cpus_estado)
        self.desenhar_gantt(gantt_history, tarefas, cpus)
        self.root.update()

    def atualizar_status(self, tick, algoritmo, cpus):
        self.lbl_status.config(
            text=f"Tick: {tick} | Algo: {algoritmo} | CPUs: {cpus}"
        )

    def atualizar_tabela_tcb(self, tarefas, gantt_history, tick_atual):
        for item in self.tabela_tcb.get_children():
            self.tabela_tcb.delete(item)

        if isinstance(tarefas, list):
            tarefas_dict = {str(t.id): t for t in tarefas}
        else:
            tarefas_dict = {str(k): v for k, v in tarefas.items()}

        cpu_at_map = {}
        if tick_atual in gantt_history:
            for cpu_id, t_id in gantt_history[tick_atual].items():
                if t_id is not None:
                    cpu_at_map[str(t_id)] = f"C{cpu_id}"

        sorted_keys = sorted(tarefas_dict.keys(), key=chave_ordenacao_y)
        for t_id in sorted_keys:
            t = tarefas_dict[t_id]
            ingresso = getattr(t, "ingresso", 0)
            duracao = getattr(t, "duracao", 0)
            executado = getattr(t, "tempo_executado", 0)
            restante = max(0, duracao - executado)
            periodo = getattr(t, "periodo", "-")
            deadline = getattr(t, "deadline_absoluto", "-")
            concluidas = getattr(t, "execucoes_concluidas", 0)
            misses = sum(1 for ev in getattr(t, "historico_eventos", []) if ev.tipo == "DEADLINE_MISS")
            cpu_at = cpu_at_map.get(str(t_id), "-")
            estado = getattr(t, "estado", "AGUARDANDO")

            self.tabela_tcb.insert(
                "",
                tk.END,
                values=(str(t_id), ingresso, duracao, restante, periodo, deadline, concluidas, misses, cpu_at, estado),
            )

    def atualizar_painel_lateral(self, tarefas, fila_prontos, cpus_estado):
        # Atualiza texto da Fila de Prontos
        if fila_prontos:
            texto_prontos = ", ".join([f"T{t_id}" for t_id in fila_prontos])
        else:
            texto_prontos = "(vazia)"
        self.txt_prontos.config(text=f" [{texto_prontos}]")

        # Atualiza texto do Estado das CPUs
        linhas_cpu = []
        for c in cpus_estado:
            c_id = c["id"]
            t_exec = c["tarefa_atual"]
            t_str = f"Executando T{t_exec}" if t_exec else "Ociosa / Desligada"
            linhas_cpu.append(f"C{c_id}: {t_str}")
        self.txt_cpus_estado.config(text="\n".join(linhas_cpu) if linhas_cpu else "N/A")

        # Atualiza Legenda
        for widget in self.frame_sub_legenda.winfo_children():
            widget.destroy()

        if isinstance(tarefas, list):
            tarefas_dict = {str(t.id): t for t in tarefas}
        else:
            tarefas_dict = {str(k): v for k, v in tarefas.items()}

        lbl_sec_tarefas = tk.Label(
            self.frame_sub_legenda,
            text="Tarefas",
            font=("Arial", 9, "bold"),
            bg="#f9f9f9",
        )
        lbl_sec_tarefas.pack(anchor="w", padx=2, pady=(2, 2))

        sorted_keys = sorted(tarefas_dict.keys(), key=chave_ordenacao_y)
        for t_id in sorted_keys:
            task = tarefas_dict[t_id]
            cor_hex = getattr(task, "cor", "2196F3")
            cor = f"#{cor_hex}" if not str(cor_hex).startswith("#") else cor_hex

            item_frame = tk.Frame(self.frame_sub_legenda, bg="#f9f9f9")
            item_frame.pack(fill=tk.X, padx=2, pady=1)

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

        ttk.Separator(self.frame_sub_legenda, orient="horizontal").pack(
            fill=tk.X, padx=2, pady=4
        )

        lbl_sec_eventos = tk.Label(
            self.frame_sub_legenda,
            text="Legenda Gráfica",
            font=("Arial", 9, "bold"),
            bg="#f9f9f9",
        )
        lbl_sec_eventos.pack(anchor="w", padx=2, pady=(2, 2))

        icones = [
            ("↓", "green", "Chegada"),
            ("↑", "blue", "Conclusão"),
            ("✕", "red", "Deadline Miss"),
            ("⇡", "#FF8C00", "Ativação Ignorada"),
            ("S", "purple", "Sorteio"),
            ("■", "#cccccc", "CPU Desligada"),
            ("...", "black", "Tarefa Suspensa"),
        ]

        for sim, cor, desc in icones:
            item_frame = tk.Frame(self.frame_sub_legenda, bg="#f9f9f9")
            item_frame.pack(fill=tk.X, padx=2, pady=1)

            lbl_sym = tk.Label(
                item_frame,
                text=sim,
                fg=cor,
                bg="#f9f9f9",
                font=("Arial", 10, "bold"),
                width=2,
            )
            lbl_sym.pack(side=tk.LEFT, padx=(0, 2))

            lbl_txt = tk.Label(
                item_frame, text=desc, bg="#f9f9f9", font=("Arial", 8)
            )
            lbl_txt.pack(side=tk.LEFT)

    def desenhar_gantt(self, gantt_history: dict, tarefas, total_cpus=1):
        self.canvas_gantt.delete("all")
        if not tarefas:
            return

        if isinstance(tarefas, list):
            tarefas_dict = {str(t.id): t for t in tarefas}
        else:
            tarefas_dict = {str(k): v for k, v in tarefas.items()}

        cell_w = 32
        cell_h = 38
        margin_x = 75
        margin_y = 45

        sorted_task_ids = sorted(
            [str(k) for k in tarefas_dict.keys()], key=chave_ordenacao_y
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
                    task = tarefas_dict[task_key]
                    y_idx = sorted_task_ids.index(task_key)
                    y0 = margin_y + (y_idx * cell_h) + 3
                    y1 = y0 + cell_h - 6

                    cor_hex = getattr(task, "cor", "2196F3")
                    cor = (
                        f"#{cor_hex}"
                        if not str(cor_hex).startswith("#")
                        else str(cor_hex)
                    )

                    estado_t = getattr(task, "estado", "")
                    if estado_t == "SUSPENSA":
                        self.canvas_gantt.create_rectangle(
                            x0, y0, x1, y1, fill="#222222", outline="black", dash=(2, 2)
                        )
                    else:
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
                task = tarefas_dict[task_id]
                y_idx = sorted_task_ids.index(str(task_id))
                y0 = margin_y + (y_idx * cell_h) + 3
                y1 = y0 + cell_h - 6

                for ev in getattr(task, "historico_eventos", []):
                    if ev.tempo_inicio == tick:
                        if ev.tipo == "CHEGADA":
                            self.canvas_gantt.create_text(
                                x0 + 4,
                                y0 - 6,
                                text="↓",
                                fill="green",
                                font=("Arial", 10, "bold"),
                            )
                        elif ev.tipo == "FIM":
                            self.canvas_gantt.create_text(
                                x0 + 4,
                                y1 + 6,
                                text="↑",
                                fill="blue",
                                font=("Arial", 10, "bold"),
                            )
                        elif ev.tipo == "DEADLINE_MISS":
                            self.canvas_gantt.create_line(
                                x0, y0 - 2, x0, y1 + 2, fill="red", width=2
                            )
                            self.canvas_gantt.create_text(
                                x0,
                                y0 - 8,
                                text="✕",
                                fill="red",
                                font=("Arial", 10, "bold"),
                            )
                        elif ev.tipo == "ATIVACAO_IGNORADA":
                            self.canvas_gantt.create_line(
                                x0 + 5, y1 + 14, x0 + 5, y1 + 2,
                                arrow=tk.LAST, fill="#FF8C00",
                                dash=(2, 2), width=2,
                            )
                        elif ev.tipo == "SORTEIO":
                            self.canvas_gantt.create_text(
                                x0 + (cell_w / 2),
                                y0 + 12,
                                text="S",
                                fill="purple",
                                font=("Arial", 9, "bold"),
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
        ent_dl.insert(0, str(val_atuais[5]))
        ent_dl.grid(row=1, column=1, pady=2)

        tk.Label(frame_form, text="Estado:").grid(
            row=2, column=0, sticky="e", pady=2
        )
        cb_estado = ttk.Combobox(
            frame_form,
            values=["AGUARDANDO", "PRONTA", "EXECUTANDO", "SUSPENSA", "TERMINADA"],
            width=10,
            state="readonly",
        )
        cb_estado.set(val_atuais[9])  # Estado atualizado na coluna 9 devido à nova coluna
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
        tarefas,
        total_cpus: int = 1,
    ):
        cell_w = 36
        cell_h = 40
        margin_x = 90
        margin_y = 60

        if isinstance(tarefas, list):
            tarefas_norm = {str(t.id): t for t in tarefas}
        else:
            tarefas_norm = {str(k): v for k, v in tarefas.items()}

        sorted_task_ids = sorted(
            list(tarefas_norm.keys()), key=chave_ordenacao_y
        )
        num_ticks = max(len(gantt_history), 1)

        width = margin_x + (num_ticks * cell_w) + 140
        height = (
            margin_y + (len(sorted_task_ids) * cell_h) + 140
        )

        svg = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
            f'  <rect width="{width}" height="{height}" fill="#ffffff" />',
            '  <!-- Título -->',
            '  <text x="20" y="30" font-size="16" font-weight="bold" fill="#000000" font-family="sans-serif">Gráfico de Gantt - Simulador SO</text>',
        ]

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

                        estado_t = getattr(task, "estado", "")
                        if estado_t == "SUSPENSA":
                            svg.append(
                                f'  <rect x="{x0}" y="{y0}" width="{cell_w}" height="{cell_h - 8}" fill="#222222" stroke="#000000" stroke-dasharray="3,3" stroke-width="1" />'
                            )
                        else:
                            svg.append(
                                f'  <rect x="{x0}" y="{y0}" width="{cell_w}" height="{cell_h - 8}" fill="{cor}" stroke="#000000" stroke-width="1" />'
                            )

                        if total_cpus > 1:
                            svg.append(
                                f'  <text x="{x0 + (cell_w / 2)}" y="{y0 + 20}" font-size="9" font-weight="bold" fill="#ffffff" font-family="sans-serif" text-anchor="middle">C{cpu_id}</text>'
                            )

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
                                f'  <path d="M{x0+5} {y0-12} L{x0+5} {y0-2} M{x0+2} {y0-6} L{x0+5} {y0-2} L{x0+8} {y0-6}" stroke="#008000" stroke-width="2" fill="none" />'
                            )
                        elif ev.tipo == "FIM":
                            svg.append(
                                f'  <path d="M{x0+5} {y1+12} L{x0+5} {y1+2} M{x0+2} {y1+6} L{x0+5} {y1+2} L{x0+8} {y1+6}" stroke="#0000FF" stroke-width="2" fill="none" />'
                            )
                        elif ev.tipo == "DEADLINE_MISS":
                            svg.append(
                                f'  <line x1="{x0}" y1="{y0 - 4}" x2="{x0}" y2="{y1 + 4}" stroke="#FF0000" stroke-width="2" />'
                            )
                            svg.append(
                                f'  <path d="M{x0-4} {y0-8} L{x0+4} {y0-2} M{x0+4} {y0-8} L{x0-4} {y0-2}" stroke="#FF0000" stroke-width="2" fill="none" />'
                            )
                        elif ev.tipo == "ATIVACAO_IGNORADA":
                            svg.append(
                                f'  <path d="M{x0+5} {y1+14} L{x0+5} {y1+2} M{x0+2} {y1+6} L{x0+5} {y1+2} L{x0+8} {y1+6}" stroke="#FF8C00" stroke-width="2" stroke-dasharray="2,2" fill="none" />'
                            )
                        elif ev.tipo == "SORTEIO":
                            svg.append(
                                f'  <text x="{x0 + (cell_w / 2)}" y="{y0 + 14}" font-size="10" font-weight="bold" fill="purple" font-family="sans-serif" text-anchor="middle">S</text>'
                            )

        legenda_y = margin_y + (len(sorted_task_ids) * cell_h) + 30
        svg.append(f'  <g transform="translate({margin_x}, {legenda_y})">')
        svg.append(f'    <rect width="580" height="60" fill="#f9f9f9" stroke="#cccccc" rx="5"/>')
        svg.append(f'    <text x="15" y="20" font-size="12" font-weight="bold" fill="#000" font-family="sans-serif">Legenda de Eventos:</text>')
        svg.append(f'    <text x="15" y="42" font-size="11" fill="green" font-family="sans-serif">↓ Chegada</text>')
        svg.append(f'    <text x="95" y="42" font-size="11" fill="blue" font-family="sans-serif">↑ Conclusão</text>')
        svg.append(f'    <text x="180" y="42" font-size="11" fill="red" font-family="sans-serif">✕ Deadline Miss</text>')
        svg.append(f'    <text x="290" y="42" font-size="11" fill="#FF8C00" font-family="sans-serif">⇡ Ativação Ignorada</text>')
        svg.append(f'    <text x="420" y="42" font-size="11" fill="purple" font-family="sans-serif">S: Sorteio</text>')
        svg.append(f'    <text x="495" y="42" font-size="11" fill="#444" font-family="sans-serif">... Suspensa</text>')
        svg.append(f'  </g>')

        svg.append("</svg>")

        with open(caminho_arquivo, "w", encoding="utf-8") as f:
            f.write("\n".join(svg))

        self.criar_mensagem_aviso(
            f"Gráfico e legenda exportados com sucesso em SVG:\n{caminho_arquivo}"
        )

    def criar_mensagem_erro(self, mensagem: str) -> None:
        print(f"[ERRO] {mensagem}")
        messagebox.showerror("Erro do Sistema", mensagem, parent=self.root)

    def criar_mensagem_aviso(self, mensagem: str) -> None:
        print(f"[AVISO] {mensagem}")
        messagebox.showwarning("Aviso do Sistema", mensagem, parent=self.root)

    def iniciar_loop(self):
        self.root.mainloop()
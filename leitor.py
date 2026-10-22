from tcb import TCB
from escalonador import ESCALONADORES

class LeitorConfiguracao:
    # Construtor: executado ao criar um objeto
    def __init__(self, descricao="Classe que faz a leitura do arquivo txt e trata erros"):
        # Atributos de instância (da configuração) com valores padrão [req. 3.2]
        # Se o arquivo informar algo, ler() sobrescreve esses valores.
        self.escalonador = "RM"
        self.quantum = 1
        self.num_cpus = 1
        self.tarefas = []
        # Lista de mensagens de erro, para mostrar ao usuário depois
        self.erros = []
        self.avisos = [] # Alguns eventos devem ser notificados ao usuário, mas não são considerados erros
        self.descricao = descricao

    # Método de instância
    def ler(self, caminho):
        try:
            with open(caminho, encoding="utf-8") as f:      
                 # Lê todas as linhas, tira espaços e ignora as em branco [req. 3.3.6]
                linhas = [l.strip() for l in f if l.strip()]

            # Para não dar erro em linhas[0] e garantir o mínimo de linhas [req. 3.3.1]
            if len(linhas) < 2:
                self.erros.append("O arquivo precisa ter ao menos 2 linhas: sistema e uma tarefa.")
                return
            
            # A primeira linha é o cabeçalho, as demais são tarefas [req. 3.3.1]
            self._ler_cabecalho(linhas[0])

            for linha in linhas[1:]:
                self._ler_tarefa(linha)

        except FileNotFoundError:
            self.erros.append(f"Arquivo não encontrado: {caminho}")
        except PermissionError:
            self.erros.append(f"Sem permissão para ler: {caminho}")
        except IsADirectoryError:
            self.erros.append(f"O caminho é uma pasta, não um arquivo: {caminho}")
        except UnicodeDecodeError:
            self.erros.append(f"Encoding inválido em: {caminho}")

    def _ler_cabecalho(self, linha):
        # TODO: interpretar "algoritmo;quantum;qtde_cpus"
        campos = linha.rstrip(";").split(";")

        if len(campos) != 3:
            self.erros.append("Linha 1: esperado 'algoritmo;quantum;qtde_cpus'.")
            return

        algoritmo = campos[0].strip().upper()
        if algoritmo not in ESCALONADORES:
            self.erros.append(f"Linha 1: algoritmo '{algoritmo}' desconhecido (use RM ou EDF).")
        else:
            self.escalonador = algoritmo

        # Verificando se os dois valores são inteiros maiores que zero
        try:
            quantum = int(campos[1])
            num_cpus = int(campos[2])

            if quantum < 1 or num_cpus < 1:
                self.erros.append("Linha 1: quantum e qtde_cpus devem ser maiores que 0.")
            else:
                self.quantum = quantum
                self.num_cpus = num_cpus

        except ValueError:
            self.erros.append("Linha 1: quantum e qtde_cpus devem ser números inteiros.")
        

    def _ler_tarefa(self, linha):
        # O formato é id;cor;ingresso;duracao;periodo;prazo;lista_eventos

        campos = [c.strip() for c in linha.rstrip(";").split(";")]

        if len(campos) < 6: # O Sétimo campo é opcional
            self.erros.append(f"Tarefa inválida (faltam campos): '{linha}'")
            return
        
        try:
            id = int(campos[0])
            ingresso = int(campos[2])
            duracao = int(campos[3])
            periodo = int(campos[4])
            prazo = int(campos[5])
        except ValueError:
            self.erros.append(f"Tarefa com valor não numérico: '{linha}'")
            return

        cor = campos[1].upper()
        digitos_hex = "0123456789ABCDEF"

        if len(cor) != 6 or any(c not in digitos_hex for c in cor) :
            self.erros.append(f"Cor inválida '{campos[1]}' (use 6 dígitos hex, ex.: F0E0D0): '{linha}'")
            return

        if periodo < 0:
            self.erros.append(f"Período negativo: '{linha}'")
            return

        if periodo == 0:
            self.avisos.append(f"Tarefa {id} é aperiódica e foi ignorada (Projeto A só aceita periódicas).")
            return

        if ingresso < 0 or duracao < 1 or prazo < 1:
            self.erros.append(f"ingresso deve ser >= 0; duracao e prazo devem ser >= 1: '{linha}'")
            return

        if any(t.id == id for t in self.tarefas): # Se alguma tarefa tiver ID repetido
            self.erros.append(f"Id {id} repetido (o id deve ser único): '{linha}'")
            return

        eventos = campos[6:] # Guarda pro projeto B 

        self.tarefas.append(TCB(id, cor, ingresso, duracao, periodo, prazo, eventos)) # Adiciona na lista de tarefas uma instância de TCB


    # Representação em texto do objeto (opcional, mas útil para debugging)
    def __str__(self):
        return f"Pessoa({self.descricao})"


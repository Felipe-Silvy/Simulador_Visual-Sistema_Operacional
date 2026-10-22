import random

class EscalonadorStrategy:
    """
    Classe base (Strategy) para definir a estratégia de escalonamento de tarefas.
    Implementa a lógica comum de ordenação e tratamento de empates.
    """
    nome_politica = "BASE"

    def chave_prioridade(self, tcb):
        """
        Método abstrato que deve ser implementado pelas subclasses.
        Define o critério de prioridade específico de cada algoritmo.
        Menor valor numérico indica maior prioridade.
        """
        raise NotImplementedError("O algoritmo precisa implementar chave_prioridade")

    def selecionar(self, candidatas, num_cpus, tempo):
        """
        Seleciona as tarefas candidatas mais prioritárias para ocuparem as CPUs disponíveis.
        Trata também desempates e sorteios quando necessário.
        """
        # Ordena as candidatas da mais prioritária para a menos prioritária, usando desempate aleatório se necessário
        ordenadas = sorted(candidatas, key=lambda t: (self._chave_completa(t), random.random()))

        escolhidas = ordenadas[:num_cpus]
        sorteadas = []
        if len(ordenadas) > num_cpus:
            chave_corte = self._chave_completa(ordenadas[num_cpus - 1])
            if chave_corte == self._chave_completa(ordenadas[num_cpus]):
                # Caso o corte caia em um empate, as tarefas empatadas ganham via sorteio
                sorteadas = [t for t in escolhidas if self._chave_completa(t) == chave_corte]

        return escolhidas, sorteadas

    def _chave_completa(self, tcb):
        """
        Combina o critério principal do algoritmo com os critérios de desempate exigidos (req. 4.3),
        na seguinte ordem de preferência:
        1. Prioridade do algoritmo específico.
        2. Tarefas que já estão em execução (evita troca desnecessária de contexto).
        3. Prazo (deadline) mais próximo.
        4. Ordem de chegada (quem chegou primeiro).
        5. Menor duração.
        """
        return (
            self.chave_prioridade(tcb),                    # Critério principal do algoritmo
            0 if tcb.estado == "EXECUTANDO" else 1,        # 1º desempate: prioriza quem já está executando
            tcb.prazo,                                     # 2º desempate: prazo absoluto ou relativo
            tcb.ingresso,                                  # 3º desempate: ordem de chegada (FIFO)
            tcb.duracao,                                   # 4º desempate: menor duração de execução
        )

class EscalonadorRM(EscalonadorStrategy):
    """
    Implementação do escalonador Rate Monotonic (RM).
    Atribui prioridades estáticas com base no período da tarefa.
    """
    nome_politica = "RM"

    def chave_prioridade(self, tcb):
        return tcb.periodo              # Menor período tem maior prioridade (prioridade fixa)


class EscalonadorEDF(EscalonadorStrategy):
    """
    Implementação do escalonador Earliest Deadline First (EDF).
    Atribui prioridades dinâmicas com base no prazo absoluto da tarefa.
    """
    nome_politica = "EDF"

    def chave_prioridade(self, tcb):
        return tcb.deadline_absoluto    # Deadline mais próximo tem maior prioridade (prioridade dinâmica)

# Dicionário de mapeamento para instanciar os escalonadores disponíveis pelo nome
ESCALONADORES = {
    "RM": EscalonadorRM,
    "EDF": EscalonadorEDF,
}
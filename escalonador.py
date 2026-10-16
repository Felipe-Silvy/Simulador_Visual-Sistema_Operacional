import random

class EscalonadorStrategy:
    nome_politica = "BASE"

    def chave_prioridade(self, tcb):
        # Cada algoritmo define o seu critério. Menor valor = mais prioritária.
        raise NotImplementedError("O algoritmo precisa implementar chave_prioridade")

    def selecionar(self, candidatas, num_cpus, tempo):
        # Ordena da mais prioritária para a menos e devolve as 'num_cpus' primeiras
        ordenadas = sorted(candidatas, key=lambda t: (self._chave_completa(t), random.random()))

        escolhidas = ordenadas[:num_cpus]
        sorteadas = []
        if len(ordenadas) > num_cpus:
            chave_corte = self._chave_completa(ordenadas[num_cpus - 1])
            if chave_corte == self._chave_completa(ordenadas[num_cpus]):
                # o corte caiu no meio de um empate: as escolhidas empatadas venceram no sorteio
                sorteadas = [t for t in escolhidas if self._chave_completa(t) == chave_corte]

        return escolhidas, sorteadas

    def _chave_completa(self, tcb):
        # Critério principal do algoritmo + desempates do req. 4.3, nesta ordem
        return (
            self.chave_prioridade(tcb),                    # critério do algoritmoa
            0 if tcb.estado == "EXECUTANDO" else 1,        # 1º desempate: quem já executa
            tcb.prazo,                                     # 2º: prazo
            tcb.ingresso,                                  # 3º: quem chegou antes
            tcb.duracao,                                   # 4º: menor duração
        )

class EscalonadorRM(EscalonadorStrategy):
    nome_politica = "RM"

    def chave_prioridade(self, tcb):
        return tcb.periodo              # menor período vence (prioridade fixa)


class EscalonadorEDF(EscalonadorStrategy):
    nome_politica = "EDF"

    def chave_prioridade(self, tcb):
        return tcb.deadline_absoluto    # deadline mais próximo vence (prioridade dinâmica)

ESCALONADORES = {
    "RM": EscalonadorRM,
    "EDF": EscalonadorEDF,
}
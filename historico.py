class HistoricoSimulacao:
    """
    Gerencia a linha do tempo e o histórico de snapshots da simulação (Caretaker).
    Permite navegação linear (desfazer/refazer) e ramificação quando o passado é modificado.
    """
    def __init__(self):
        self._historico = []      # Lista sequencial de snapshots
        self._indice_atual = -1   # Aponta para o estado atual na linha do tempo

    def salvar(self, snapshot):
        """
        Salva um novo snapshot. Se estivermos a meio do histórico (após um 'desfazer')
        e uma nova ação for executada, o futuro alternativo é descartado (ramificação).
        """
        if self._indice_atual < len(self._historico) - 1:
            # Descarta o "futuro" a partir do ponto atual
            self._historico = self._historico[:self._indice_atual + 1]
        
        self._historico.append(snapshot)
        self._indice_atual += 1

    def desfazer(self):
        """
        Retrocede o relógio e o estado para o passo anterior na memória.
        Retorna o Snapshot correspondente ou None se estiver no início.
        """
        if self._indice_atual > 0:
            self._indice_atual -= 1
            return self._historico[self._indice_atual]
        return None

    def refazer(self):
        # Avança para o snapshot seguinte na memória (sem recalcular).
        if self._indice_atual < len(self._historico) - 1:
            self._indice_atual += 1
            return self._historico[self._indice_atual]
        return None

    def obter_atual(self):
        """Retorna o snapshot correspondente ao índice atual da linha do tempo."""
        if 0 <= self._indice_atual < len(self._historico):
            return self._historico[self._indice_atual]
        return None

    def invalidar_futuro_por_edicao(self):
        # Chamado quando o usuário modifica uma tarefa ou parâmetro no passado [Req. 1.5.2 e 3.4]
        if self._indice_atual < len(self._historico) - 1:
            self._historico = self._historico[:self._indice_atual + 1]

    def substituir_atual(self, snapshot):
        self._historico[self._indice_atual] = snapshot
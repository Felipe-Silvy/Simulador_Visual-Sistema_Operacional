class HistoricoSimulacao:
    """
    Gerencia a linha do tempo de estados (snapshots) da simulação.
    Permite navegar para trás (desfazer) e para a frente (refazer), além de
    descartar cenários futuros caso o usuário faça edições no passado.
    """
    def __init__(self):
        self._historico = []      # Lista sequencial de snapshots guardados
        self._indice_atual = -1   # Posição atual na linha do tempo

    def salvar(self, snapshot):
        # Se estivermos no meio do histórico e ocorra uma nova ação, descarta o futuro antigo
        if self._indice_atual < len(self._historico) - 1:
            self._historico = self._historico[:self._indice_atual + 1]
        
        self._historico.append(snapshot)
        self._indice_atual += 1

    def desfazer(self):
        # Volta um passo no tempo
        if self._indice_atual > 0:
            self._indice_atual -= 1
            return self._historico[self._indice_atual]
        return None

    def refazer(self):
        # Avança um passo no tempo (reaproveitando o futuro já calculado)
        if self._indice_atual < len(self._historico) - 1:
            self._indice_atual += 1
            return self._historico[self._indice_atual]
        return None

    def obter_atual(self):
        # Devolve o snapshot do instante em que a simulação se encontra
        if 0 <= self._indice_atual < len(self._historico):
            return self._historico[self._indice_atual]
        return None

    def invalidar_futuro_por_edicao(self):
        # Invalida o futuro recalculado quando uma tarefa ou o algoritmo muda a meio da execução
        if self._indice_atual < len(self._historico) - 1:
            self._historico = self._historico[:self._indice_atual + 1]

    def substituir_atual(self, snapshot):
        # Atualiza o snapshot do tick atual após alguma modificação de estado
        self._historico[self._indice_atual] = snapshot
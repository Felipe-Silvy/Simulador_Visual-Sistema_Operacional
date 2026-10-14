import sys
from leitor import LeitorConfiguracao
from simulador import Simulador

def main(): 
    caminho = input("Digite o caminho do arquivo de configuração: ")

    configuracao = LeitorConfiguracao()
    LeitorConfiguracao.ler(caminho)

    if configuracao.erros:
        for erro in configuracao.erros:
            print(erro)
        return          # MOSTRAR AO USUÁRIO POSTERIORMENTE NA INTERFACE

    simulador = Simulador( cpus=configuracao.num_cpus, tarefas=configuracao.tarefas, escalonador=configuracao.escalonador, )

    simulador.executar()

if __name__ == "__main__":
    main()
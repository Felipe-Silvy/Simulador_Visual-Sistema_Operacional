import sys
from leitor import LeitorConfiguracao
from simulador import Simulador
from escalonador import ESCALONADORES

def main(): 
    caminho = input("Digite o caminho do arquivo de configuração: ")

    configuracao = LeitorConfiguracao()
    configuracao.ler(caminho)

    if configuracao.erros:
        for erro in configuracao.erros:
            print(erro)
        return          # MOSTRAR AO USUÁRIO POSTERIORMENTE NA INTERFACE

    for aviso in configuracao.avisos: print(aviso)
    
    nome = configuracao.escalonador           
    classe = ESCALONADORES[nome]              
    escalonador = classe()    

    simulador = Simulador( num_cpus=configuracao.num_cpus, tarefas=configuracao.tarefas, escalonador=escalonador)
    simulador.executar()

if __name__ == "__main__":
    main()
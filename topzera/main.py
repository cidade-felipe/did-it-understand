'''CLI para avaliar respostas com Azure OpenAI.'''

from __future__ import annotations

import argparse
import sys

from avaliador_openai import ResultadoAvaliacaoIA, avaliar_resposta_com_ia, carregar_configuracao


def construir_parser() -> argparse.ArgumentParser:
    '''Monta o parser da CLI do avaliador baseado em Azure OpenAI.

    Esta funcao define o contrato de entrada da aplicacao. As flags principais
    sao ``--pergunta``, ``--esperada`` e ``--usuario``, que alimentam a
    avaliacao, e ``--check-config``, que permite validar o ambiente sem chamar
    a API e sem gerar custo.

    Centralizar essa definicao melhora manutencao da CLI e deixa explicito, em
    um unico lugar, quais combinacoes de uso o programa suporta.

    Returns:
        Parser configurado com as flags necessarias para avaliacao interativa,
        avaliacao por argumentos e verificacao isolada de configuracao.
    '''
    parser = argparse.ArgumentParser(
        description='Avalia semanticamente uma resposta usando uma implantacao do Azure OpenAI.',
    )
    parser.add_argument('--pergunta', help='Pergunta do exercicio.')
    parser.add_argument('--esperada', help='Resposta esperada pelo professor ou avaliador.')
    parser.add_argument('--usuario', help='Resposta fornecida pelo usuario.')
    parser.add_argument(
        '--check-config',
        action='store_true',
        help='Valida as variaveis de ambiente sem chamar a API.',
    )
    return parser


def ler_entrada_interativa() -> tuple[str, str, str]:
    '''Coleta dados de avaliacao diretamente do terminal.

    Este caminho e usado quando a pessoa executa a CLI sem informar os tres
    argumentos de avaliacao. As variaveis ``pergunta``, ``resposta_esperada`` e
    ``resposta_usuario`` sao coletadas por ``input`` e retornadas ja com
    ``strip`` aplicado, reduzindo ruido por espacos acidentais.

    O modo interativo e util para testes manuais, demonstracoes e depuracao
    rapida, porque elimina a necessidade de montar toda a linha de comando.

    Returns:
        Tupla com pergunta, resposta esperada e resposta do usuario.
    '''
    print('Avaliador semantico com Azure OpenAI')
    pergunta = input('Pergunta: ').strip()
    resposta_esperada = input('Resposta esperada: ').strip()
    resposta_usuario = input('Resposta do usuario: ').strip()
    return pergunta, resposta_esperada, resposta_usuario


def exibir_resultado(resultado: ResultadoAvaliacaoIA) -> None:
    '''Imprime o resultado da avaliacao semantica em formato legivel.

    A funcao recebe ``resultado`` ja consolidado e exibe os campos mais
    relevantes para tomada de decisao humana: ``feedback``, ``nota``,
    ``similaridade_semantica`` e ``justificativa``. Em seguida, delega a
    impressao das listas auxiliares para ``imprimir_lista``.

    O objetivo e transformar a resposta estruturada da IA em uma saida simples
    de terminal, boa o bastante para validacao manual, apresentacoes e uso em
    operacao leve sem interface grafica.

    Args:
        resultado: Estrutura retornada pelo avaliador com nota, feedback,
            justificativa e listas auxiliares produzidas pela IA.
    '''
    print('\nResultado da avaliacao')
    print(f'Feedback: {resultado.feedback}')
    print(f'Nota: {resultado.nota:.2f}/100')
    print(f'Similaridade semantica: {resultado.similaridade_semantica:.2%}')

    if resultado.justificativa:
        print(f'\nJustificativa: {resultado.justificativa}')

    imprimir_lista('Pontos corretos', resultado.pontos_corretos)
    imprimir_lista('Lacunas', resultado.lacunas)
    imprimir_lista('Alertas', resultado.alertas)


def imprimir_lista(titulo: str, itens: list[str]) -> None:
    '''Renderiza uma lista nomeada somente quando houver itens relevantes.

    As variaveis principais sao ``titulo``, que nomeia a secao, e ``itens``,
    que carrega o conteudo textual. A verificacao inicial evita imprimir blocos
    vazios, o que deixa a saida final mais limpa e mais facil de ler.

    Args:
        titulo: Rotulo exibido acima da lista.
        itens: Conteudo textual a ser impresso, um item por linha.
    '''
    if not itens:
        return
    print(f'\n{titulo}:')
    for item in itens:
        print(f'- {item}')


def executar_check_config() -> int:
    '''Valida a configuracao local sem consumir a API do Azure OpenAI.

    A funcao chama ``carregar_configuracao`` e expõe de forma amigavel os
    valores mais importantes da integracao, especialmente ``endpoint``,
    ``deployment`` e ``api_version``. Ela existe para separar um problema
    comum de operacao, ambiente mal configurado, de um problema de avaliacao em
    si.

    Isso economiza tempo e custo, porque a pessoa consegue validar o setup
    antes de abrir uma chamada real para o modelo.

    Returns:
        Codigo de saida ``0`` quando a configuracao minima foi encontrada e
        normalizada com sucesso.
    '''
    configuracao = carregar_configuracao()
    print('Configuracao encontrada.')
    print(f'Endpoint: {configuracao.endpoint}')
    print(f'Deployment: {configuracao.deployment}')
    print(f'API version: {configuracao.api_version}')
    return 0


def main() -> int:
    '''Orquestra a execucao principal da CLI semantica.

    Esta funcao concentra a jornada completa da aplicacao em terminal. A
    variavel ``args`` guarda os argumentos parseados, ``entradas`` verifica se
    a pessoa informou o trio completo de textos e o bloco ``try`` centraliza o
    tratamento de falhas operacionais em um retorno numerico simples.

    O fluxo cobre tres cenarios: validacao isolada de configuracao por
    ``--check-config``, avaliacao por argumentos e avaliacao interativa. Essa
    orquestracao em um unico ponto reduz duplicacao, facilita manutencao e
    deixa claro como a CLI transforma entrada humana em chamada ao avaliador.

    Returns:
        Codigo de saida do processo, onde ``0`` representa sucesso e ``1``
        indica erro operacional.
    '''
    parser = construir_parser()
    args = parser.parse_args()

    try:
        if args.check_config:
            return executar_check_config()

        entradas = [args.pergunta, args.esperada, args.usuario]
        if any(entradas) and not all(entradas):
            parser.error('Informe --pergunta, --esperada e --usuario juntos, ou rode sem argumentos.')

        if all(entradas):
            pergunta, resposta_esperada, resposta_usuario = args.pergunta, args.esperada, args.usuario
        else:
            pergunta, resposta_esperada, resposta_usuario = ler_entrada_interativa()

        resultado = avaliar_resposta_com_ia(
            pergunta=pergunta,
            resposta_esperada=resposta_esperada,
            resposta_usuario=resposta_usuario,
        )
        exibir_resultado(resultado)
        return 0
    except Exception as erro:
        print(f'Erro: {erro}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())

'''CLI para avaliar respostas com Azure OpenAI.'''

from __future__ import annotations

import argparse
import sys

from avaliador_openai import ResultadoAvaliacaoIA, avaliar_resposta_com_ia, carregar_configuracao


def construir_parser() -> argparse.ArgumentParser:
    '''Monta o parser da CLI do avaliador baseado em Azure OpenAI.

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

    Esse modo e util para testes manuais e demonstracoes em que a pessoa
    prefere digitar as respostas em vez de montar a chamada completa por flags.

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

    A funcao trata parsing de argumentos, escolha entre modo interativo e
    automatizado, execucao do check de configuracao e traducao de excecoes para
    codigo de saida apropriado em terminal.

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

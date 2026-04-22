'''Interface de linha de comando para avaliar respostas com PLN.'''

from __future__ import annotations

import argparse
from textwrap import dedent

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from avaliador import ConfiguracaoAvaliacao, ResultadoAvaliacao, avaliar_resposta


console = Console()


def construir_parser() -> argparse.ArgumentParser:
    '''Monta o parser da linha de comando para o avaliador local.

    O parser concentra as opcoes que controlam entrada de dados e modo de
    exibicao, reduzindo duplicacao e mantendo o contrato da CLI explicito para
    uso manual, scripts e demonstracoes.

    Returns:
        Instancia de ``ArgumentParser`` pronta para interpretar os argumentos
        suportados por esta interface.
    '''
    parser = argparse.ArgumentParser(
        description='Avalia se uma resposta do usuario esta proxima da resposta esperada.',
    )
    parser.add_argument('--pergunta', help='Pergunta usada no exercicio.')
    parser.add_argument('--esperada', help='Resposta esperada pelo avaliador.')
    parser.add_argument('--usuario', help='Resposta fornecida pelo usuario.')
    parser.add_argument(
        '--manter-stopwords',
        action='store_true',
        help='Mantem stopwords no pre-processamento.',
    )
    parser.add_argument(
        '--detalhes',
        action='store_true',
        help='Mostra detalhes do pre-processamento e da analise.',
    )
    parser.add_argument(
        '--sem-stemming',
        action='store_true',
        help='Desliga o stemming do NLTK. Use para comparar antes e depois da inteligencia linguistica.',
    )
    return parser


def ler_entrada_interativa() -> tuple[str, str, str]:
    '''Coleta pergunta e respostas diretamente do terminal.

    Esse caminho e usado quando a CLI e executada sem argumentos, o que facilita
    testes rapidos e apresentacoes sem exigir que o usuario memorize flags.

    Returns:
        Tupla com pergunta, resposta esperada e resposta do usuario, sempre com
        espacos excedentes removidos nas extremidades.
    '''
    console.print(Panel.fit('Modo interativo: avaliador de respostas com PLN', title='Did It Understand?'))
    pergunta = input('Pergunta: ').strip()
    resposta_esperada = input('Resposta esperada: ').strip()
    resposta_usuario = input('Resposta do usuario: ').strip()
    return pergunta, resposta_esperada, resposta_usuario


def exibir_resultado(resultado: ResultadoAvaliacao, mostrar_detalhes: bool = False) -> None:
    '''Renderiza o resultado da avaliacao em formato amigavel no terminal.

    A tabela principal resume as metricas mais importantes para leitura rapida.
    Quando ``mostrar_detalhes`` esta habilitado, a funcao tambem exibe os
    artefatos do pre-processamento e as observacoes geradas pelo avaliador,
    o que ajuda a explicar como a nota foi formada.

    Args:
        resultado: Objeto retornado pelo motor de avaliacao com todos os dados
            relevantes da analise.
        mostrar_detalhes: Define se os detalhes tecnicos do processamento devem
            ser impressos junto ao resumo executivo.
    '''
    tabela = Table(title='Resultado da avaliacao')
    tabela.add_column('Metrica')
    tabela.add_column('Valor', justify='right')
    tabela.add_row('Pergunta', resultado.pergunta)
    tabela.add_row('Nota final', f'{resultado.nota:.2f}/100')
    tabela.add_row('Feedback', resultado.feedback)
    tabela.add_row('Similaridade TF-IDF', f'{resultado.similaridade:.2%}')
    tabela.add_row('Cobertura de palavras-chave', f'{resultado.cobertura_palavras_chave:.2%}')
    console.print(tabela)

    if mostrar_detalhes:
        console.print('\n[bold]Detalhes[/bold]')
        console.print(
            dedent(
                f'''\
                Tokens da resposta esperada: {' '.join(resultado.resposta_esperada_processada.tokens)}
                Tokens da resposta do usuario: {' '.join(resultado.resposta_usuario_processada.tokens)}
                Radicais usados na comparacao, esperada: {resultado.resposta_esperada_processada.texto_processado}
                Radicais usados na comparacao, usuario: {resultado.resposta_usuario_processada.texto_processado}
                Palavras-chave esperadas: {', '.join(resultado.palavras_chave_esperadas) or 'nenhuma'}
                Palavras-chave encontradas: {', '.join(resultado.palavras_chave_encontradas) or 'nenhuma'}
                '''
            ).strip()
        )

    if resultado.observacoes:
        console.print('\n[bold]Leitura do resultado[/bold]')
        for observacao in resultado.observacoes:
            console.print(f'- {observacao}')


def main() -> None:
    '''Executa o fluxo principal da CLI do avaliador baseado em PLN.

    A funcao decide entre modo interativo e modo por argumentos, valida se a
    entrada esta completa, monta a configuracao operacional e delega a analise
    ao modulo avaliador. O objetivo e concentrar a orquestracao da interface em
    um unico ponto facil de manter.
    '''
    parser = construir_parser()
    args = parser.parse_args()

    entradas_preenchidas = [args.pergunta, args.esperada, args.usuario]
    if any(entradas_preenchidas) and not all(entradas_preenchidas):
        parser.error('Informe --pergunta, --esperada e --usuario juntos, ou rode sem argumentos.')

    if all(entradas_preenchidas):
        pergunta, resposta_esperada, resposta_usuario = (
            args.pergunta,
            args.esperada,
            args.usuario,
        )
    else:
        pergunta, resposta_esperada, resposta_usuario = ler_entrada_interativa()

    configuracao = ConfiguracaoAvaliacao(
        remover_stopwords=not args.manter_stopwords,
        aplicar_stemming=not args.sem_stemming,
    )
    resultado = avaliar_resposta(
        pergunta=pergunta,
        resposta_esperada=resposta_esperada,
        resposta_usuario=resposta_usuario,
        configuracao=configuracao,
    )
    exibir_resultado(resultado, mostrar_detalhes=args.detalhes)


if __name__ == '__main__':
    main()

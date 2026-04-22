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

    Esta funcao centraliza o contrato da interface de linha de comando. As
    flags mais importantes sao ``--pergunta``, ``--esperada`` e ``--usuario``,
    que alimentam diretamente o motor de avaliacao, alem de
    ``--manter-stopwords``, ``--sem-stemming`` e ``--detalhes``, que alteram
    o comportamento do pre-processamento e da exibicao.

    Concentrar a definicao dessas opcoes em um unico ponto reduz duplicacao e
    facilita manutencao, porque qualquer ajuste na forma como a CLI recebe
    dados fica isolado aqui e nao espalhado pela orquestracao principal.

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

    Esse fluxo e acionado quando a aplicacao e executada sem argumentos. As
    variaveis retornadas, ``pergunta``, ``resposta_esperada`` e
    ``resposta_usuario``, sao exatamente as mesmas consumidas pelo avaliador,
    apenas capturadas por ``input`` em vez de flags da CLI.

    O ``strip`` aplicado em cada campo evita que espacos acidentais nas
    extremidades contaminem a avaliacao, o que melhora a consistencia entre
    uso manual e uso automatizado.

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

    A funcao recebe o objeto ``resultado`` ja consolidado e traduz esse
    conteudo para uma visualizacao mais facil de consumir por quem esta
    executando o projeto manualmente. Os campos mais importantes exibidos na
    tabela sao ``nota``, ``feedback``, ``similaridade`` e
    ``cobertura_palavras_chave``, porque eles resumem desempenho, classificacao
    final e os dois sinais que sustentam a nota.

    Quando ``mostrar_detalhes`` esta ativo, a exibicao aprofunda a leitura com
    tokens, radicais de comparacao e listas de palavras-chave. Isso e
    especialmente util para depuracao, para explicar resultados em sala ou
    para calibrar regras de pre-processamento sem precisar instrumentar o
    codigo manualmente.

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

    Esta funcao orquestra toda a experiencia de uso no terminal. A variavel
    ``args`` concentra o resultado do parsing, ``entradas_preenchidas`` decide
    se a execucao seguira por argumentos ou por coleta interativa, e
    ``configuracao`` traduz as flags da CLI em parametros concretos para o
    motor de avaliacao.

    O ponto principal desta funcao nao e calcular a nota, e sim garantir que o
    contrato de entrada seja respeitado. Isso evita cenarios em que parte dos
    dados chega por argumento e parte fica ausente, o que reduziria a
    confiabilidade da avaliacao e aumentaria o custo de suporte.
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

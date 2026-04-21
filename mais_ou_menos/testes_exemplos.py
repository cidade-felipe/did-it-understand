"""Executa exemplos prontos para apoiar a apresentacao do trabalho."""

from __future__ import annotations

import json
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from avaliador import avaliar_resposta


ARQUIVO_EXEMPLOS = Path(__file__).with_name("exemplos.json")
console = Console()


def carregar_exemplos() -> list[dict[str, str]]:
    """Carrega a bateria de exemplos usada nas demonstracoes do projeto.

    O arquivo JSON centraliza cenarios prontos para comparacao entre expectativa
    humana e resultado do sistema, o que facilita reproducao durante testes
    manuais, apresentacoes e analises criticas.

    Returns:
        Lista de dicionarios com pergunta, respostas e expectativa associada a
        cada cenario.
    """
    return json.loads(ARQUIVO_EXEMPLOS.read_text(encoding="utf-8"))


def main() -> None:
    """Executa todos os exemplos cadastrados e imprime um resumo comparativo.

    A funcao funciona como uma bateria demonstrativa de casos conhecidos,
    destacando o comportamento do sistema em cada cenario e quantificando
    quantas vezes o feedback automatico bateu com a expectativa humana.
    """
    exemplos = carregar_exemplos()
    acertos = 0
    tabela = Table(title="Bateria de exemplos")
    tabela.add_column("#", justify="right")
    tabela.add_column("Cenario")
    tabela.add_column("Humano")
    tabela.add_column("Sistema")
    tabela.add_column("Nota", justify="right")
    tabela.add_column("Similaridade", justify="right")

    for indice, exemplo in enumerate(exemplos, start=1):
        resultado = avaliar_resposta(
            pergunta=exemplo["pergunta"],
            resposta_esperada=exemplo["resposta_esperada"],
            resposta_usuario=exemplo["resposta_usuario"],
        )
        acertou = resultado.feedback == exemplo["expectativa"]
        acertos += int(acertou)
        tabela.add_row(
            str(indice),
            exemplo["nome"],
            exemplo["expectativa"],
            resultado.feedback,
            f"{resultado.nota:.2f}",
            f"{resultado.similaridade:.2%}",
        )

        console.print(Panel.fit(f"Exemplo {indice}: {exemplo['nome']}", title="Analise individual"))
        console.print(f"Expectativa humana: {exemplo['expectativa']}")
        console.print(f"Resultado do sistema: {resultado.feedback}")
        console.print(f"Nota: {resultado.nota:.2f}")
        console.print(f"Similaridade: {resultado.similaridade:.2%}")
        console.print(f"Palavras-chave encontradas: {', '.join(resultado.palavras_chave_encontradas) or 'nenhuma'}")

        for observacao in resultado.observacoes:
            console.print(f"- {observacao}")

    total = len(exemplos)
    console.print(tabela)
    console.print("\n[bold]Resumo[/bold]")
    console.print(f"O sistema bateu com a expectativa humana em {acertos} de {total} exemplos.")
    console.print(
        "Quando houver divergencia, isso pode ser usado na analise critica para mostrar que "
        "similaridade textual nao equivale a compreensao semantica."
    )


if __name__ == "__main__":
    main()

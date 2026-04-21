"""Testes basicos para garantir o comportamento principal do avaliador."""

from __future__ import annotations

import unittest

from avaliador import avaliar_resposta
from preprocessamento import preprocessar_texto


class TestPreprocessamento(unittest.TestCase):
    def test_remove_acentos_e_pontuacao(self) -> None:
        """Verifica se a limpeza textual remove ruido basico do enunciado.

        O teste protege contra regressao em uma etapa critica do pipeline,
        porque manter acentos ou pontuacao indevida aumentaria falsos negativos
        na comparacao entre respostas equivalentes.
        """
        processado = preprocessar_texto("Computacao, linguagem e analise!")
        self.assertEqual(processado.tokens, ["computacao", "linguagem", "analise"])
        self.assertEqual(len(processado.tokens_comparacao), 3)

    def test_stemming_aproxima_variacoes_da_mesma_palavra(self) -> None:
        """Confirma que flexoes proximas convergem para o mesmo radical.

        Sem essa garantia, respostas semanticamente corretas poderiam receber
        notas artificilamente menores apenas por diferencas morfologicas.
        """
        esperado = preprocessar_texto("processar analisar")
        usuario = preprocessar_texto("processa analise")
        self.assertEqual(esperado.tokens_comparacao, usuario.tokens_comparacao)


class TestAvaliador(unittest.TestCase):
    def test_resposta_identica_recebe_nota_maxima(self) -> None:
        """Garante o caso ideal em que referencia e usuario sao identicos.

        Esse teste valida o teto da escala e ajuda a detectar regressao em
        pesos, pre-processamento ou arredondamento da nota final.
        """
        resposta = "PLN e a area da computacao que processa linguagem humana."
        resultado = avaliar_resposta("O que e PLN?", resposta, resposta)
        self.assertEqual(resultado.feedback, "Entendeu")
        self.assertEqual(resultado.nota, 100.0)

    def test_resposta_vazia_recebe_nota_baixa(self) -> None:
        """Assegura que ausencia de conteudo nao seja interpretada como acerto.

        O objetivo e mitigar risco de falso positivo quando a entrada fica
        vazia apos o pre-processamento ou o usuario simplesmente nao responde.
        """
        resultado = avaliar_resposta(
            "O que e PLN?",
            "PLN e a area da computacao que processa linguagem humana.",
            "",
        )
        self.assertEqual(resultado.feedback, "Nao entendeu")
        self.assertEqual(resultado.nota, 0.0)

    def test_resposta_errada_fica_abaixo_do_limite_parcial(self) -> None:
        """Valida que uma resposta fora do tema fique abaixo da faixa parcial.

        Esse caso cobre uma regressao importante de negocio: evitar que o
        sistema premie textos fluentemente escritos, mas semanticamente errados.
        """
        resultado = avaliar_resposta(
            "O que e PLN?",
            "PLN e a area da computacao que processa linguagem humana.",
            "PLN e um programa de planilhas usado para organizar contas.",
        )
        self.assertEqual(resultado.feedback, "Nao entendeu")
        self.assertLess(resultado.nota, 45.0)


if __name__ == "__main__":
    unittest.main()

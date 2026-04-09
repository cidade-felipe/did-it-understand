"""Testes basicos para garantir o comportamento principal do avaliador."""

from __future__ import annotations

import unittest

from avaliador import avaliar_resposta
from preprocessamento import preprocessar_texto


class TestPreprocessamento(unittest.TestCase):
    def test_remove_acentos_e_pontuacao(self) -> None:
        processado = preprocessar_texto("Computacao, linguagem e analise!")
        self.assertEqual(processado.tokens, ["computacao", "linguagem", "analise"])
        self.assertEqual(len(processado.tokens_comparacao), 3)

    def test_stemming_aproxima_variacoes_da_mesma_palavra(self) -> None:
        esperado = preprocessar_texto("processar analisar")
        usuario = preprocessar_texto("processa analise")
        self.assertEqual(esperado.tokens_comparacao, usuario.tokens_comparacao)


class TestAvaliador(unittest.TestCase):
    def test_resposta_identica_recebe_nota_maxima(self) -> None:
        resposta = "PLN e a area da computacao que processa linguagem humana."
        resultado = avaliar_resposta("O que e PLN?", resposta, resposta)
        self.assertEqual(resultado.feedback, "Entendeu")
        self.assertEqual(resultado.nota, 100.0)

    def test_resposta_vazia_recebe_nota_baixa(self) -> None:
        resultado = avaliar_resposta(
            "O que e PLN?",
            "PLN e a area da computacao que processa linguagem humana.",
            "",
        )
        self.assertEqual(resultado.feedback, "Nao entendeu")
        self.assertEqual(resultado.nota, 0.0)

    def test_resposta_errada_fica_abaixo_do_limite_parcial(self) -> None:
        resultado = avaliar_resposta(
            "O que e PLN?",
            "PLN e a area da computacao que processa linguagem humana.",
            "PLN e um programa de planilhas usado para organizar contas.",
        )
        self.assertEqual(resultado.feedback, "Nao entendeu")
        self.assertLess(resultado.nota, 45.0)


if __name__ == "__main__":
    unittest.main()

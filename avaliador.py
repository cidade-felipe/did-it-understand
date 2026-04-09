"""Motor de avaliacao de respostas com TF-IDF e similaridade do cosseno."""

from __future__ import annotations

from dataclasses import dataclass, field

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from preprocessamento import (
    TextoProcessado,
    extrair_palavras_chave,
    preprocessar_texto,
    radicalizar_token,
)


@dataclass(slots=True)
class ConfiguracaoAvaliacao:
    remover_stopwords: bool = True
    aplicar_stemming: bool = True
    peso_similaridade: float = 0.8
    peso_palavras_chave: float = 0.2
    limite_palavras_chave: int = 6
    limite_entendeu: float = 70.0
    limite_parcial: float = 30.0

    def soma_pesos(self) -> float:
        return self.peso_similaridade + self.peso_palavras_chave


@dataclass(slots=True)
class ResultadoAvaliacao:
    pergunta: str
    resposta_esperada: str
    resposta_usuario: str
    resposta_esperada_processada: TextoProcessado
    resposta_usuario_processada: TextoProcessado
    similaridade: float
    cobertura_palavras_chave: float
    nota: float
    feedback: str
    palavras_chave_esperadas: list[str] = field(default_factory=list)
    palavras_chave_encontradas: list[str] = field(default_factory=list)
    observacoes: list[str] = field(default_factory=list)


def _validar_configuracao(configuracao: ConfiguracaoAvaliacao) -> None:
    if configuracao.soma_pesos() <= 0:
        raise ValueError("A soma dos pesos precisa ser maior que zero.")
    if configuracao.limite_parcial > configuracao.limite_entendeu:
        raise ValueError("O limite de parcial nao pode ser maior que o limite de entendeu.")


def calcular_similaridade_tfidf(tokens_esperados: list[str], tokens_usuario: list[str]) -> float:
    documento_esperado = " ".join(tokens_esperados)
    documento_usuario = " ".join(tokens_usuario)
    if not documento_esperado or not documento_usuario:
        return 0.0

    vetorizador = TfidfVectorizer(
        lowercase=False,
        preprocessor=None,
        tokenizer=str.split,
        token_pattern=None,
    )
    matriz_tfidf = vetorizador.fit_transform([documento_esperado, documento_usuario])
    matriz_similaridade = cosine_similarity(matriz_tfidf[0:1], matriz_tfidf[1:2])
    return float(matriz_similaridade[0, 0])


def _classificar_feedback(nota: float, configuracao: ConfiguracaoAvaliacao) -> str:
    if nota >= configuracao.limite_entendeu:
        return "Entendeu"
    if nota >= configuracao.limite_parcial:
        return "Parcial"
    return "Nao entendeu"


def _gerar_observacoes(
    resposta_esperada: TextoProcessado,
    resposta_usuario: TextoProcessado,
    similaridade: float,
    cobertura_palavras_chave: float,
    palavras_chave_encontradas: list[str],
) -> list[str]:
    observacoes: list[str] = []

    if not resposta_usuario.tokens:
        observacoes.append(
            "A resposta do usuario ficou vazia depois do pre-processamento, por isso a nota foi zerada."
        )
        return observacoes

    if similaridade >= 0.75:
        observacoes.append("A estrutura textual ficou bem proxima da resposta esperada.")
    elif similaridade >= 0.4:
        observacoes.append("Ha proximidade textual moderada entre as respostas.")
    else:
        observacoes.append("A proximidade textual ficou baixa, indicando pouca sobreposicao de termos.")

    if cobertura_palavras_chave == 0:
        observacoes.append("Nenhuma palavra-chave principal da resposta esperada apareceu na resposta do usuario.")
    elif cobertura_palavras_chave < 0.5:
        observacoes.append("A resposta cobriu apenas parte das palavras-chave mais importantes.")
    else:
        observacoes.append("A resposta recuperou boa parte das palavras-chave centrais.")

    proporcao_tamanho = len(resposta_usuario.tokens) / max(len(resposta_esperada.tokens), 1)
    if proporcao_tamanho < 0.5:
        observacoes.append(
            "A resposta do usuario e bem mais curta que a esperada, o que pode indicar explicacao incompleta."
        )

    if palavras_chave_encontradas:
        observacoes.append(
            "Palavras-chave encontradas: " + ", ".join(palavras_chave_encontradas) + "."
        )

    return observacoes


def avaliar_resposta(
    pergunta: str,
    resposta_esperada: str,
    resposta_usuario: str,
    configuracao: ConfiguracaoAvaliacao | None = None,
) -> ResultadoAvaliacao:
    configuracao = configuracao or ConfiguracaoAvaliacao()
    _validar_configuracao(configuracao)

    if not str(resposta_esperada).strip():
        raise ValueError("A resposta esperada nao pode ser vazia.")

    resposta_esperada_proc = preprocessar_texto(
        resposta_esperada,
        remover_stopwords=configuracao.remover_stopwords,
        aplicar_stemming=configuracao.aplicar_stemming,
    )
    resposta_usuario_proc = preprocessar_texto(
        resposta_usuario,
        remover_stopwords=configuracao.remover_stopwords,
        aplicar_stemming=configuracao.aplicar_stemming,
    )

    palavras_chave = extrair_palavras_chave(
        resposta_esperada_proc.tokens,
        limite=configuracao.limite_palavras_chave,
    )
    palavras_usuario = set(resposta_usuario_proc.tokens)
    radicais_usuario = set(resposta_usuario_proc.tokens_comparacao)
    palavras_encontradas = [
        palavra
        for palavra in palavras_chave
        if palavra in palavras_usuario or radicalizar_token(palavra) in radicais_usuario
    ]
    cobertura_palavras_chave = (
        len(palavras_encontradas) / len(palavras_chave) if palavras_chave else 0.0
    )

    similaridade = calcular_similaridade_tfidf(
        resposta_esperada_proc.tokens_comparacao,
        resposta_usuario_proc.tokens_comparacao,
    )

    nota_base = (
        (similaridade * configuracao.peso_similaridade)
        + (cobertura_palavras_chave * configuracao.peso_palavras_chave)
    ) / configuracao.soma_pesos()
    nota = round(nota_base * 100, 2)
    feedback = _classificar_feedback(nota, configuracao)

    observacoes = _gerar_observacoes(
        resposta_esperada_proc,
        resposta_usuario_proc,
        similaridade,
        cobertura_palavras_chave,
        palavras_encontradas,
    )

    return ResultadoAvaliacao(
        pergunta=pergunta,
        resposta_esperada=resposta_esperada,
        resposta_usuario=resposta_usuario,
        resposta_esperada_processada=resposta_esperada_proc,
        resposta_usuario_processada=resposta_usuario_proc,
        similaridade=similaridade,
        cobertura_palavras_chave=cobertura_palavras_chave,
        nota=nota,
        feedback=feedback,
        palavras_chave_esperadas=palavras_chave,
        palavras_chave_encontradas=palavras_encontradas,
        observacoes=observacoes,
    )

"""Funcoes de pre-processamento para o trabalho de PLN."""

from __future__ import annotations

from dataclasses import dataclass
import re

from nltk.stem import SnowballStemmer
from unidecode import unidecode


STEMMER_PORTUGUES = SnowballStemmer("portuguese")


STOPWORDS_PADRAO = {
    "a",
    "ao",
    "aos",
    "aquela",
    "aquelas",
    "aquele",
    "aqueles",
    "aquilo",
    "as",
    "ate",
    "com",
    "como",
    "da",
    "das",
    "de",
    "dela",
    "dele",
    "deles",
    "delas",
    "depois",
    "do",
    "dos",
    "e",
    "ela",
    "elas",
    "ele",
    "eles",
    "em",
    "entre",
    "era",
    "eram",
    "essa",
    "essas",
    "esse",
    "esses",
    "esta",
    "estao",
    "estas",
    "este",
    "estes",
    "eu",
    "foi",
    "foram",
    "ha",
    "isso",
    "isto",
    "ja",
    "la",
    "lhe",
    "lhes",
    "mais",
    "mas",
    "me",
    "mesmo",
    "meu",
    "meus",
    "minha",
    "minhas",
    "muito",
    "na",
    "nao",
    "nas",
    "nem",
    "no",
    "nos",
    "nossa",
    "nossas",
    "nosso",
    "nossos",
    "num",
    "numa",
    "o",
    "os",
    "ou",
    "para",
    "pela",
    "pelas",
    "pelo",
    "pelos",
    "por",
    "qual",
    "quando",
    "que",
    "quem",
    "se",
    "sem",
    "ser",
    "sera",
    "seu",
    "seus",
    "sua",
    "suas",
    "tambem",
    "te",
    "tem",
    "tendo",
    "tenho",
    "ter",
    "tinha",
    "tinham",
    "um",
    "uma",
    "voce",
    "voces",
}


@dataclass(slots=True)
class TextoProcessado:
    original: str
    normalizado: str
    tokens: list[str]
    tokens_comparacao: list[str]
    texto_processado: str


def remover_acentos(texto: str) -> str:
    return unidecode(texto)


def normalizar_texto(texto: str) -> str:
    texto = "" if texto is None else str(texto)
    texto = remover_acentos(texto.lower()).strip()
    texto = re.sub(r"[^\w\s]", " ", texto, flags=re.UNICODE)
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto


def tokenizar(texto: str) -> list[str]:
    if not texto:
        return []
    return re.findall(r"[a-z0-9]+", texto)


def radicalizar_token(token: str) -> str:
    return STEMMER_PORTUGUES.stem(token)


def preprocessar_texto(
    texto: str,
    remover_stopwords: bool = True,
    aplicar_stemming: bool = True,
    stopwords: set[str] | None = None,
) -> TextoProcessado:
    normalizado = normalizar_texto(texto)
    tokens = tokenizar(normalizado)

    stopwords_ativas = STOPWORDS_PADRAO if stopwords is None else stopwords
    if remover_stopwords:
        tokens = [
            token
            for token in tokens
            if token not in stopwords_ativas and (len(token) > 1 or token.isdigit())
        ]

    tokens_comparacao = [radicalizar_token(token) for token in tokens] if aplicar_stemming else tokens

    return TextoProcessado(
        original="" if texto is None else str(texto),
        normalizado=normalizado,
        tokens=tokens,
        tokens_comparacao=tokens_comparacao,
        texto_processado=" ".join(tokens_comparacao),
    )


def extrair_palavras_chave(tokens: list[str], limite: int = 6) -> list[str]:
    if limite <= 0:
        return []

    frequencia: dict[str, int] = {}
    primeira_posicao: dict[str, int] = {}

    for indice, token in enumerate(tokens):
        if len(token) <= 2:
            continue
        frequencia[token] = frequencia.get(token, 0) + 1
        primeira_posicao.setdefault(token, indice)

    ordenadas = sorted(
        frequencia,
        key=lambda token: (-frequencia[token], primeira_posicao[token], token),
    )
    return ordenadas[:limite]

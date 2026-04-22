'''Funcoes de pre-processamento para o trabalho de PLN.'''

from __future__ import annotations

from dataclasses import dataclass
import re

from nltk.stem import SnowballStemmer
from unidecode import unidecode


STEMMER_PORTUGUES = SnowballStemmer('portuguese')


STOPWORDS_PADRAO = {
    'a',
    'ao',
    'aos',
    'aquela',
    'aquelas',
    'aquele',
    'aqueles',
    'aquilo',
    'as',
    'ate',
    'com',
    'como',
    'da',
    'das',
    'de',
    'dela',
    'dele',
    'deles',
    'delas',
    'depois',
    'do',
    'dos',
    'e',
    'ela',
    'elas',
    'ele',
    'eles',
    'em',
    'entre',
    'era',
    'eram',
    'essa',
    'essas',
    'esse',
    'esses',
    'esta',
    'estao',
    'estas',
    'este',
    'estes',
    'eu',
    'foi',
    'foram',
    'ha',
    'isso',
    'isto',
    'ja',
    'la',
    'lhe',
    'lhes',
    'mais',
    'mas',
    'me',
    'mesmo',
    'meu',
    'meus',
    'minha',
    'minhas',
    'muito',
    'na',
    'nao',
    'nas',
    'nem',
    'no',
    'nos',
    'nossa',
    'nossas',
    'nosso',
    'nossos',
    'num',
    'numa',
    'o',
    'os',
    'ou',
    'para',
    'pela',
    'pelas',
    'pelo',
    'pelos',
    'por',
    'qual',
    'quando',
    'que',
    'quem',
    'se',
    'sem',
    'ser',
    'sera',
    'seu',
    'seus',
    'sua',
    'suas',
    'tambem',
    'te',
    'tem',
    'tendo',
    'tenho',
    'ter',
    'tinha',
    'tinham',
    'um',
    'uma',
    'voce',
    'voces',
}


@dataclass(slots=True)
class TextoProcessado:
    original: str
    normalizado: str
    tokens: list[str]
    tokens_comparacao: list[str]
    texto_processado: str


def remover_acentos(texto: str) -> str:
    '''Remove acentos e caracteres diacriticos de um texto.

    Essa etapa reduz variacoes ortograficas que atrapalham comparacoes
    lexicais, principalmente quando respostas equivalentes usam grafias com e
    sem acentuacao.

    Args:
        texto: Texto bruto a ser normalizado.

    Returns:
        Texto convertido para uma representacao ASCII aproximada.
    '''
    return unidecode(texto)


def normalizar_texto(texto: str) -> str:
    '''Padroniza o texto para as etapas seguintes do pipeline.

    O processamento converte para minusculas, remove acentos, substitui
    pontuacao por espacos e colapsa espacamentos repetidos. O tratamento de
    ``None`` como string vazia evita falhas desnecessarias em cenarios reais.

    Args:
        texto: Texto de entrada, que pode inclusive ser ``None``.

    Returns:
        Texto limpo e padronizado para tokenizacao.
    '''
    texto = '' if texto is None else texto
    texto = remover_acentos(texto.lower()).strip()
    texto = re.sub(r'[^\w\s]', ' ', texto, flags=re.UNICODE)
    texto = re.sub(r'\s+', ' ', texto).strip()
    return texto


def tokenizar(texto: str) -> list[str]:
    '''Extrai tokens alfanumericos simples do texto normalizado.

    A expressao regular prioriza simplicidade e previsibilidade, o que e
    suficiente para o escopo do projeto e reduz a dependencia de tokenizadores
    mais pesados.

    Args:
        texto: Texto previamente normalizado.

    Returns:
        Lista de tokens em ordem de aparicao. Retorna lista vazia quando o
        texto nao possui conteudo util.
    '''
    return re.findall(r'[a-z0-9]+', texto) if texto else []


def radicalizar_token(token: str) -> str:
    '''Aplica stemming em um token usando o algoritmo em portugues.

    O radical resultante e usado para comparacao aproximada entre palavras de
    mesma familia, como singular e plural ou flexoes verbais.

    Args:
        token: Token individual que sera reduzido ao seu radical.

    Returns:
        Radical calculado pelo ``SnowballStemmer`` para portugues.
    '''
    return STEMMER_PORTUGUES.stem(token)


def preprocessar_texto(
    texto: str,
    remover_stopwords: bool = True,
    aplicar_stemming: bool = True,
    stopwords: set[str] | None = None,
) -> TextoProcessado:
    '''Executa o pipeline completo de pre-processamento textual.

    O fluxo atual combina normalizacao, tokenizacao, remocao opcional de
    stopwords e stemming opcional. O resultado preserva tanto os tokens limpos
    quanto os radicais usados na comparacao, o que facilita auditoria e
    experimentacao com diferentes configuracoes.

    Args:
        texto: Texto original a ser processado.
        remover_stopwords: Indica se palavras funcionais comuns devem ser
            filtradas antes da analise.
        aplicar_stemming: Define se os tokens comparativos devem ser reduzidos
            aos seus radicais.
        stopwords: Conjunto alternativo de stopwords. Quando omitido, utiliza a
            lista padrao do projeto.

    Returns:
        Estrutura ``TextoProcessado`` com texto normalizado, tokens limpos,
        tokens usados na comparacao e a representacao final concatenada.
    '''
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
        original='' if texto is None else texto,
        normalizado=normalizado,
        tokens=tokens,
        tokens_comparacao=tokens_comparacao,
        texto_processado=' '.join(tokens_comparacao),
    )


def extrair_palavras_chave(tokens: list[str], limite: int = 6) -> list[str]:
    '''Seleciona palavras-chave por frequencia e ordem de aparicao.

    Tokens muito curtos sao ignorados para reduzir ruido. Em seguida, os
    termos sao ordenados pela frequencia decrescente e, em caso de empate, pela
    primeira ocorrencia no texto, preservando relevancia local.

    Args:
        tokens: Lista de tokens limpos a partir da qual as palavras-chave serao
            extraidas.
        limite: Quantidade maxima de termos que devem ser retornados.

    Returns:
        Lista ordenada com as palavras-chave consideradas mais representativas.
        Retorna lista vazia quando o limite informado nao for positivo.
    '''
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

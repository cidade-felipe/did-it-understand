'''Motor de avaliacao de respostas com TF-IDF e similaridade do cosseno.'''

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
        '''Retorna a soma dos pesos usados na composicao da nota final.

        A nota consolidada nasce da combinacao de dois sinais principais:
        ``peso_similaridade``, que mede o quanto a resposta do usuario se
        aproxima lexicalmente da resposta esperada, e
        ``peso_palavras_chave``, que mede se os conceitos centrais apareceram.
        Concentrar esse calculo em um unico metodo evita que a validacao da
        configuracao e a formula final usem totais diferentes, o que
        distorceria a escala de 0 a 100.

        Returns:
            Soma simples dos pesos configurados para os dois criterios
            principais de avaliacao.
        '''
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
    '''Valida se a configuracao permite uma avaliacao coerente.

    Esta validacao acontece antes de qualquer processamento de texto para
    impedir que o sistema gere uma nota matematicamente calculavel, mas
    semanticamente enganosa. As variaveis mais importantes aqui sao
    ``peso_similaridade`` e ``peso_palavras_chave``, que precisam somar um
    valor positivo para a formula da nota funcionar, e ``limite_parcial`` com
    ``limite_entendeu``, que definem a fronteira entre os feedbacks
    categorizados.

    Sem essa checagem, seria possivel executar o pipeline inteiro e ainda
    assim produzir um resultado incorreto do ponto de vista de negocio, como
    classificar uma resposta melhor como inferior a outra apenas por causa de
    limites invertidos.

    Args:
        configuracao: Parametros que controlam o calculo da nota e do feedback.

    Raises:
        ValueError: Quando a soma dos pesos e invalida ou os limites de
            classificacao estao incoerentes.
    '''
    if configuracao.soma_pesos() <= 0:
        raise ValueError('A soma dos pesos precisa ser maior que zero.')
    if configuracao.limite_parcial > configuracao.limite_entendeu:
        raise ValueError('O limite de parcial não pode ser maior que o limite de entendeu.')


def calcular_similaridade_tfidf(tokens_esperados: list[str], tokens_usuario: list[str]) -> float:
    '''Calcula a similaridade vetorial entre duas listas de tokens.

    O algoritmo transforma ``tokens_esperados`` e ``tokens_usuario`` em dois
    documentos artificiais, ``documento_esperado`` e ``documento_usuario``,
    apenas para que o ``TfidfVectorizer`` consiga montar uma
    ``matriz_tfidf`` comparavel. Em seguida, a ``matriz_similaridade`` mede o
    cosseno entre esses vetores e retorna um valor entre ``0.0`` e ``1.0``.

    As variaveis centrais desta funcao sao:
        - ``documento_esperado`` e ``documento_usuario``, que condensam os
          tokens em strings adequadas para o vetorizador;
        - ``matriz_tfidf``, que representa a importancia relativa de cada
          termo em cada resposta;
        - ``matriz_similaridade``, que traduz a proximidade vetorial em um
          numero simples para compor a nota final.

    Essa metrica funciona bem como um sinal barato e interpretavel de
    proximidade textual. Ao mesmo tempo, a docstring deixa claro que ela nao
    representa compreensao semantica completa sozinha, por isso o projeto a
    combina com palavras-chave.

    Args:
        tokens_esperados: Tokens derivados da resposta de referencia.
        tokens_usuario: Tokens derivados da resposta enviada pelo usuario.

    Returns:
        Similaridade do cosseno entre os vetores TF-IDF dos dois documentos.
        Retorna 0.0 quando algum dos lados fica vazio apos o pre-processamento.
    '''
    documento_esperado = ' '.join(tokens_esperados)
    documento_usuario = ' '.join(tokens_usuario)
    if not documento_esperado or not documento_usuario:
        return 0.0

    vetorizador = TfidfVectorizer(
        lowercase=False,
        preprocessor=None,
        tokenizer=str.split,
        token_pattern=None,
    )
    matriz_tfidf = vetorizador.fit_transform([documento_esperado, documento_usuario])
    matriz_similaridade = cosine_similarity(matriz_tfidf[:1], matriz_tfidf[1:2])
    return float(matriz_similaridade[0, 0])


def _classificar_feedback(nota: float, configuracao: ConfiguracaoAvaliacao) -> str:
    '''Traduz a nota numerica em uma categoria de feedback.

    A decisao depende diretamente de tres variaveis: ``nota``,
    ``configuracao.limite_entendeu`` e ``configuracao.limite_parcial``. A
    primeira informa o desempenho consolidado da resposta, enquanto as duas
    ultimas determinam o corte minimo para enquadrar o resultado como
    ``Entendeu``, ``Parcial`` ou ``Nao entendeu``.

    Isolar essa regra em uma funcao separada reduz acoplamento com a etapa de
    calculo numerico e facilita ajustes futuros de taxonomia sem mexer na
    formula da nota.

    Args:
        nota: Nota final ja normalizada na escala de 0 a 100.
        configuracao: Configuracao com os limites que separam os niveis
            'Entendeu', 'Parcial' e 'Nao entendeu'.

    Returns:
        Rotulo textual apropriado para a faixa em que a nota se encontra.
    '''
    if nota >= configuracao.limite_entendeu:
        return 'Entendeu'
    return 'Parcial' if nota >= configuracao.limite_parcial else 'Nao entendeu'


def _gerar_observacoes(
    resposta_esperada: TextoProcessado,
    resposta_usuario: TextoProcessado,
    similaridade: float,
    cobertura_palavras_chave: float,
    palavras_chave_encontradas: list[str],
) -> list[str]:
    '''Gera observacoes textuais para ajudar a interpretar a nota.

    A funcao transforma sinais tecnicos em frases legiveis para quem esta
    consumindo o resultado. As variaveis principais sao ``similaridade``,
    ``cobertura_palavras_chave`` e ``palavras_chave_encontradas``, que
    resumem respectivamente proximidade textual, presenca dos conceitos
    centrais e quais termos relevantes realmente apareceram. A variavel local
    ``proporcao_tamanho`` complementa a leitura ao indicar se a resposta do
    usuario ficou muito curta em relacao ao esperado.

    Na pratica, essa camada melhora interpretabilidade. Em vez de expor apenas
    uma nota, o sistema entrega pistas concretas sobre o motivo do resultado,
    o que reduz atrito em depuracao, apresentacoes academicas e calibracao de
    parametros.

    Args:
        resposta_esperada: Estrutura processada da resposta de referencia.
        resposta_usuario: Estrutura processada da resposta enviada pelo usuario.
        similaridade: Similaridade TF-IDF calculada entre as respostas.
        cobertura_palavras_chave: Fracao das palavras-chave esperadas que foram
            detectadas na resposta do usuario.
        palavras_chave_encontradas: Lista efetivamente reconhecida no texto do
            usuario, ja considerando o uso de radicais.

    Returns:
        Lista ordenada de observacoes em linguagem natural para complementar a
        interpretacao da nota final.
    '''
    observacoes: list[str] = []

    if not resposta_usuario.tokens:
        observacoes.append(
            'A resposta do usuário ficou vazia depois do pré-processamento, por isso a nota foi zerada.'
        )
        return observacoes

    if similaridade >= 0.75:
        observacoes.append('A estrutura textual ficou bem próxima da resposta esperada.')
    elif similaridade >= 0.4:
        observacoes.append('Há proximidade textual moderada entre as respostas.')
    else:
        observacoes.append('A proximidade textual ficou baixa, indicando pouca sobreposição de termos.')

    if cobertura_palavras_chave == 0:
        observacoes.append('Nenhuma palavra-chave principal da resposta esperada apareceu na resposta do usuário.')
    elif cobertura_palavras_chave < 0.5:
        observacoes.append('A resposta cobriu apenas parte das palavras-chave mais importantes.')
    else:
        observacoes.append('A resposta recuperou boa parte das palavras-chave centrais.')

    proporcao_tamanho = len(resposta_usuario.tokens) / max(len(resposta_esperada.tokens), 1)
    if proporcao_tamanho < 0.5:
        observacoes.append(
            'A resposta do usuário é bem mais curta que a esperada, o que pode indicar explicação incompleta.'
        )

    if palavras_chave_encontradas:
        observacoes.append(
            'Palavras-chave encontradas: ' + ', '.join(palavras_chave_encontradas) + '.'
        )

    return observacoes


def avaliar_resposta(
    pergunta: str,
    resposta_esperada: str,
    resposta_usuario: str,
    configuracao: ConfiguracaoAvaliacao | None = None,
) -> ResultadoAvaliacao:
    '''Avalia o quanto a resposta do usuario se aproxima da resposta esperada.

    Esta e a funcao central do avaliador local. O fluxo passa por quatro
    etapas: validacao da configuracao, pre-processamento das duas respostas,
    calculo das metricas intermediarias e consolidacao do resultado final.

    Variaveis e artefatos mais importantes do fluxo:
        - ``resposta_esperada_proc`` e ``resposta_usuario_proc`` armazenam as
          versoes processadas dos textos, incluindo tokens limpos e tokens de
          comparacao;
        - ``palavras_chave`` representa os conceitos mais relevantes extraidos
          da resposta esperada;
        - ``palavras_encontradas`` identifica o subconjunto dessas palavras
          que apareceu no texto do usuario, inclusive por radical;
        - ``cobertura_palavras_chave`` mede a fracao de conceitos centrais
          cobertos;
        - ``similaridade`` captura a proximidade lexical entre as respostas;
        - ``nota_base`` combina os sinais ponderados antes da conversao para a
          escala percentual final;
        - ``feedback`` traduz a nota numerica em uma classificacao simples e
          comunicavel.

    A escolha por combinar similaridade TF-IDF e cobertura de palavras-chave
    busca um equilibrio entre simplicidade, transparencia e custo
    computacional. O metodo nao tenta resolver semantica profunda, mas entrega
    um comportamento facil de explicar e suficientemente util para cenarios
    educacionais, demonstracoes e prototipos de avaliacao automatizada.

    Args:
        pergunta: Enunciado associado a resposta, preservado no resultado para
            contextualizacao.
        resposta_esperada: Texto usado como referencia para a avaliacao.
        resposta_usuario: Texto produzido pelo usuario e submetido a analise.
        configuracao: Parametros opcionais para ajustar pesos, limites e regras
            de pre-processamento. Quando ausente, usa a configuracao padrao.

    Returns:
        Estrutura completa com nota, feedback, metricas intermediarias e
        artefatos de pre-processamento, permitindo auditoria do resultado.

    Raises:
        ValueError: Quando a resposta esperada e vazia ou a configuracao e
            inconsistente.
    '''
    configuracao = configuracao or ConfiguracaoAvaliacao()
    _validar_configuracao(configuracao)

    if not resposta_esperada.strip():
        raise ValueError('A resposta esperada não pode ser vazia.')

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

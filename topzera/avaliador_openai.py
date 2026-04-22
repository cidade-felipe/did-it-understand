'''Avaliador semantico de respostas usando Azure OpenAI.'''

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field # Serve para criar classes simples de dados com menos  boilerplate, ou seja, sem precisar escrever métodos como __init__ ou __repr__ manualmente.
from json import JSONDecodeError
from typing import Any # Fornece tipos genéricos para anotações, como Any, List, Dict, etc. Aqui é usado para indicar que um valor pode ser de qualquer tipo, especialmente útil ao lidar com dados JSON que podem ter estrutura variada.
from urllib.parse import urlsplit, urlunsplit # urlsplit é usado para dividir uma URL em seus componentes (esquema, netloc, caminho, query, fragmento), enquanto urlunsplit é usado para recompor uma URL a partir desses componentes. No código, essas funções são usadas para normalizar o endpoint do Azure OpenAI, removendo partes indesejadas da URL.

from dotenv import load_dotenv

@dataclass(slots=True)
class ConfiguracaoAzureOpenAI:
    api_key: str
    endpoint: str
    deployment: str
    api_version: str
    temperatura: float


@dataclass(slots=True)
class ResultadoAvaliacaoIA:
    pergunta: str
    resposta_esperada: str
    resposta_usuario: str
    nota: float
    feedback: str
    similaridade_semantica: float
    justificativa: str
    pontos_corretos: list[str] = field(default_factory=list)
    lacunas: list[str] = field(default_factory=list)
    alertas: list[str] = field(default_factory=list)


def carregar_configuracao() -> ConfiguracaoAzureOpenAI:
    '''Le configuracao do ambiente e monta o objeto de acesso ao Azure OpenAI.

    Esta funcao e a porta de entrada de toda a integracao com Azure OpenAI. O
    fluxo carrega o arquivo ``.env``, tenta resolver credenciais por nomes
    alternativos e consolida tudo em um objeto tipado. As variaveis mais
    importantes sao ``api_key``, ``endpoint``, ``deployment`` e
    ``api_version``, porque definem autenticacao, destino da chamada e modelo
    efetivamente utilizado. A variavel ``temperatura`` entra como parametro
    obrigatorio de comportamento do modelo.

    Ha tambem uma lista auxiliar, ``ausentes``, usada para acumular quais
    configuracoes obrigatorias nao foram encontradas. Isso melhora muito a
    experiencia de operacao, porque a falha deixa claro o que precisa ser
    corrigido antes de consumir a API e gerar custo desnecessario.

    Returns:
        Estrutura tipada com credenciais e parametros operacionais da API.

    Raises:
        RuntimeError: Quando faltam variaveis obrigatorias ou quando a
            temperatura configurada nao pode ser convertida para numero.
    '''
    load_dotenv()

    api_key = obter_env('AZURE_OPENAI_API_KEY', 'OPENAI_API_KEY')
    endpoint = normalizar_endpoint_azure(obter_env('AZURE_OPENAI_ENDPOINT', 'AZURE_ENDPOINT'))
    deployment = obter_env(
        'AZURE_OPENAI_DEPLOYMENT',
        'AZURE_OPENAI_MODEL',
        'AZURE_DEPLOYMENT',
        'OPENAI_MODEL',
        'API_VERSION'
    )
    api_version = obter_env_opcional('AZURE_OPENAI_API_VERSION', 'OPENAI_API_VERSION','API_VERSION')
    temperatura_bruta = obter_env_opcional('AZURE_OPENAI_TEMPERATURE')

    ausentes = []
    if not api_key:
        ausentes.append('AZURE_OPENAI_API_KEY ou OPENAI_API_KEY')
    if not endpoint:
        ausentes.append('AZURE_OPENAI_ENDPOINT ou AZURE_ENDPOINT')
    if not deployment:
        ausentes.append('AZURE_OPENAI_DEPLOYMENT')
    if temperatura_bruta is None:
        ausentes.append('AZURE_OPENAI_TEMPERATURE')

    if ausentes:
        raise RuntimeError(
            'Configuração incompleta. Defina no .env: ' + '; '.join(ausentes) + '.'
        )

    temperatura = carregar_temperatura()

    return ConfiguracaoAzureOpenAI(
        api_key=api_key,
        endpoint=endpoint,
        deployment=deployment,
        api_version=api_version,
        temperatura=temperatura,
    )


def obter_env(*nomes: str) -> str:
    '''Retorna o primeiro valor de ambiente valido ou string vazia.

    Esta funcao e um wrapper sobre ``obter_env_opcional`` para os pontos do
    codigo em que trabalhar com string vazia e mais simples do que lidar com
    ``None``. O parametro variadico ``nomes`` representa a prioridade de busca
    entre diferentes convencoes de ambiente.

    Esse desenho reduz condicionais espalhadas pela base e ajuda a manter o
    carregamento de configuracao mais previsivel.

    Args:
        *nomes: Variaveis de ambiente candidatas, em ordem de prioridade.

    Returns:
        Primeiro valor nao vazio encontrado, ou string vazia caso todos os
        nomes consultados estejam ausentes.
    '''
    valor = obter_env_opcional(*nomes)
    return valor or ''


def obter_env_opcional(*nomes: str) -> str | None:
    '''Procura a primeira variavel de ambiente nao vazia entre varios nomes.

    A funcao percorre ``nomes`` em ordem e retorna o primeiro valor que exista
    e contenha texto util depois de ``strip``. O retorno opcional permite ao
    codigo chamador diferenciar com clareza entre "nao configurado" e
    "configurado com conteudo valido".

    Args:
        *nomes: Lista ordenada de chaves que podem conter a configuracao.

    Returns:
        Valor limpo da primeira variavel encontrada, ou ``None`` quando nenhuma
        delas estiver definida com conteudo util.
    '''
    for nome in nomes:
        valor = os.getenv(nome)
        if valor and valor.strip():
            return valor.strip()
    return None


def carregar_temperatura() -> float:
    '''Carrega a temperatura obrigatoria do modelo a partir do ambiente.

    A variavel de interesse aqui e ``AZURE_OPENAI_TEMPERATURE``. Quando ela
    existe, a funcao tenta convertela para ``float`` de forma defensiva. Como
    a temperatura agora faz parte do contrato minimo de configuracao do
    projeto, a ausencia da variavel passa a ser tratada como erro de
    configuracao, nao mais como fallback silencioso.

    Essa abordagem melhora previsibilidade operacional. Em vez de deixar o
    comportamento do deployment decidir a temperatura de forma implícita, o
    sistema exige um valor explícito no ambiente e valida esse valor antes de
    qualquer chamada à API.

    Returns:
        Valor em ponto flutuante validado a partir do ambiente.

    Raises:
        RuntimeError: Quando ``AZURE_OPENAI_TEMPERATURE`` nao foi definida.
        RuntimeError: Quando o valor informado nao pode ser interpretado como
            numero.
    '''
    valor = os.getenv('AZURE_OPENAI_TEMPERATURE')
    if not valor or not valor.strip():
        raise RuntimeError('Configuração incompleta. Defina no .env: AZURE_OPENAI_TEMPERATURE.')

    try:
        return float(valor)
    except ValueError as erro:
        raise RuntimeError('AZURE_OPENAI_TEMPERATURE precisa ser um número, exemplo: 1.') from erro


def normalizar_endpoint_azure(endpoint: str) -> str:
    '''Normaliza o endpoint base do Azure OpenAI.

    Em ambientes reais, e comum encontrar o endpoint configurado com trechos a
    mais, como ``/openai`` ou rotas completas de deployment. Esta funcao limpa
    essas variacoes para produzir um endpoint base compativel com o cliente
    oficial.

    Variaveis importantes no processo:
        - ``partes`` recebe o resultado de ``urlsplit`` para separar esquema,
          host e caminho;
        - ``caminho`` concentra apenas a parte da rota que pode precisar de
          poda;
        - ``indice_openai`` identifica se existe um segmento ``/openai`` a ser
          removido;
        - ``endpoint_limpo`` recompõe a URL final sem query string nem
          fragmentos.

    Isso reduz erro de configuracao e economiza tempo de diagnostico, porque o
    projeto tolera pequenas inconsistencias de preenchimento no ``.env``.

    Args:
        endpoint: Valor bruto informado no ambiente.

    Returns:
        Endpoint base limpo, terminado com ``/``. Retorna string vazia quando a
        entrada nao possui conteudo util.
    '''
    endpoint = endpoint.strip()
    if not endpoint:
        return ''

    partes = urlsplit(endpoint)
    caminho = partes.path.rstrip('/')
    indice_openai = caminho.lower().find('/openai')

    if indice_openai >= 0:
        caminho = caminho[:indice_openai]

    endpoint_limpo = urlunsplit((partes.scheme, partes.netloc, caminho, '', ''))
    return endpoint_limpo.rstrip('/') + '/'


def criar_cliente(configuracao: ConfiguracaoAzureOpenAI):
    '''Instancia o cliente do Azure OpenAI sob demanda.

    O parametro ``configuracao`` concentra os dados necessarios para abrir a
    conexao, especialmente ``endpoint``, ``api_key`` e ``api_version``. O
    import tardio de ``AzureOpenAI`` e intencional: ele evita que a simples
    execucao de comandos como ``--check-config`` falhe quando a dependencia nao
    foi instalada.

    Essa separacao melhora manutencao e operacao. O codigo so exige a
    biblioteca no momento em que realmente vai chamar a API, o que reduz
    acoplamento entre validacao local e consumo efetivo do servico.

    Args:
        configuracao: Credenciais e parametros necessarios para abrir conexao
            com a API do Azure OpenAI.

    Returns:
        Cliente configurado para chamadas de chat completions.

    Raises:
        RuntimeError: Quando a biblioteca ``openai`` nao esta instalada no
            ambiente virtual do projeto.
    '''
    try:
        from openai import AzureOpenAI
    except ModuleNotFoundError as erro:
        raise RuntimeError(
            'Biblioteca openai não instalada. Execute: '
            'venv\\Scripts\\python -m pip install -r requirements.txt'
        ) from erro

    return AzureOpenAI(
        api_version=configuracao.api_version,
        azure_endpoint=configuracao.endpoint,
        api_key=configuracao.api_key,
    )


def avaliar_resposta_com_ia(
    pergunta: str,
    resposta_esperada: str,
    resposta_usuario: str,
    configuracao: ConfiguracaoAzureOpenAI | None = None,
) -> ResultadoAvaliacaoIA:
    '''Avalia semanticamente a resposta do usuario via Azure OpenAI.

    Esta e a funcao central do avaliador baseado em IA. O fluxo valida as
    entradas, resolve ou recebe a ``configuracao``, cria o ``cliente`` e monta
    o dicionario ``parametros`` que sera enviado para
    ``client.chat.completions.create``. Depois, processa a resposta em tres
    etapas: extrai ``conteudo``, converte para ``dados`` JSON e transforma esse
    JSON em ``ResultadoAvaliacaoIA`` por meio de ``montar_resultado``.

    Variaveis principais do fluxo:
        - ``configuracao`` define como e para onde a chamada sera feita;
        - ``parametros`` concentra modelo, mensagens, formato de resposta e
          temperatura obrigatoria;
        - ``resposta`` e o objeto bruto devolvido pela API;
        - ``conteudo`` representa o JSON textual emitido pelo modelo;
        - ``dados`` e a versao parseada e pronta para validacao defensiva.

    O principal ganho dessa separacao e confiabilidade operacional. Em vez de
    espalhar parsing e normalizacao pela base, o pipeline deixa claro onde a
    API e chamada, onde o JSON e validado e onde o resultado final e montado.

    Args:
        pergunta: Enunciado que contextualiza a avaliacao.
        resposta_esperada: Resposta de referencia usada como criterio.
        resposta_usuario: Resposta submetida pelo usuario para comparacao.
        configuracao: Configuracao opcional. Quando omitida, e carregada do
            ambiente atual.

    Returns:
        Resultado estruturado com nota, feedback, similaridade semantica e
        justificativas complementares.

    Raises:
        ValueError: Quando pergunta ou respostas obrigatorias sao vazias.
        RuntimeError: Quando a configuracao ou a dependencia da API sao
            insuficientes para executar a chamada.
    '''
    if not pergunta.strip():
        raise ValueError('A pergunta não pode ser vazia.')
    if not resposta_esperada.strip():
        raise ValueError('A resposta esperada não pode ser vazia.')
    if not resposta_usuario.strip():
        raise ValueError('A resposta do usuário não pode ser vazia.')

    configuracao = configuracao or carregar_configuracao()
    cliente = criar_cliente(configuracao)

    parametros = {
        'model': configuracao.deployment,
        'response_format': {'type': 'json_object'},
        'messages': montar_mensagens(pergunta, resposta_esperada, resposta_usuario),
        'temperature': configuracao.temperatura,
    }

    resposta = cliente.chat.completions.create(**parametros)

    conteudo = resposta.choices[0].message.content or '{}'
    dados = carregar_resultado_json(conteudo)
    return montar_resultado(
        pergunta=pergunta,
        resposta_esperada=resposta_esperada,
        resposta_usuario=resposta_usuario,
        dados=dados,
    )


def montar_mensagens(
    pergunta: str,
    resposta_esperada: str,
    resposta_usuario: str,
) -> list[dict[str, str]]:
    '''Constroi as mensagens enviadas ao modelo de linguagem.

    A funcao separa a requisicao em dois blocos principais:
    ``instrucao_sistema``, que define regras de avaliacao e schema de saida, e
    ``tarefa_usuario``, que injeta os dados concretos do exercicio. As
    variaveis ``pergunta``, ``resposta_esperada`` e ``resposta_usuario`` entram
    apenas na mensagem de usuario, preservando o prompt de sistema como
    contrato fixo do avaliador.

    Essa estrutura melhora consistencia do modelo, facilita depuracao e reduz
    risco de respostas fora de formato, porque o schema JSON esperado fica
    explicitado sempre da mesma forma.

    Args:
        pergunta: Enunciado da atividade.
        resposta_esperada: Gabarito ou resposta de referencia.
        resposta_usuario: Resposta fornecida pelo aluno ou usuario final.

    Returns:
        Lista de mensagens no formato aceito pela API de chat completions.
    '''
    instrucao_sistema = '''
Você é um avaliador de respostas educacionais.
Compare a resposta do aluno com a resposta esperada.

Regras:
- avalie o significado, não apenas palavras idênticas;
- não exija informações que não estejam na resposta esperada;
- aceite paráfrases corretas;
- penalize contradições, fuga do tema e explicações vagas;
- retorne somente JSON válido.

Schema do JSON:
{
  'nota': 0,
  'feedback': 'Parcial',
  'similaridade_semantica': 0.0,
  'justificativa': 'texto curto',
  'pontos_corretos': ['texto curto'],
  'lacunas': ['texto curto'],
  'alertas': ['texto curto']
}
'''.strip()

    tarefa_usuario = f'''
Pergunta:
{pergunta}

Resposta esperada:
{resposta_esperada}

Resposta do usuário:
{resposta_usuario}

Avalie a resposta do usuário.
Use nota de 0 a 100.
Use similaridade_semantica de 0.0 a 1.0.
'''.strip()

    return [
        {'role': 'system', 'content': instrucao_sistema},
        {'role': 'user', 'content': tarefa_usuario},
    ]


def montar_resultado(
    pergunta: str,
    resposta_esperada: str,
    resposta_usuario: str,
    dados: dict[str, Any],
) -> ResultadoAvaliacaoIA:
    '''Converte o JSON do modelo em uma estrutura tipada e segura.

    O objetivo aqui e transformar um dicionario generico em um objeto
    previsivel para o restante do sistema. As variaveis ``nota`` e
    ``similaridade`` passam por ``limitar_float`` para evitar valores fora de
    faixa, enquanto ``feedback`` passa por ``normalizar_feedback`` para caber
    na taxonomia oficial do projeto.

    Os campos de lista, como ``pontos_corretos``, ``lacunas`` e ``alertas``,
    sao saneados por ``normalizar_lista``. Isso reduz a chance de a camada de
    apresentacao quebrar por causa de retornos parcialmente fora do schema.

    Args:
        pergunta: Enunciado associado a avaliacao.
        resposta_esperada: Resposta de referencia preservada no resultado.
        resposta_usuario: Resposta do usuario preservada no resultado.
        dados: Objeto JSON retornado pelo modelo apos parsing.

    Returns:
        Resultado final pronto para consumo pela CLI ou por futuras integracoes.
    '''
    nota = limitar_float(dados.get('nota', 0), minimo=0.0, maximo=100.0)
    similaridade = limitar_float(dados.get('similaridade_semantica', nota / 100), minimo=0.0, maximo=1.0)
    feedback = normalizar_feedback(str(dados.get('feedback', '')), nota)

    return ResultadoAvaliacaoIA(
        pergunta=pergunta,
        resposta_esperada=resposta_esperada,
        resposta_usuario=resposta_usuario,
        nota=nota,
        feedback=feedback,
        similaridade_semantica=similaridade,
        justificativa=str(dados.get('justificativa', '')).strip(),
        pontos_corretos=normalizar_lista(dados.get('pontos_corretos')),
        lacunas=normalizar_lista(dados.get('lacunas')),
        alertas=normalizar_lista(dados.get('alertas')),
    )


def carregar_resultado_json(conteudo: str) -> dict[str, Any]:
    '''Converte o conteudo textual do modelo em um dicionario JSON valido.

    A variavel ``conteudo`` representa a resposta textual bruta do modelo. A
    funcao tenta desserializar esse texto com ``json.loads`` e depois garante
    que o retorno seja um objeto JSON, nao uma lista, string ou numero solto.

    Essa verificacao e importante porque a API pode responder com texto
    malformatado ou com um tipo inesperado mesmo quando o prompt pede um
    objeto. Falhar cedo aqui reduz risco de erro mais obscuro nas camadas
    seguintes.

    Args:
        conteudo: Texto bruto retornado pelo modelo.

    Returns:
        Dicionario com os campos de avaliacao fornecidos pela IA.

    Raises:
        ValueError: Quando o modelo nao retorna JSON valido ou devolve um tipo
            diferente de objeto.
    '''
    try:
        dados = json.loads(conteudo)
    except JSONDecodeError as erro:
        raise ValueError('O modelo não retornou um JSON válido.') from erro

    if not isinstance(dados, dict):
        raise ValueError('O JSON retornado pelo modelo precisa ser um objeto.')
    return dados


def limitar_float(valor: Any, minimo: float, maximo: float) -> float:
    '''Converte um valor para ``float`` e restringe ao intervalo permitido.

    Esta funcao protege o sistema contra valores numericos inconsistentes. O
    parametro ``valor`` pode vir em qualquer formato retornado pela API, e os
    limites ``minimo`` e ``maximo`` definem a faixa segura para o campo em
    questao, como ``0`` a ``100`` para nota ou ``0.0`` a ``1.0`` para
    similaridade.

    Se a conversao falha, o codigo escolhe o limite inferior como fallback
    conservador. Isso prioriza robustez e evita propagar excecoes de parsing
    para camadas que esperam apenas um numero valido.

    Args:
        valor: Valor bruto retornado pela API ou por outra etapa do pipeline.
        minimo: Limite inferior aceito.
        maximo: Limite superior aceito.

    Returns:
        Numero convertido e ajustado para permanecer entre ``minimo`` e
        ``maximo``. Quando a conversao falha, usa o limite inferior.
    '''
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        numero = minimo
    return max(minimo, min(maximo, numero))


def normalizar_feedback(feedback_modelo: str, nota: float) -> str:
    '''Padroniza o feedback textual em uma taxonomia fixa do projeto.

    O campo ``feedback_modelo`` pode chegar com variacoes de rotulo, sinonimos
    ou ate pequenas inconsistencias de escrita. Esta funcao tenta primeiro
    enquadrar essas variacoes em uma taxonomia controlada. Se isso nao for
    possivel, usa ``nota`` como fallback para inferir a classe final.

    Essa padronizacao tem impacto direto na confiabilidade da interface e em
    futuras analises agregadas, porque evita que pequenas diferencas textuais
    do modelo criem categorias duplicadas ou ambiguidade de leitura.

    Args:
        feedback_modelo: Rotulo textual original vindo do modelo.
        nota: Nota numerica usada como fallback para classificacao.

    Returns:
        Um dos tres rotulos oficiais: ``Entendeu``, ``Parcial`` ou
        ``Nao entendeu``.
    '''
    feedback_limpo = feedback_modelo.strip().lower()
    if feedback_limpo in {'entendeu', 'entende', 'correto'}:
        return 'Entendeu'
    if feedback_limpo in {'parcial', 'entendeu parcialmente', 'meio certo'}:
        return 'Parcial'
    if feedback_limpo in {'nao entendeu', 'não entendeu', 'errado', 'incorreto'}:
        return 'Nao entendeu'

    if nota >= 70:
        return 'Entendeu'
    return 'Parcial' if nota >= 30 else 'Nao entendeu'


def normalizar_lista(valor: Any) -> list[str]:
    '''Converte um campo potencialmente heterogeneo em lista limpa de strings.

    O parametro ``valor`` pode conter exatamente o que o modelo decidiu
    devolver, inclusive tipos inesperados. A funcao garante que apenas listas
    validas sejam aceitas e que cada item seja convertido para string, tenha
    ``strip`` aplicado e seja descartado se ficar vazio.

    Esse saneamento e importante para campos como ``pontos_corretos``,
    ``lacunas`` e ``alertas``, porque a camada de exibicao presume listas
    simples e prontas para impressao.

    Args:
        valor: Valor bruto retornado pela API para campos como pontos corretos,
            lacunas ou alertas.

    Returns:
        Lista contendo apenas itens nao vazios, convertidos para string.
        Retorna lista vazia quando a entrada nao e uma lista valida.
    '''
    if not isinstance(valor, list):
        return []
    return [str(item).strip() for item in valor if str(item).strip()]

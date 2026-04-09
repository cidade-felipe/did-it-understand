"""Avaliador semantico de respostas usando Azure OpenAI."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from json import JSONDecodeError
from typing import Any
from urllib.parse import urlsplit, urlunsplit

from dotenv import load_dotenv

API_VERSION_PADRAO = "2024-12-01-preview"


@dataclass(slots=True)
class ConfiguracaoAzureOpenAI:
    api_key: str
    endpoint: str
    deployment: str
    api_version: str = API_VERSION_PADRAO
    temperatura: float | None = None


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
    load_dotenv()

    api_key = obter_env("AZURE_OPENAI_API_KEY", "OPENAI_API_KEY")
    endpoint = normalizar_endpoint_azure(obter_env("AZURE_OPENAI_ENDPOINT", "AZURE_ENDPOINT"))
    deployment = obter_env(
        "AZURE_OPENAI_DEPLOYMENT",
        "AZURE_OPENAI_MODEL",
        "AZURE_DEPLOYMENT",
        "OPENAI_MODEL",
    )
    api_version = obter_env_opcional("AZURE_OPENAI_API_VERSION", "OPENAI_API_VERSION") or API_VERSION_PADRAO
    temperatura = carregar_temperatura()

    ausentes = []
    if not api_key:
        ausentes.append("AZURE_OPENAI_API_KEY ou OPENAI_API_KEY")
    if not endpoint:
        ausentes.append("AZURE_OPENAI_ENDPOINT ou AZURE_ENDPOINT")
    if not deployment:
        ausentes.append("AZURE_OPENAI_DEPLOYMENT")

    if ausentes:
        raise RuntimeError(
            "Configuracao incompleta. Defina no .env: " + "; ".join(ausentes) + "."
        )

    return ConfiguracaoAzureOpenAI(
        api_key=api_key,
        endpoint=endpoint,
        deployment=deployment,
        api_version=api_version,
        temperatura=temperatura,
    )


def obter_env(*nomes: str) -> str:
    valor = obter_env_opcional(*nomes)
    return valor or ""


def obter_env_opcional(*nomes: str) -> str | None:
    for nome in nomes:
        valor = os.getenv(nome)
        if valor and valor.strip():
            return valor.strip()
    return None


def carregar_temperatura() -> float | None:
    valor = os.getenv("AZURE_OPENAI_TEMPERATURE")
    if not valor or not valor.strip():
        return None

    try:
        return float(valor)
    except ValueError as erro:
        raise RuntimeError("AZURE_OPENAI_TEMPERATURE precisa ser um numero, exemplo: 1.") from erro


def normalizar_endpoint_azure(endpoint: str) -> str:
    endpoint = endpoint.strip()
    if not endpoint:
        return ""

    partes = urlsplit(endpoint)
    caminho = partes.path.rstrip("/")
    indice_openai = caminho.lower().find("/openai")

    if indice_openai >= 0:
        caminho = caminho[:indice_openai]

    endpoint_limpo = urlunsplit((partes.scheme, partes.netloc, caminho, "", ""))
    return endpoint_limpo.rstrip("/") + "/"


def criar_cliente(configuracao: ConfiguracaoAzureOpenAI):
    try:
        from openai import AzureOpenAI
    except ModuleNotFoundError as erro:
        raise RuntimeError(
            "Biblioteca openai nao instalada. Execute: "
            "venv\\Scripts\\python -m pip install -r requirements.txt"
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
    if not pergunta.strip():
        raise ValueError("A pergunta nao pode ser vazia.")
    if not resposta_esperada.strip():
        raise ValueError("A resposta esperada nao pode ser vazia.")
    if not resposta_usuario.strip():
        raise ValueError("A resposta do usuario nao pode ser vazia.")

    configuracao = configuracao or carregar_configuracao()
    cliente = criar_cliente(configuracao)

    parametros = {
        "model": configuracao.deployment,
        "response_format": {"type": "json_object"},
        "messages": montar_mensagens(pergunta, resposta_esperada, resposta_usuario),
    }

    if configuracao.temperatura is not None:
        parametros["temperature"] = configuracao.temperatura

    resposta = cliente.chat.completions.create(**parametros)

    conteudo = resposta.choices[0].message.content or "{}"
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
    instrucao_sistema = """
Voce e um avaliador de respostas educacionais.
Compare a resposta do aluno com a resposta esperada.

Regras:
- avalie o significado, nao apenas palavras identicas;
- nao exija informacoes que nao estejam na resposta esperada;
- aceite parafrases corretas;
- penalize contradicoes, fuga do tema e explicacoes vagas;
- retorne somente JSON valido.

Schema do JSON:
{
  "nota": 0,
  "feedback": "Parcial",
  "similaridade_semantica": 0.0,
  "justificativa": "texto curto",
  "pontos_corretos": ["texto curto"],
  "lacunas": ["texto curto"],
  "alertas": ["texto curto"]
}
""".strip()

    tarefa_usuario = f"""
Pergunta:
{pergunta}

Resposta esperada:
{resposta_esperada}

Resposta do usuario:
{resposta_usuario}

Avalie a resposta do usuario.
Use nota de 0 a 100.
Use similaridade_semantica de 0.0 a 1.0.
""".strip()

    return [
        {"role": "system", "content": instrucao_sistema},
        {"role": "user", "content": tarefa_usuario},
    ]


def montar_resultado(
    pergunta: str,
    resposta_esperada: str,
    resposta_usuario: str,
    dados: dict[str, Any],
) -> ResultadoAvaliacaoIA:
    nota = limitar_float(dados.get("nota", 0), minimo=0.0, maximo=100.0)
    similaridade = limitar_float(dados.get("similaridade_semantica", nota / 100), minimo=0.0, maximo=1.0)
    feedback = normalizar_feedback(str(dados.get("feedback", "")), nota)

    return ResultadoAvaliacaoIA(
        pergunta=pergunta,
        resposta_esperada=resposta_esperada,
        resposta_usuario=resposta_usuario,
        nota=nota,
        feedback=feedback,
        similaridade_semantica=similaridade,
        justificativa=str(dados.get("justificativa", "")).strip(),
        pontos_corretos=normalizar_lista(dados.get("pontos_corretos")),
        lacunas=normalizar_lista(dados.get("lacunas")),
        alertas=normalizar_lista(dados.get("alertas")),
    )


def carregar_resultado_json(conteudo: str) -> dict[str, Any]:
    try:
        dados = json.loads(conteudo)
    except JSONDecodeError as erro:
        raise ValueError("O modelo nao retornou um JSON valido.") from erro

    if not isinstance(dados, dict):
        raise ValueError("O JSON retornado pelo modelo precisa ser um objeto.")
    return dados


def limitar_float(valor: Any, minimo: float, maximo: float) -> float:
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        numero = minimo
    return max(minimo, min(maximo, numero))


def normalizar_feedback(feedback_modelo: str, nota: float) -> str:
    feedback_limpo = feedback_modelo.strip().lower()
    if feedback_limpo in {"entendeu", "entende", "correto"}:
        return "Entendeu"
    if feedback_limpo in {"parcial", "entendeu parcialmente", "meio certo"}:
        return "Parcial"
    if feedback_limpo in {"nao entendeu", "não entendeu", "errado", "incorreto"}:
        return "Nao entendeu"

    if nota >= 70:
        return "Entendeu"
    return "Parcial" if nota >= 30 else "Nao entendeu"


def normalizar_lista(valor: Any) -> list[str]:
    if not isinstance(valor, list):
        return []
    return [str(item).strip() for item in valor if str(item).strip()]

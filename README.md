# Did It Understand?

Sistema em Python para avaliar se uma resposta do usuário está próxima de uma resposta esperada.

O projeto tem duas versões:

- `mais_ou_menos`: versão clássica do trabalho, com pré-processamento, TF-IDF, similaridade do cosseno e cobertura de palavras-chave.
- `topzera`: versão com Azure OpenAI, que usa um modelo de linguagem como avaliador semântico.

## Objetivo

O trabalho responde à pergunta "a máquina entendeu?" de forma crítica.

Fato: a versão TF-IDF mede proximidade textual.

Fato: a versão com Azure OpenAI pede para um modelo comparar o significado das respostas.

Inferência: a versão com IA tende a lidar melhor com paráfrases, sinônimos e respostas escritas com vocabulário diferente.

Opinião técnica: vale apresentar as duas. A versão `mais_ou_menos` mostra os conceitos de PLN da disciplina de forma transparente. A versão `topzera` mostra uma evolução mais semântica, mas exige API, internet, credenciais e uma discussão honesta sobre custo, dependência externa e possibilidade de julgamento inconsistente.

## Entrada e saída

O sistema recebe:

- uma pergunta
- uma resposta esperada
- uma resposta do usuário

E retorna:

- nota de 0 a 100
- feedback, `Entendeu`, `Parcial` ou `Não entendeu`
- indicadores da avaliação
- explicação do resultado

## Estrutura

```text
did-it-understand/
├── mais_ou_menos/
│   ├── avaliador.py                # Motor de avaliação clássica
│   ├── exemplos.json               # Casos prontos para demonstração
│   ├── main.py                     # CLI da versão clássica
│   ├── preprocessamento.py         # Normalização, tokenização e stemming
│   ├── test_avaliador.py           # Testes unitários da versão clássica
│   └── testes_exemplos.py          # Execução de cenários demonstrativos
├── topzera/
│   ├── avaliador_openai.py         # Avaliador semântico com Azure OpenAI
│   └── main.py                     # CLI da versão com IA
├── .env                            # Credenciais locais e configuração
├── .env.exemple                    # Exemplo de variáveis de ambiente
├── .gitignore
├── documentacao_funcoes_pln.md     # Guia detalhado das funções
├── documentation.md                # Esta documentação técnica
├── LICENSE                         # Licença
├── README.md                       # Guia de uso do projeto
└── requirements.txt                # Dependências Python
```

## Preparar ambiente

Se você ainda não trouxe o projeto para a sua máquina, clone o repositório:

```powershell
git clone https://github.com/cidade-felipe/did-it-understand.git
cd did-it-understand
```

Use o ambiente virtual `venv` do projeto.

Para instalar as dependências do projeto:

```powershell
venv\Scripts\python -m pip install -r requirements.txt
```

## Executar a versão TF-IDF

Modo interativo:

```powershell
venv\Scripts\python mais_ou_menos\main.py
```

Modo por argumentos:

```powershell
venv\Scripts\python mais_ou_menos\main.py --pergunta "O que é PLN?" --esperada "PLN é a área da computação que processa linguagem humana." --usuario "PLN é o campo da computação que analisa linguagem humana." --detalhes
```

Comparar com e sem stemming:

```powershell
venv\Scripts\python mais_ou_menos\main.py --sem-stemming --pergunta "O que é PLN?" --esperada "PLN é a área da computação que processa linguagem humana." --usuario "PLN é o campo da computação que analisa linguagem humana." --detalhes
```

Rodar exemplos:

```powershell
venv\Scripts\python mais_ou_menos\testes_exemplos.py
```

## Como funciona a versão TF-IDF

Fluxo:

```text
pergunta
resposta esperada  -> pré-processamento -> TF-IDF -> similaridade do cosseno -> nota -> feedback
resposta usuário   -> pré-processamento -> TF-IDF -> palavras-chave ------------^
```

O pré-processamento faz:

- conversão para minúsculas
- remoção de acentos
- remoção de pontuação
- tokenização
- remoção opcional de stopwords
- stemming em português com `nltk`

A nota combina:

- `80%` da similaridade TF-IDF
- `20%` da cobertura de palavras-chave da resposta esperada

Classificação padrão:

- `70` ou mais: `Entendeu`
- de `30` até `69,99`: `Parcial`
- abaixo de `30`: `Não entendeu`

## Configurar Azure OpenAI

No arquivo `.env` da raiz, configure suas credenciais:

```env
OPENAI_API_KEY=sua_chave_do_azure
AZURE_ENDPOINT=https://seu-recurso.cognitiveservices.azure.com/
AZURE_OPENAI_DEPLOYMENT=nome_do_seu_deployment
AZURE_OPENAI_API_VERSION=2024-12-01-preview
```

Importante: no Azure OpenAI, o `model` enviado pelo código deve ser o nome do deployment criado no Azure, não necessariamente o nome público do modelo.

Prefira usar o endpoint base, terminando em `.cognitiveservices.azure.com/`. Se você colar uma URL com `/openai/...` e `api-version`, o código tenta limpar essa URL antes de criar o cliente.

Por padrão, o código não envia `temperature`. Alguns deployments aceitam somente a temperatura padrão e dão erro quando recebem `temperature=0.0`. Se o seu deployment aceitar temperatura customizada, configure `AZURE_OPENAI_TEMPERATURE=1` ou outro valor suportado.

## Executar a versão Azure OpenAI

Validar configuração sem gastar token:

```powershell
venv\Scripts\python topzera\main.py --check-config
```

Modo interativo:

```powershell
venv\Scripts\python topzera\main.py
```

Modo por argumentos:

```powershell
venv\Scripts\python topzera\main.py --pergunta "O que é PLN?" --esperada "PLN é a área da computação que processa linguagem humana." --usuario "É uma área que analisa textos escritos por pessoas."
```

## Como interpretar a versão com IA

A saída mostra:

- `Feedback`: Entendeu, Parcial ou Não entendeu
- `Nota`: escala de 0 a 100
- `Similaridade semântica`: proximidade estimada pelo modelo
- `Justificativa`: explicação curta do julgamento
- `Pontos corretos`: ideias da resposta do usuário que combinam com a esperada
- `Lacunas`: o que faltou
- `Alertas`: contradições, fuga do tema ou vagueza

## Validação

Rode os testes automatizados:

```powershell
venv\Scripts\python -m unittest discover -s mais_ou_menos -p "test*.py"
```

Valide a configuração da IA:

```powershell
venv\Scripts\python topzera\main.py --check-config
```

Para defender melhor o trabalho, teste estes cenários nas duas versões:

- resposta correta com palavras parecidas
- resposta correta com outras palavras
- resposta incompleta
- resposta errada com palavras parecidas
- resposta vazia na versão TF-IDF
- resposta vaga na versão com IA

## Limites

Fato: TF-IDF compara palavras e distribuições de termos.

Fato: o modelo via Azure OpenAI avalia linguagem natural de forma mais flexível, mas continua sendo uma estimativa produzida por um sistema estatístico.

Inferência: respostas corretas com vocabulário muito diferente podem receber nota injusta no TF-IDF.

Inferência: a versão com IA pode variar a justificativa, depender da disponibilidade da API e gerar custo por uso.

Opinião técnica: a melhor apresentação é comparar os resultados das duas versões e explicar o trade-off. A primeira é mais simples, barata, reproduzível e alinhada aos conceitos básicos de PLN. A segunda captura melhor significado, mas aumenta complexidade operacional.

## Roteiro de apresentação

1. Apresente o problema: comparar resposta esperada e resposta do usuário.
2. Mostre a versão `mais_ou_menos` e explique pré-processamento, TF-IDF e cosseno.
3. Rode exemplos bons, parciais e ruins.
4. Mostre a versão `topzera` avaliando um exemplo com paráfrase.
5. Compare as notas das duas abordagens.
6. Discuta que similaridade textual não é o mesmo que entendimento.
7. Conclua quando a abordagem simples é suficiente e quando a IA ajuda.

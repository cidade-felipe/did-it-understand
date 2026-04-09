# Did It Understand?

Sistema em Python para avaliar se a resposta de um usuário está próxima da resposta esperada, usando `scikit-learn`, `nltk`, `Unidecode`, pré-processamento de texto, TF-IDF e similaridade do cosseno.

## Objetivo

O trabalho responde à pergunta "a máquina entendeu?" de forma honesta: o sistema mede proximidade textual, não compreensão semântica real.

Ele recebe:

- uma pergunta
- uma resposta esperada
- uma resposta do usuário

E retorna:

- similaridade entre os textos
- nota de 0 a 100
- feedback final, `Entendeu`, `Parcial` ou `Não entendeu`

## Estrutura do projeto

```text
├── tests/
│   └── test_avaliador.py      # Testes automatizados do pré-processamento e avaliador
├── avaliador.py               # Calcula TF-IDF, similaridade, nota e feedback
├── exemplos.json              # Casos prontos para demonstração e análise crítica
├── main.py                    # Interface de terminal para usar o avaliador
├── preprocessamento.py        # Normalização, tokenização, stopwords e stemming
├── requirements.txt           # Bibliotecas Python usadas no projeto
├── testes_exemplos.py         # Executa a bateria de exemplos do trabalho
└── README.md                  # Documentação, execução e limites da abordagem
```

## Como a solução funciona

### 1. Pré-processamento

Em `preprocessamento.py`, o texto passa por:

- conversão para minúsculas
- remoção de acentos
- remoção de pontuação
- tokenização
- remoção opcional de stopwords
- stemming em português com `nltk`

Isso reduz ruído e deixa a comparação mais consistente.

### 2. TF-IDF

Em `avaliador.py`, cada resposta vira um vetor TF-IDF com `TfidfVectorizer`, do `scikit-learn`.

Fato:

- `TF` mede a frequência de cada termo dentro da resposta
- `IDF` reduz o peso de termos muito comuns no conjunto comparado

Bibliotecas usadas:

- `scikit-learn` calcula o TF-IDF e ajuda na similaridade do cosseno
- `nltk` aplica stemming, aproximando variações como `processar`, `processa` e `processando`
- `Unidecode` remove marcas de acento e deixa os termos mais fáceis de comparar
- `rich` melhora a exibição dos resultados no terminal

### 3. Similaridade do cosseno

Depois dos vetores, o sistema calcula a similaridade do cosseno.

Interpretação:

- perto de `1`, respostas muito parecidas
- perto de `0`, respostas muito diferentes

### 4. Nota final

A nota combina:

- `80%` da similaridade TF-IDF
- `20%` da cobertura de palavras-chave da resposta esperada

Classificação padrão:

- `70` ou mais, `Entendeu`
- entre `30` e `69,99`, `Parcial`
- abaixo de `30`, `Não entendeu`

Opinião técnica:

- essa combinação, com limites calibrados para respostas curtas, é superior a usar apenas similaridade bruta com faixas rígidas, porque reduz um pouco os falsos positivos e aproxima melhor a nota do julgamento humano em textos pequenos

Trade-off:

- a heurística melhora a nota final na prática, mas não resolve sinônimos nem entendimento semântico profundo

## Como executar

### Instalar dependências

```bash
python -m pip install -r requirements.txt
```

### Modo interativo

```bash
python main.py
```

### Modo por argumentos

```bash
python main.py --pergunta "O que é PLN?" --esperada "PLN é a área da computação que processa linguagem humana." --usuario "PLN é o campo da computação que analisa linguagem humana." --detalhes
```

### Comparar com e sem stemming

```bash
python main.py --sem-stemming --pergunta "O que é PLN?" --esperada "PLN é a área da computação que processa linguagem humana." --usuario "PLN é o campo da computação que analisa linguagem humana." --detalhes
```

### Rodar os exemplos do trabalho

```bash
python testes_exemplos.py
```

### Rodar os testes automatizados

```bash
python -m unittest discover -s tests
```

## O que mostrar na apresentação

Um roteiro seguro:

1. apresentar o problema
2. explicar o pré-processamento
3. mostrar a fórmula de TF-IDF e a similaridade do cosseno
4. executar exemplos bons e ruins
5. discutir por que o sistema acerta ou erra
6. concluir que similaridade textual não é o mesmo que entendimento real

## Limites da abordagem

Fato:

- o sistema compara palavras e distribuições de termos

Fato:

- ele não representa semântica profunda, contexto, ironia, intenção nem conhecimento de mundo

Inferência:

- respostas corretas com vocabulário muito diferente podem receber nota injusta

Inferência:

- respostas superficiais que repetem termos importantes podem parecer melhores do que realmente são

## Validação sugerida

Para defender melhor o trabalho, vale mostrar:

- resposta correta com palavras parecidas
- resposta correta com outras palavras
- resposta incompleta
- resposta errada com palavras parecidas
- resposta vazia

Isso ajuda a conectar a parte técnica com impacto real da avaliação, reduzindo o risco de apresentar o sistema como algo mais inteligente do que ele realmente é.

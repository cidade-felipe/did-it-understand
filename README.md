# Did It Understand?

Sistema em Python para avaliar se a resposta de um usuario esta proxima da resposta esperada, usando `scikit-learn`, `nltk`, `Unidecode`, pre-processamento de texto, TF-IDF e similaridade do cosseno.

## Objetivo

O trabalho responde a pergunta "a maquina entendeu?" de forma honesta: o sistema mede proximidade textual, nao compreensao semantica real.

Ele recebe:

- uma pergunta
- uma resposta esperada
- uma resposta do usuario

E retorna:

- similaridade entre os textos
- nota de 0 a 100
- feedback final, `Entendeu`, `Parcial` ou `Nao entendeu`

## Estrutura do projeto

```text
did-it-understand/
|- Backup/
|  `- README.original.md
|- avaliador.py
|- exemplos.json
|- main.py
|- preprocessamento.py
|- requirements.txt
|- testes_exemplos.py
`- tests/
   `- test_avaliador.py
```

## Como a solucao funciona

### 1. Pre-processamento

Em `preprocessamento.py`, o texto passa por:

- conversao para minusculas
- remocao de acentos
- remocao de pontuacao
- tokenizacao
- remocao opcional de stopwords
- stemming em portugues com `nltk`

Isso reduz ruido e deixa a comparacao mais consistente.

### 2. TF-IDF

Em `avaliador.py`, cada resposta vira um vetor TF-IDF com `TfidfVectorizer`, do `scikit-learn`.

Fato:

- `TF` mede a frequencia de cada termo dentro da resposta
- `IDF` reduz o peso de termos muito comuns no conjunto comparado

Bibliotecas usadas:

- `scikit-learn` calcula o TF-IDF e ajuda na similaridade do cosseno
- `nltk` aplica stemming, aproximando variacoes como `processar`, `processa` e `processando`
- `Unidecode` remove marcas de acento e deixa os termos mais faceis de comparar
- `rich` melhora a exibicao dos resultados no terminal

### 3. Similaridade do cosseno

Depois dos vetores, o sistema calcula a similaridade do cosseno.

Interpretacao:

- perto de `1`, respostas muito parecidas
- perto de `0`, respostas muito diferentes

### 4. Nota final

A nota combina:

- `80%` da similaridade TF-IDF
- `20%` da cobertura de palavras-chave da resposta esperada

Classificacao padrao:

- `70` ou mais, `Entendeu`
- entre `30` e `69,99`, `Parcial`
- abaixo de `30`, `Nao entendeu`

Opiniao tecnica:

- essa combinacao, com limites calibrados para respostas curtas, e superior a usar apenas similaridade bruta com faixas rigidas, porque reduz um pouco os falsos positivos e aproxima melhor a nota do julgamento humano em textos pequenos

Trade-off:

- a heuristica melhora a nota final na pratica, mas nao resolve sinonimos nem entendimento semantico profundo

## Como executar

### Instalar dependencias

```bash
python -m pip install -r requirements.txt
```

### Modo interativo

```bash
python main.py
```

### Modo por argumentos

```bash
python main.py --pergunta "O que e PLN?" --esperada "PLN e a area da computacao que processa linguagem humana." --usuario "PLN e o campo da computacao que analisa linguagem humana." --detalhes
```

### Comparar com e sem stemming

```bash
python main.py --sem-stemming --pergunta "O que e PLN?" --esperada "PLN e a area da computacao que processa linguagem humana." --usuario "PLN e o campo da computacao que analisa linguagem humana." --detalhes
```

### Rodar os exemplos do trabalho

```bash
python testes_exemplos.py
```

### Rodar os testes automatizados

```bash
python -m unittest discover -s tests
```

## O que mostrar na apresentacao

Um roteiro seguro:

1. apresentar o problema
2. explicar o pre-processamento
3. mostrar a formula de TF-IDF e a similaridade do cosseno
4. executar exemplos bons e ruins
5. discutir por que o sistema acerta ou erra
6. concluir que similaridade textual nao e o mesmo que entendimento real

## Limites da abordagem

Fato:

- o sistema compara palavras e distribuicoes de termos

Fato:

- ele nao representa semantica profunda, contexto, ironia, intencao nem conhecimento de mundo

Inferencia:

- respostas corretas com vocabulario muito diferente podem receber nota injusta

Inferencia:

- respostas superficiais que repetem termos importantes podem parecer melhores do que realmente sao

## Validacao sugerida

Para defender melhor o trabalho, vale mostrar:

- resposta correta com palavras parecidas
- resposta correta com outras palavras
- resposta incompleta
- resposta errada com palavras parecidas
- resposta vazia

Isso ajuda a conectar a parte tecnica com impacto real da avaliacao, reduzindo o risco de apresentar o sistema como algo mais inteligente do que ele realmente e.

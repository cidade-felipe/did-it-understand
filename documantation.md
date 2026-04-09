# Documentação técnica, Did It Understand?

## 1. Descrição do trabalho

O projeto **Did It Understand?** é um avaliador simples de respostas textuais com técnicas de Processamento de Linguagem Natural.

A proposta do trabalho é responder, com senso crítico, à pergunta: **a máquina entendeu?**

Na prática, o sistema recebe:

- uma pergunta
- uma resposta esperada
- uma resposta escrita pelo usuário

Depois disso, ele compara a resposta esperada com a resposta do usuário e retorna:

- similaridade TF-IDF
- cobertura de palavras-chave
- nota final de `0` a `100`
- feedback, `Entendeu`, `Parcial` ou `Nao entendeu`
- observações para ajudar na interpretação

## 2. Ideia principal

Fato:

- o sistema compara textos por padrões de palavras
- o sistema usa TF-IDF, stemming, stopwords, palavras-chave e similaridade do cosseno

Inferência:

- uma resposta com vocabulário parecido tende a receber uma nota maior
- uma resposta correta, mas escrita com termos muito diferentes, pode receber uma nota baixa

Opinião técnica:

- este sistema é adequado para demonstrar PLN básico em sala, mas não deve ser vendido como um corretor automático perfeito

## 3. Estrutura do projeto

```text
├── Backup/
│   └── README.original.md
├── tests/
│   └── test_avaliador.py
├── avaliador.py
├── documation.md
├── exemplos.json
├── main.py
├── preprocessamento.py
├── README.md
├── requirements.txt
└── testes_exemplos.py
```

## 4. Como instalar

Recomendação:

```bash
python -m venv .venv
```

No Windows PowerShell:

```bash
.\.venv\Scripts\python -m pip install -r requirements.txt
```

Forma genérica:

```bash
python -m pip install -r requirements.txt
```

## 5. Bibliotecas utilizadas

### scikit-learn

Usada em `avaliador.py`.

Responsabilidade:

- transformar texto pré-processado em vetor TF-IDF com `TfidfVectorizer`
- apoiar o cálculo da similaridade do cosseno com `cosine_similarity`

Por que usar:

- é uma biblioteca consolidada para machine learning em Python
- evita manter uma implementação manual de TF-IDF
- facilita explicar o método com uma ferramenta real de mercado

### nltk

Usada em `preprocessamento.py`.

Responsabilidade:

- aplicar stemming em português com `SnowballStemmer("portuguese")`

Por que usar:

- aproxima variações da mesma família de palavras
- por exemplo, `processar`, `processa` e `processando` ficam mais parecidas na comparação

Trade-off:

- stemming corta palavras em radicais aproximados
- isso ajuda a comparar flexões, mas não entende sinônimos automaticamente

### Unidecode

Usada em `preprocessamento.py`.

Responsabilidade:

- remover marcas de acento
- exemplo conceitual, uma palavra com acento é convertida para uma forma sem acento

Por que usar:

- respostas digitadas com ou sem acento ficam mais comparáveis

### rich

Usada em `main.py` e `testes_exemplos.py`.

Responsabilidade:

- exibir tabelas, painéis e textos formatados no terminal

Por que usar:

- deixa a apresentação do trabalho mais legível
- melhora a demonstração em sala

## 6. Como usar pelo terminal

### Modo interativo

Execute:

```bash
python main.py
```

O programa vai pedir:

```text
Pergunta:
Resposta esperada:
Resposta do usuario:
```

Exemplo de pergunta:

```text
O que é PLN?
```

Exemplo de resposta esperada:

```text
PLN é a área da computação e da inteligência artificial que desenvolve técnicas para processar, analisar e gerar linguagem humana, como textos e fala.
```

Exemplo de resposta do usuário:

```text
PLN é uma área da computação que usa técnicas para processar e analisar textos escritos por pessoas.
```

### Modo com argumentos

Execute:

```bash
python main.py --pergunta "O que é PLN?" --esperada "PLN é a área da computação que processa linguagem humana." --usuario "PLN é uma área que analisa texto e linguagem humana." --detalhes
```

### Opções do main.py

`--pergunta`

Pergunta apresentada ao aluno ou usuário.

`--esperada`

Resposta de referência, considerada correta ou ideal.

`--usuario`

Resposta que será avaliada.

`--detalhes`

Mostra tokens, radicais e palavras-chave.

`--manter-stopwords`

Desliga a remoção de stopwords.

Use quando quiser demonstrar a diferença entre texto com palavras comuns e texto mais limpo.

`--sem-stemming`

Desliga o stemming do NLTK.

Use para demonstrar o impacto da inteligência linguística simples.

## 7. Como rodar exemplos prontos

Execute:

```bash
python testes_exemplos.py
```

Esse script lê o arquivo `exemplos.json`, avalia cada cenário e exibe:

- expectativa humana
- resposta do sistema
- nota
- similaridade
- palavras-chave encontradas
- observações

## 8. Como rodar testes automatizados

Execute:

```bash
python -m unittest discover -s tests
```

Os testes verificam comportamentos centrais, como:

- remoção de acentos e pontuação
- aproximação de palavras com stemming
- nota máxima para resposta igual à esperada
- nota zero para resposta vazia
- nota baixa para resposta errada

## 9. Fluxo interno da avaliação

O caminho da resposta dentro do sistema é:

```text
texto original
↓
normalização
↓
tokenização
↓
remoção de stopwords
↓
stemming
↓
vetorização TF-IDF
↓
similaridade do cosseno
↓
cálculo de palavras-chave
↓
nota final
↓
feedback
```

## 10. Como a nota é calculada

O sistema usa esta combinação:

```text
nota_base = similaridade * 0.8 + cobertura_de_palavras_chave * 0.2
nota_final = nota_base * 100
```

Na configuração padrão:

- similaridade TF-IDF pesa `80%`
- cobertura de palavras-chave pesa `20%`
- nota `>= 70` vira `Entendeu`
- nota `>= 30` e `< 70` vira `Parcial`
- nota `< 30` vira `Nao entendeu`

## 11. Arquivo preprocessamento.py

Responsabilidade geral:

- preparar texto natural para comparação matemática

### Constante STEMMER_PORTUGUES

Instância do `SnowballStemmer` configurada para português.

Uso:

- gerar radicais de palavras
- aproximar flexões, como `analisar` e `analisa`

### Constante STOPWORDS_PADRAO

Conjunto de palavras comuns em português.

Uso:

- remover termos muito frequentes, como artigos, pronomes e preposições
- reduzir ruído antes do TF-IDF

### Classe TextoProcessado

Data class que guarda as versões de um texto após o pré-processamento.

Campos:

- `original`, texto recebido pela função
- `normalizado`, texto em minúsculas, sem acentos e sem pontuação relevante
- `tokens`, lista de palavras já filtradas
- `tokens_comparacao`, lista usada no TF-IDF, normalmente com stemming
- `texto_processado`, string montada a partir dos tokens de comparação

### Função remover_acentos(texto)

Remove acentos e marcas especiais usando `unidecode`.

Entrada:

- uma string

Saída:

- string normalizada sem acentos

Exemplo conceitual:

```text
"computação" vira "computacao"
```

### Função normalizar_texto(texto)

Aplica uma limpeza inicial no texto.

O que faz:

- converte `None` para string vazia
- transforma o conteúdo em string
- deixa em minúsculas
- remove acentos
- substitui pontuação por espaço
- remove espaços repetidos

Por que existe:

- para deixar respostas diferentes em um formato comparável

### Função tokenizar(texto)

Quebra o texto normalizado em tokens.

O que ela captura:

- letras de `a` a `z`
- números

Retorno:

- lista de strings

### Função radicalizar_token(token)

Aplica stemming em uma palavra.

Entrada:

- token individual

Saída:

- radical gerado pelo NLTK

Observação:

- o radical pode não ser uma palavra bonita para leitura humana
- ele existe para comparação computacional

### Função preprocessar_texto(texto, remover_stopwords, aplicar_stemming, stopwords)

Função principal do módulo de pré-processamento.

O que faz:

- normaliza texto
- tokeniza
- remove stopwords, se configurado
- aplica stemming, se configurado
- devolve um objeto `TextoProcessado`

Quando usar:

- antes de comparar uma resposta esperada e uma resposta do usuário

### Função extrair_palavras_chave(tokens, limite)

Escolhe palavras importantes a partir dos tokens da resposta esperada.

Como decide:

- ignora tokens muito curtos
- calcula frequência
- prioriza palavras mais frequentes
- preserva a ordem de primeira aparição como critério de desempate

Uso no projeto:

- calcular a cobertura de palavras-chave
- exibir quais termos importantes o usuário mencionou

## 12. Arquivo avaliador.py

Responsabilidade geral:

- receber textos pré-processados
- calcular similaridade
- calcular nota
- classificar feedback
- criar observações explicativas

### Classe ConfiguracaoAvaliacao

Guarda os parâmetros da avaliação.

Campos principais:

- `remover_stopwords`, liga ou desliga remoção de stopwords
- `aplicar_stemming`, liga ou desliga stemming
- `peso_similaridade`, peso da similaridade na nota
- `peso_palavras_chave`, peso das palavras-chave na nota
- `limite_palavras_chave`, quantidade máxima de palavras-chave extraídas
- `limite_entendeu`, pontuação mínima para `Entendeu`
- `limite_parcial`, pontuação mínima para `Parcial`

### Método ConfiguracaoAvaliacao.soma_pesos()

Retorna a soma dos pesos configurados.

Uso:

- normalizar a nota quando os pesos são combinados

### Classe ResultadoAvaliacao

Data class com todo o resultado da avaliação.

Campos principais:

- `pergunta`
- `resposta_esperada`
- `resposta_usuario`
- `resposta_esperada_processada`
- `resposta_usuario_processada`
- `similaridade`
- `cobertura_palavras_chave`
- `nota`
- `feedback`
- `palavras_chave_esperadas`
- `palavras_chave_encontradas`
- `observacoes`

### Função _validar_configuracao(configuracao)

Helper interno.

O que valida:

- a soma dos pesos precisa ser maior que zero
- o limite de `Parcial` não pode ser maior que o limite de `Entendeu`

Por que existe:

- impede configurações incoerentes antes de calcular nota

### Função calcular_similaridade_tfidf(tokens_esperados, tokens_usuario)

Calcula similaridade textual.

Etapas:

- junta tokens em duas strings
- cria um `TfidfVectorizer`
- gera matriz TF-IDF para resposta esperada e resposta do usuário
- calcula similaridade do cosseno
- retorna um número entre `0` e `1`, na maioria dos casos

Se algum texto ficar vazio:

- retorna `0.0`

### Função _classificar_feedback(nota, configuracao)

Helper interno.

Transforma a nota num rótulo textual.

Regra padrão:

- `70` ou mais, `Entendeu`
- de `30` até `69.99`, `Parcial`
- abaixo de `30`, `Nao entendeu`

### Função _gerar_observacoes(...)

Helper interno.

Cria frases de interpretação para o resultado.

Pode indicar:

- resposta vazia
- proximidade textual baixa, moderada ou alta
- ausência de palavras-chave
- cobertura parcial de palavras-chave
- resposta curta demais
- palavras-chave encontradas

### Função avaliar_resposta(pergunta, resposta_esperada, resposta_usuario, configuracao)

Função principal do sistema.

Fluxo:

- cria configuração padrão, se nenhuma configuração for recebida
- valida a configuração
- rejeita resposta esperada vazia
- pré-processa resposta esperada
- pré-processa resposta do usuário
- extrai palavras-chave da resposta esperada
- verifica quais palavras-chave aparecem na resposta do usuário
- calcula cobertura de palavras-chave
- calcula similaridade TF-IDF
- combina similaridade e cobertura em uma nota
- classifica feedback
- gera observações
- retorna `ResultadoAvaliacao`

Essa é a melhor função para reutilizar caso alguém queira criar uma interface gráfica, uma API ou uma tela web.

## 13. Arquivo main.py

Responsabilidade geral:

- oferecer uma interface de terminal para o usuário final

### Variável console

Objeto `Console` do Rich.

Uso:

- imprimir painéis, tabelas e textos formatados

### Função construir_parser()

Cria o parser de argumentos da CLI.

Define as opções:

- `--pergunta`
- `--esperada`
- `--usuario`
- `--manter-stopwords`
- `--detalhes`
- `--sem-stemming`

### Função ler_entrada_interativa()

Solicita dados no terminal.

Retorna:

- pergunta
- resposta esperada
- resposta do usuário

Quando é usada:

- quando o usuário roda `python main.py` sem informar argumentos

### Função exibir_resultado(resultado, mostrar_detalhes)

Mostra a avaliação no terminal.

Sempre exibe:

- pergunta
- nota final
- feedback
- similaridade TF-IDF
- cobertura de palavras-chave
- leitura do resultado

Quando `mostrar_detalhes=True`, exibe também:

- tokens da resposta esperada
- tokens da resposta do usuário
- radicais usados na comparação
- palavras-chave esperadas
- palavras-chave encontradas

### Função main()

Ponto de entrada da CLI.

Fluxo:

- constrói parser
- lê argumentos
- valida se `--pergunta`, `--esperada` e `--usuario` foram enviados juntos
- entra no modo interativo quando faltam argumentos
- cria `ConfiguracaoAvaliacao`
- chama `avaliar_resposta`
- chama `exibir_resultado`

## 14. Arquivo testes_exemplos.py

Responsabilidade geral:

- rodar casos preparados em `exemplos.json`
- apoiar a apresentação e a análise crítica

### Constante ARQUIVO_EXEMPLOS

Caminho do arquivo `exemplos.json`.

### Variável console

Objeto `Console` do Rich.

Uso:

- imprimir os resultados dos exemplos com melhor formatação

### Função carregar_exemplos()

Lê o JSON de exemplos.

Retorno:

- lista de dicionários com pergunta, resposta esperada, resposta do usuário e expectativa

### Função main()

Executa a bateria de exemplos.

Fluxo:

- carrega exemplos
- avalia cada resposta
- compara feedback do sistema com expectativa humana
- monta tabela de resumo
- imprime análise individual
- imprime resumo final

## 15. Arquivo tests/test_avaliador.py

Responsabilidade geral:

- proteger os comportamentos principais com testes automatizados

### Classe TestPreprocessamento

Testa funções de pré-processamento.

### Método test_remove_acentos_e_pontuacao()

Confirma que o texto fica tokenizado sem pontuação.

### Método test_stemming_aproxima_variacoes_da_mesma_palavra()

Confirma que o stemming aproxima palavras da mesma família.

### Classe TestAvaliador

Testa a avaliação final.

### Método test_resposta_identica_recebe_nota_maxima()

Confirma que uma resposta igual à esperada recebe nota `100.0` e feedback `Entendeu`.

### Método test_resposta_vazia_recebe_nota_baixa()

Confirma que resposta vazia recebe nota `0.0` e feedback `Nao entendeu`.

### Método test_resposta_errada_fica_abaixo_do_limite_parcial()

Confirma que uma resposta claramente errada fica abaixo do limite parcial.

## 16. Arquivo exemplos.json

Responsabilidade geral:

- guardar cenários de demonstração

Campos de cada exemplo:

- `nome`, descrição curta do cenário
- `pergunta`, pergunta do exercício
- `resposta_esperada`, referência de resposta correta
- `resposta_usuario`, texto avaliado pelo sistema
- `expectativa`, julgamento humano esperado

## 17. Como interpretar um resultado

Exemplo de saída:

```text
Nota final: 39.77/100
Feedback: Parcial
Similaridade TF-IDF: 37.21%
Cobertura de palavras-chave: 50.00%
```

Leitura:

- a nota final é a combinação entre similaridade e palavras-chave
- a similaridade mostra proximidade entre os vetores TF-IDF
- a cobertura mostra quantas palavras-chave esperadas apareceram
- feedback parcial significa que houve alguma proximidade, mas não suficiente para considerar compreensão completa

## 18. Limitações conhecidas

O sistema não entende linguagem como uma pessoa.

Limitações:

- não entende contexto profundo
- não entende ironia
- não valida conhecimento factual externo
- não reconhece todos os sinônimos
- pode penalizar paráfrases corretas
- pode favorecer respostas que repetem palavras-chave sem explicar bem
- pode ser sensível à resposta esperada escolhida

## 19. Boas práticas para usar na apresentação

Recomendação:

- mostre uma resposta correta e direta
- mostre uma resposta incompleta
- mostre uma resposta errada
- mostre uma resposta correta com palavras muito diferentes
- explique pelo menos um erro do sistema
- diga que similaridade textual não é compreensão real

## 20. Possíveis melhorias futuras

Melhorias sustentáveis:

- adicionar lematização em português
- usar embeddings semânticos
- criar interface web
- salvar histórico de avaliações
- permitir cadastro de várias respostas esperadas por pergunta
- extrair palavras-chave com método estatístico mais robusto
- melhorar mensagens para o aluno, apontando conceitos ausentes
- criar testes com dados reais de respostas de estudantes

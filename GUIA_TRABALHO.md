# Guia do Trabalho: "A máquina entendeu?"

Este arquivo resume o que aparece nos PDFs do repositório e organiza um caminho prático para fazer o trabalho.

Arquivos lidos:

- `Processamento de Linguagem Natural (Pln) .pdf`
- `Sistema de verificação de respostas com PLN.pdf`

## 1. O que é o trabalho

A atividade em grupo pede um sistema simples em Python para verificar se uma resposta de usuário está parecida com uma resposta esperada.

O programa deve receber:

- uma pergunta
- uma resposta esperada
- uma resposta do usuário

E deve retornar:

- a similaridade entre as respostas
- uma nota de `0` a `100`
- um feedback como `Entendeu`, `Parcial` ou `Não entendeu`

## 2. O que a professora espera

Pelo enunciado, a expectativa principal não é só "fazer rodar". Ela quer que o grupo mostre:

- um sistema funcionando
- uso dos conceitos vistos em aula, especialmente pré-processamento e similaridade de textos
- testes com exemplos diferentes
- análise crítica do resultado
- discussão sobre os limites de dizer que a máquina realmente "entendeu"

Em termos práticos, a professora parece esperar três coisas ao mesmo tempo:

- implementação técnica
- experimentação com exemplos
- reflexão teórica

## 3. Implementação mínima obrigatória

Todos os grupos devem ter:

- entrada de dados
- pré-processamento simples
- `TF-IDF`
- similaridade do cosseno
- exibição da nota

Então, mesmo que o grupo tenha uma missão extra, isso aqui é a base obrigatória.

## 4. Missões extras por grupo

O PDF divide os grupos por diferenciação:

- Grupo 1: melhorar pré-processamento
- Grupo 2: adicionar inteligência linguística
- Grupo 3: criar interface
- Grupo 4: melhorar a avaliação da nota
- Grupo 5: criar testes e análise crítica

### Grupo 1

Ideias:

- remover stopwords
- melhorar limpeza de pontuação
- normalizar acentos e caixa
- comparar resultado antes e depois da limpeza

### Grupo 2

Ideias:

- aplicar stemming
- testar lematização, se for viável
- mostrar como palavras diferentes com mesma raiz afetam a similaridade

### Grupo 3

Ideias:

- interface em `tkinter`, `streamlit` ou interface de terminal bem organizada
- campos para pergunta, resposta esperada e resposta do usuário
- exibição clara da nota e do feedback

### Grupo 4

Ideias:

- criar faixas de nota mais coerentes
- separar nota por níveis: ruim, médio, bom, excelente
- combinar similaridade com regras extras, como presença de palavras-chave

### Grupo 5

Ideias:

- montar casos em que o sistema acerta
- montar casos em que o sistema erra
- mostrar que palavras parecidas nem sempre significam mesma ideia
- mostrar que respostas corretas com outras palavras podem receber nota injusta

## 5. O que vale a pena fazer para entregar bem

Um trabalho forte deve mostrar não só o resultado final, mas também o raciocínio do grupo. Um formato bom é:

1. explicar rapidamente o problema
2. mostrar como o texto foi tratado
3. mostrar como a similaridade foi calculada
4. mostrar a regra usada para gerar a nota
5. testar com exemplos bons e ruins
6. concluir se o sistema "entende" ou só compara palavras

## 6. Estrutura sugerida do projeto

Para o enunciado puro, uma estrutura mínima ainda seria suficiente. Mas o
repositório atual já evoluiu além desse mínimo.

Estrutura mínima conceitual:

```text
did-it-understand/
├─ main.py
├─ avaliador.py
├─ preprocessamento.py
├─ testes_exemplos.py
├─ requirements.txt
└─ README.md
```

Estrutura real do projeto hoje:

```text
did-it-understand/
├─ gui.py
├─ mais_ou_menos/
│  ├─ avaliador.py
│  ├─ preprocessamento.py
│  ├─ main.py
│  ├─ exemplos.json
│  ├─ test_avaliador.py
│  └─ testes_exemplos.py
├─ topzera/
│  ├─ avaliador_openai.py
│  └─ main.py
├─ README.md
├─ documentation.md
├─ documentacao_funcoes_pln.md
├─ GUIA_TRABALHO.md
└─ requirements.txt
```

Opinião técnica:

- essa estrutura atual é superior à versão mínima porque separa responsabilidades;
- `mais_ou_menos` concentra o motor clássico;
- `topzera` isola a integração com Azure OpenAI;
- `gui.py` reaproveita os dois motores sem duplicar regra de negócio.

## 7. Esquema de implementação

### Etapa 1. Entrada

Receber:

- pergunta
- resposta esperada
- resposta do usuário

### Etapa 2. Pré-processamento

Fazer pelo menos:

- transformar em minúsculas
- remover pontuação
- quebrar em tokens

Se o grupo quiser melhorar:

- remover stopwords
- remover acentos
- aplicar stemming ou lematização

### Etapa 3. Vetorização

Usar `TfidfVectorizer`.

A lógica mais direta:

- vetorizar resposta esperada
- vetorizar resposta do usuário
- comparar os vetores

### Etapa 4. Similaridade

Usar similaridade do cosseno.

Exemplo de interpretação:

- acima de `0.75`: entendeu
- entre `0.40` e `0.74`: parcial
- abaixo de `0.40`: não entendeu

Esses limites podem ser ajustados com base nos testes.

### Etapa 5. Nota

Transformar a similaridade em nota de `0` a `100`.

Exemplo simples:

- `nota = similaridade * 100`

Exemplo melhorado:

- nota baseada em similaridade
- ajuste por presença de palavras-chave essenciais
- classificação final por faixa

## 8. Bibliotecas que fazem sentido

- `scikit-learn` para `TF-IDF` e cosseno
- `nltk` para stopwords e stemming
- `unidecode` para normalização de acentos
- `tkinter` ou `streamlit` se houver interface

## 9. Ideias de testes para impressionar melhor

O próprio PDF já indica o tipo de teste que a professora quer ver. Então vale preparar casos como:

- resposta correta usando palavras diferentes
- resposta errada com palavras parecidas
- resposta incompleta
- resposta muito curta
- resposta que copia uma palavra-chave, mas não responde de fato

Exemplos de cenário:

- Pergunta: "O que é PLN?"
- Resposta esperada: "PLN é a área da computação que processa linguagem natural."
- Resposta do usuário correta com outras palavras: "É um campo da computação que permite analisar textos e linguagem humana."
- Resposta parecida, mas ruim: "PLN é linguagem com palavras processadas."

## 10. O que dizer na análise crítica

Essa parte parece muito importante no enunciado.

O PDF de PLN ajuda a sustentar a discussão: linguagem natural envolve morfologia, sintaxe, semântica e pragmática. Já o sistema da atividade compara textos por similaridade, então ele está muito mais perto de comparar palavras e padrões do que de entender significado de verdade.

Pontos bons para comentar:

- o sistema pode funcionar bem quando as respostas usam vocabulário parecido
- ele pode falhar quando duas respostas têm o mesmo sentido com palavras diferentes
- ele pode dar nota alta para uma resposta superficial que repete termos importantes
- similaridade textual não é o mesmo que compreensão semântica
- isso mostra limites do PLN mais simples

## 11. O que provavelmente a professora vai observar na apresentação

- se o grupo implementou a base obrigatória
- se a missão extra foi realmente feita
- se os testes fazem sentido
- se o grupo consegue explicar por que o sistema acertou ou errou
- se a discussão final mostra senso crítico

Ou seja: não basta mostrar a nota saindo na tela. É importante justificar o comportamento do sistema.

## 12. Roteiro de apresentação

Um roteiro seguro:

1. apresentar o objetivo do sistema
2. abrir a GUI para mostrar a entrada e a saída de forma visual
3. explicar que a GUI só orquestra dois motores já existentes
4. explicar o pré-processamento da versão `mais_ou_menos`
5. explicar `TF-IDF` e cosseno de forma simples
6. mostrar a regra da nota e a cobertura de palavras-chave
7. trocar para `topzera` e explicar a avaliação semântica
8. rodar testes diferentes
9. mostrar casos em que funciona e em que falha
10. concluir que comparar texto não equivale, por si só, a entender linguagem

## 13. Caminho mais seguro para tirar uma boa impressão

Se a ideia for fazer um trabalho consistente sem complicar demais:

- implementar bem a versão básica
- deixar o código limpo
- preparar testes claros
- fazer uma boa análise crítica

Se quiser destacar mais:

- adicionar interface
- comparar versão básica e versão melhorada
- mostrar métricas ou tabela de testes

## 14. Sugestão de divisão entre integrantes

- pessoa 1: pré-processamento
- pessoa 2: cálculo de similaridade e nota
- pessoa 3: interface ou organização da apresentação
- pessoa 4: testes e análise crítica

## 15. Resumo final

Em resumo, a professora parece esperar um trabalho que mostre:

- aplicação prática de PLN básico
- uso de `TF-IDF` e similaridade do cosseno
- melhoria ou diferenciação por grupo
- testes bem pensados
- reflexão sobre os limites da técnica

Se o grupo entregar um sistema funcional, exemplos convincentes e uma discussão honesta sobre onde ele falha, já estará alinhado com o espírito da atividade.

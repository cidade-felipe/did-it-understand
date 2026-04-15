# Documentação das funções do trabalho de PLN

## 1. Objetivo deste documento

Este documento explica, função por função, as duas formas implementadas no projeto **Did It Understand?** para avaliar se uma resposta do usuário está próxima de uma resposta esperada.

As duas abordagens são:

- `mais_ou_menos`, abordagem clássica de PLN com pré-processamento, TF-IDF, similaridade do cosseno e cobertura de palavras-chave.
- `topzera`, abordagem semântica com Azure OpenAI, em que um modelo de linguagem avalia a resposta com base no significado.

Fato: as duas versões recebem pergunta, resposta esperada e resposta do usuário.

Fato: as duas retornam uma avaliação, mas usam critérios diferentes.

Inferência: a versão clássica é melhor para explicar conceitos básicos de PLN, enquanto a versão com IA é melhor para lidar com respostas escritas com outras palavras.

Opinião técnica: para apresentação do trabalho, vale mostrar as duas versões juntas, porque isso deixa claro o trade-off entre transparência, custo, dependência externa e capacidade semântica.

## 2. Visão geral das duas formas

### 2.1. Forma 1: `mais_ou_menos`

Essa versão é determinística. Isso significa que, usando a mesma entrada e a mesma configuração, o resultado tende a ser o mesmo.

Ela trabalha com estas etapas:

1. Recebe os textos.
2. Normaliza os textos.
3. Quebra os textos em tokens.
4. Remove palavras pouco informativas, se essa opção estiver ativa.
5. Aplica stemming, se essa opção estiver ativa.
6. Calcula TF-IDF.
7. Calcula similaridade do cosseno.
8. Calcula cobertura de palavras-chave.
9. Gera nota e feedback.

Em termos simples, ela compara a proximidade textual entre a resposta esperada e a resposta do usuário.

### 2.2. Forma 2: `topzera`

Essa versão usa Azure OpenAI. Em vez de comparar somente tokens e frequência de palavras, ela envia a pergunta, a resposta esperada e a resposta do usuário para um modelo de linguagem.

Ela trabalha com estas etapas:

1. Carrega as configurações do `.env`.
2. Valida chave, endpoint, deployment e versão da API.
3. Cria um cliente do Azure OpenAI.
4. Monta mensagens de instrução para o modelo.
5. Solicita uma resposta em JSON.
6. Valida o JSON retornado.
7. Normaliza nota, feedback, similaridade e listas explicativas.

Em termos simples, ela tenta avaliar significado, lacunas, contradições e pontos corretos.

## 3. Funções da versão `mais_ou_menos`

### 3.1. Arquivo `mais_ou_menos/preprocessamento.py`

Esse arquivo concentra as funções responsáveis por transformar texto natural em uma representação mais adequada para comparação matemática.

#### `remover_acentos(texto: str) -> str`

Remove acentos e sinais diacríticos do texto usando `unidecode`.

Exemplo conceitual:

```text
"computação" vira "computacao"
```

Por que existe:

- evita que `computação` e `computacao` sejam tratadas como palavras diferentes;
- reduz ruído causado por digitação sem acento;
- facilita a comparação entre respostas.

Trade-off:

- melhora a padronização;
- perde parte da forma original da palavra, mas isso não prejudica o objetivo do trabalho.

#### `normalizar_texto(texto: str) -> str`

Prepara o texto para tokenização.

Ela faz:

- transforma `None` em texto vazio;
- converte tudo para minúsculas;
- remove acentos;
- remove pontuação;
- troca pontuação por espaço;
- remove espaços repetidos;
- remove espaços no início e no fim.

Exemplo conceitual:

```text
"PLN é útil!" vira "pln e util"
```

Por que existe:

- reduz diferenças superficiais entre textos;
- evita que pontuação e caixa alta influenciem indevidamente a comparação.

#### `tokenizar(texto: str) -> list[str]`

Divide o texto normalizado em palavras ou números.

Ela usa uma expressão regular para capturar sequências formadas por letras minúsculas e números.

Exemplo conceitual:

```text
"pln processa linguagem humana" vira ["pln", "processa", "linguagem", "humana"]
```

Por que existe:

- TF-IDF e stemming trabalham melhor com listas de termos;
- a comparação deixa de ser feita sobre uma frase inteira e passa a ser feita sobre unidades menores.

Limitação:

- a função não entende gramática, contexto ou relação semântica entre palavras.

#### `radicalizar_token(token: str) -> str`

Aplica stemming em um token usando `SnowballStemmer("portuguese")`.

Stemming reduz palavras a uma raiz aproximada.

Exemplo conceitual:

```text
"processar", "processa" e "processamento" podem ficar mais próximas
```

Por que existe:

- aproxima variações da mesma família de palavras;
- ajuda a comparar respostas que usam flexões diferentes.

Trade-off:

- melhora a comparação entre variações morfológicas;
- pode gerar radicais que não são palavras reais;
- pode aproximar termos que não deveriam ser considerados equivalentes em alguns contextos.

#### `preprocessar_texto(texto, remover_stopwords=True, aplicar_stemming=True, stopwords=None) -> TextoProcessado`

Executa o pipeline completo de pré-processamento.

Ela chama:

- `normalizar_texto`;
- `tokenizar`;
- remoção de stopwords;
- `radicalizar_token`, quando `aplicar_stemming=True`.

Ela retorna um objeto `TextoProcessado` com:

- `original`, texto recebido;
- `normalizado`, texto limpo;
- `tokens`, tokens depois da limpeza e possível remoção de stopwords;
- `tokens_comparacao`, tokens usados no cálculo de similaridade;
- `texto_processado`, versão em string dos tokens de comparação.

Por que existe:

- centraliza a preparação dos textos;
- evita duplicação no avaliador;
- facilita comparar a resposta esperada e a resposta do usuário com a mesma regra.

Ponto importante:

- se `remover_stopwords=True`, palavras comuns como `de`, `a`, `que`, `para` e `com` são removidas;
- se `aplicar_stemming=True`, a comparação usa os radicais, não necessariamente as palavras originais.

#### `extrair_palavras_chave(tokens: list[str], limite: int = 6) -> list[str]`

Seleciona as palavras-chave mais relevantes a partir dos tokens da resposta esperada.

A lógica usada é:

1. ignora tokens com tamanho menor ou igual a 2;
2. conta a frequência de cada token;
3. registra a primeira posição em que cada token aparece;
4. ordena por maior frequência;
5. em caso de empate, prioriza quem apareceu primeiro;
6. em novo empate, usa ordem alfabética;
7. retorna até `limite` palavras.

Por que existe:

- complementa a similaridade TF-IDF com uma métrica mais explicável;
- ajuda a dizer se a resposta do usuário citou os conceitos centrais da resposta esperada.

Trade-off:

- é simples e fácil de explicar;
- não sabe, sozinha, se uma palavra-chave foi usada corretamente.

### 3.2. Classe `TextoProcessado`

Embora não seja uma função, essa classe é importante porque organiza o resultado do pré-processamento.

Campos:

- `original`, texto original recebido;
- `normalizado`, texto depois de limpeza básica;
- `tokens`, lista de tokens relevantes;
- `tokens_comparacao`, lista usada na comparação;
- `texto_processado`, string final usada em exibição e depuração.

Por que existe:

- evita retornar várias variáveis soltas;
- deixa o código mais legível;
- facilita exibir detalhes no terminal.

## 4. Funções do avaliador clássico

### 4.1. Arquivo `mais_ou_menos/avaliador.py`

Esse arquivo contém o motor principal da avaliação clássica.

### 4.2. Classe `ConfiguracaoAvaliacao`

Guarda os parâmetros que controlam a avaliação.

Campos principais:

- `remover_stopwords`, define se stopwords serão removidas;
- `aplicar_stemming`, define se stemming será aplicado;
- `peso_similaridade`, peso da similaridade TF-IDF na nota;
- `peso_palavras_chave`, peso da cobertura de palavras-chave na nota;
- `limite_palavras_chave`, quantidade máxima de palavras-chave extraídas;
- `limite_entendeu`, nota mínima para feedback `Entendeu`;
- `limite_parcial`, nota mínima para feedback `Parcial`.

#### `soma_pesos(self) -> float`

Retorna a soma de `peso_similaridade` e `peso_palavras_chave`.

Por que existe:

- permite normalizar a nota mesmo que os pesos sejam alterados;
- evita deixar a fórmula presa aos valores `0.8` e `0.2`.

Exemplo:

```text
peso_similaridade = 0.8
peso_palavras_chave = 0.2
soma_pesos = 1.0
```

### 4.3. Classe `ResultadoAvaliacao`

Organiza tudo que o avaliador clássico retorna.

Campos principais:

- pergunta;
- resposta esperada;
- resposta do usuário;
- textos processados;
- similaridade;
- cobertura de palavras-chave;
- nota;
- feedback;
- palavras-chave esperadas;
- palavras-chave encontradas;
- observações.

Por que existe:

- evita que `avaliar_resposta` retorne uma tupla grande e confusa;
- facilita exibir resultado na CLI;
- ajuda os testes a verificarem partes específicas da avaliação.

### 4.4. `_validar_configuracao(configuracao: ConfiguracaoAvaliacao) -> None`

Valida se os parâmetros da configuração fazem sentido.

Ela verifica:

- se a soma dos pesos é maior que zero;
- se o limite de `Parcial` não é maior que o limite de `Entendeu`.

Por que existe:

- impede cálculos inválidos;
- evita resultados incoerentes;
- antecipa erros de configuração.

Exemplo de problema evitado:

```text
peso_similaridade = 0
peso_palavras_chave = 0
```

Nesse caso, a nota não poderia ser calculada corretamente.

### 4.5. `calcular_similaridade_tfidf(tokens_esperados, tokens_usuario) -> float`

Calcula a similaridade entre a resposta esperada e a resposta do usuário usando TF-IDF e similaridade do cosseno.

Etapas:

1. junta os tokens esperados em uma string;
2. junta os tokens do usuário em uma string;
3. retorna `0.0` se algum documento estiver vazio;
4. cria um `TfidfVectorizer`;
5. transforma os dois textos em vetores TF-IDF;
6. calcula a similaridade do cosseno entre os vetores;
7. retorna um número entre `0.0` e `1.0`.

Por que existe:

- é a principal métrica textual do trabalho;
- mede o quanto as duas respostas compartilham termos relevantes.

Interpretação:

- valor próximo de `1.0` indica alta proximidade textual;
- valor próximo de `0.0` indica baixa sobreposição de termos.

Limitação:

- TF-IDF não entende significado profundo;
- duas frases corretas com vocabulário muito diferente podem ter similaridade baixa.

### 4.6. `_classificar_feedback(nota, configuracao) -> str`

Transforma a nota numérica em feedback textual.

Regra padrão:

- nota maior ou igual a `70`: `Entendeu`;
- nota entre `30` e `69.99`: `Parcial`;
- nota abaixo de `30`: `Nao entendeu`.

Por que existe:

- converte uma métrica quantitativa em uma mensagem fácil de interpretar;
- separa a regra de classificação do cálculo da nota.

Trade-off:

- é simples e explicável;
- os limites podem precisar de ajuste com base em exemplos reais.

### 4.7. `_gerar_observacoes(...) -> list[str]`

Cria explicações textuais sobre o resultado da avaliação.

Ela considera:

- se a resposta ficou vazia depois do pré-processamento;
- se a similaridade foi alta, moderada ou baixa;
- se houve cobertura de palavras-chave;
- se a resposta do usuário é muito mais curta que a esperada;
- quais palavras-chave foram encontradas.

Por que existe:

- a nota sozinha não explica o resultado;
- as observações ajudam na apresentação e na análise crítica;
- ajudam a mostrar quando a técnica pode acertar ou falhar.

Exemplo de observação:

```text
"A proximidade textual ficou baixa, indicando pouca sobreposição de termos."
```

### 4.8. `avaliar_resposta(pergunta, resposta_esperada, resposta_usuario, configuracao=None) -> ResultadoAvaliacao`

É a função principal da versão clássica.

Ela coordena todo o processo:

1. usa a configuração recebida ou cria uma configuração padrão;
2. valida a configuração;
3. rejeita resposta esperada vazia;
4. pré-processa a resposta esperada;
5. pré-processa a resposta do usuário;
6. extrai palavras-chave da resposta esperada;
7. identifica palavras-chave encontradas na resposta do usuário;
8. calcula a cobertura de palavras-chave;
9. calcula a similaridade TF-IDF;
10. calcula a nota final;
11. classifica o feedback;
12. gera observações;
13. retorna um `ResultadoAvaliacao`.

Fórmula padrão:

```text
nota_base = (similaridade * 0.8 + cobertura_palavras_chave * 0.2) / 1.0
nota = nota_base * 100
```

Por que existe:

- é o ponto central da implementação clássica;
- reúne pré-processamento, métricas, nota, feedback e explicação em uma única chamada.

Opinião técnica:

- a função está bem posicionada como orquestradora, porque as tarefas menores foram separadas em funções auxiliares.

## 5. Funções da CLI clássica

### 5.1. Arquivo `mais_ou_menos/main.py`

Esse arquivo permite usar a versão clássica pelo terminal.

### 5.2. `construir_parser() -> argparse.ArgumentParser`

Cria e configura o parser de argumentos da linha de comando.

Argumentos aceitos:

- `--pergunta`;
- `--esperada`;
- `--usuario`;
- `--manter-stopwords`;
- `--detalhes`;
- `--sem-stemming`.

Por que existe:

- permite executar o programa de forma interativa ou passando todos os dados por comando;
- facilita testes rápidos e demonstrações.

Exemplo de uso:

```powershell
venv\Scripts\python mais_ou_menos\main.py --pergunta "O que é PLN?" --esperada "PLN processa linguagem humana." --usuario "PLN analisa textos humanos." --detalhes
```

### 5.3. `ler_entrada_interativa() -> tuple[str, str, str]`

Pede ao usuário, no terminal, os três textos necessários:

- pergunta;
- resposta esperada;
- resposta do usuário.

Por que existe:

- permite usar o sistema sem conhecer argumentos de terminal;
- facilita a apresentação ao vivo.

### 5.4. `exibir_resultado(resultado, mostrar_detalhes=False) -> None`

Mostra o resultado da avaliação no terminal usando tabelas e textos formatados com `rich`.

Exibe:

- pergunta;
- nota final;
- feedback;
- similaridade TF-IDF;
- cobertura de palavras-chave;
- detalhes do pré-processamento, se `mostrar_detalhes=True`;
- observações interpretativas.

Por que existe:

- separa cálculo de apresentação;
- melhora a legibilidade da saída no terminal;
- ajuda a explicar o resultado durante a demonstração.

### 5.5. `main() -> None`

É o ponto de entrada da CLI clássica.

Ela faz:

1. cria o parser;
2. lê os argumentos;
3. valida se os três textos foram passados juntos;
4. usa argumentos ou modo interativo;
5. monta a `ConfiguracaoAvaliacao`;
6. chama `avaliar_resposta`;
7. chama `exibir_resultado`.

Por que existe:

- organiza o fluxo completo de execução pelo terminal;
- mantém a função `avaliar_resposta` independente da interface.

## 6. Funções de exemplos e testes da versão clássica

### 6.1. Arquivo `mais_ou_menos/testes_exemplos.py`

Esse arquivo roda casos prontos de demonstração.

#### `carregar_exemplos() -> list[dict[str, str]]`

Lê o arquivo `exemplos.json` e retorna os exemplos como lista de dicionários.

Por que existe:

- separa os dados de teste do código;
- facilita adicionar novos exemplos sem alterar a lógica.

#### `main() -> None`

Executa todos os exemplos cadastrados.

Ela faz:

1. carrega os exemplos;
2. avalia cada resposta;
3. compara o feedback do sistema com a expectativa humana;
4. imprime análise individual;
5. imprime uma tabela consolidada;
6. informa quantos exemplos bateram com a expectativa humana.

Por que existe:

- ajuda na apresentação;
- mostra casos em que o sistema acerta;
- mostra divergências úteis para a análise crítica.

### 6.2. Arquivo `mais_ou_menos/test_avaliador.py`

Esse arquivo contém testes automatizados com `unittest`.

#### `test_remove_acentos_e_pontuacao()`

Confirma que o pré-processamento remove acentos e pontuação.

Por que existe:

- garante que a limpeza básica do texto funciona;
- evita regressões em uma etapa essencial.

#### `test_stemming_aproxima_variacoes_da_mesma_palavra()`

Confirma que o stemming aproxima variações como `processar` e `processa`.

Por que existe:

- valida a parte de inteligência linguística simples;
- mostra, na prática, por que o stemming foi incluído.

#### `test_resposta_identica_recebe_nota_maxima()`

Verifica se uma resposta idêntica à esperada recebe feedback `Entendeu` e nota `100`.

Por que existe:

- valida o caso mais básico de acerto;
- garante que a fórmula não penaliza respostas iguais.

#### `test_resposta_vazia_recebe_nota_baixa()`

Verifica se uma resposta vazia recebe feedback `Nao entendeu` e nota `0`.

Por que existe:

- garante tratamento adequado para ausência de resposta;
- evita que entradas vazias gerem resultado enganoso.

#### `test_resposta_errada_fica_abaixo_do_limite_parcial()`

Verifica se uma resposta conceitualmente errada não passa do limite esperado.

Por que existe:

- testa um cenário de risco, quando há algumas palavras parecidas, mas o sentido é ruim;
- ajuda a calibrar a avaliação.

## 7. Funções da versão `topzera`

### 7.1. Arquivo `topzera/avaliador_openai.py`

Esse arquivo contém o motor da avaliação semântica com Azure OpenAI.

### 7.2. Classe `ConfiguracaoAzureOpenAI`

Guarda os dados necessários para chamar o Azure OpenAI.

Campos:

- `api_key`, chave de acesso;
- `endpoint`, endereço do recurso Azure;
- `deployment`, nome do deployment configurado no Azure;
- `api_version`, versão da API;
- `temperatura`, valor opcional de temperatura.

Por que existe:

- centraliza configuração;
- evita passar muitos parâmetros soltos entre funções;
- facilita validação e manutenção.

### 7.3. Classe `ResultadoAvaliacaoIA`

Organiza a resposta final da avaliação com IA.

Campos:

- pergunta;
- resposta esperada;
- resposta do usuário;
- nota;
- feedback;
- similaridade semântica;
- justificativa;
- pontos corretos;
- lacunas;
- alertas.

Por que existe:

- transforma o JSON do modelo em um objeto previsível;
- facilita exibição no terminal;
- reduz risco de lidar com campos ausentes diretamente na interface.

### 7.4. `carregar_configuracao() -> ConfiguracaoAzureOpenAI`

Carrega e valida as variáveis de ambiente necessárias.

Ela faz:

1. chama `load_dotenv()` para carregar o `.env`;
2. lê a chave da API;
3. lê e normaliza o endpoint;
4. lê o nome do deployment;
5. lê a versão da API ou usa a padrão;
6. lê a temperatura opcional;
7. verifica se falta algum campo obrigatório;
8. retorna `ConfiguracaoAzureOpenAI`.

Variáveis aceitas:

- chave: `AZURE_OPENAI_API_KEY` ou `OPENAI_API_KEY`;
- endpoint: `AZURE_OPENAI_ENDPOINT` ou `AZURE_ENDPOINT`;
- deployment: `AZURE_OPENAI_DEPLOYMENT`, `AZURE_OPENAI_MODEL`, `AZURE_DEPLOYMENT` ou `OPENAI_MODEL`;
- versão: `AZURE_OPENAI_API_VERSION` ou `OPENAI_API_VERSION`.

Por que existe:

- separa configuração da lógica de avaliação;
- evita erro silencioso por variável ausente;
- melhora a mensagem de erro para o usuário.

### 7.5. `obter_env(*nomes: str) -> str`

Busca a primeira variável de ambiente preenchida entre os nomes informados.

Se nenhuma existir, retorna string vazia.

Por que existe:

- permite aceitar nomes alternativos para a mesma configuração;
- simplifica `carregar_configuracao`.

### 7.6. `obter_env_opcional(*nomes: str) -> str | None`

Busca a primeira variável de ambiente válida entre os nomes informados.

Se nenhuma existir, retorna `None`.

Diferença para `obter_env`:

- `obter_env` retorna `""` quando não encontra valor;
- `obter_env_opcional` retorna `None`.

Por que existe:

- diferencia configuração obrigatória de configuração opcional;
- evita repetição de código ao ler várias variáveis.

### 7.7. `carregar_temperatura() -> float | None`

Lê `AZURE_OPENAI_TEMPERATURE`.

Comportamento:

- se a variável não existir ou estiver vazia, retorna `None`;
- se existir, tenta converter para `float`;
- se a conversão falhar, lança erro explicando que precisa ser número.

Por que existe:

- alguns deployments do Azure OpenAI não aceitam temperatura customizada;
- enviar temperatura só quando configurada evita erro em deployments mais restritos.

Trade-off:

- aumenta a compatibilidade;
- deixa a temperatura padrão nas mãos do deployment quando a variável não é definida.

### 7.8. `normalizar_endpoint_azure(endpoint: str) -> str`

Limpa o endpoint do Azure para ficar no formato esperado pelo SDK.

Ela faz:

- remove espaços;
- retorna string vazia se o endpoint estiver vazio;
- analisa a URL;
- remove qualquer trecho a partir de `/openai`;
- remove query string;
- garante barra final.

Exemplo:

```text
https://meu-recurso.cognitiveservices.azure.com/openai/deployments/x?api-version=...
```

vira:

```text
https://meu-recurso.cognitiveservices.azure.com/
```

Por que existe:

- o SDK espera o endpoint base do recurso;
- copiar uma URL completa do portal pode causar erro;
- a função torna a configuração mais tolerante.

### 7.9. `criar_cliente(configuracao: ConfiguracaoAzureOpenAI)`

Cria o cliente `AzureOpenAI`.

Ela faz:

1. tenta importar `AzureOpenAI` da biblioteca `openai`;
2. se a biblioteca não existir, gera erro com orientação de instalação;
3. instancia o cliente com versão da API, endpoint e chave.

Por que existe:

- isola a criação do cliente;
- melhora a mensagem de erro quando a dependência não está instalada;
- facilita testes futuros com mock.

### 7.10. `avaliar_resposta_com_ia(pergunta, resposta_esperada, resposta_usuario, configuracao=None) -> ResultadoAvaliacaoIA`

É a função principal da versão com IA.

Ela faz:

1. valida se pergunta, resposta esperada e resposta do usuário não estão vazias;
2. carrega configuração, se nenhuma foi passada;
3. cria o cliente Azure OpenAI;
4. monta os parâmetros da chamada;
5. adiciona temperatura somente quando configurada;
6. chama `cliente.chat.completions.create`;
7. lê o conteúdo retornado pelo modelo;
8. converte o conteúdo JSON em dicionário;
9. monta e retorna `ResultadoAvaliacaoIA`.

Por que existe:

- concentra o fluxo de avaliação semântica;
- mantém o restante do programa independente dos detalhes da API;
- transforma uma chamada externa em um resultado estruturado.

Riscos em ambiente real:

- custo por uso;
- dependência de internet;
- indisponibilidade da API;
- resposta inválida ou fora do formato esperado;
- julgamento inconsistente em casos ambíguos.

### 7.11. `montar_mensagens(pergunta, resposta_esperada, resposta_usuario) -> list[dict[str, str]]`

Monta as mensagens enviadas ao modelo.

Ela cria:

- uma mensagem de sistema, com regras de avaliação;
- uma mensagem de usuário, com pergunta, resposta esperada e resposta do usuário.

A instrução pede que o modelo:

- avalie significado, não só palavras idênticas;
- aceite paráfrases corretas;
- penalize contradições, fuga do tema e vagueza;
- retorne somente JSON válido.

Por que existe:

- separa engenharia de prompt da chamada à API;
- deixa claro o critério esperado do avaliador;
- facilita ajustes futuros na rubrica.

Opinião técnica:

- essa é uma das funções mais importantes da versão com IA, porque a qualidade da avaliação depende muito da instrução enviada ao modelo.

### 7.12. `montar_resultado(pergunta, resposta_esperada, resposta_usuario, dados) -> ResultadoAvaliacaoIA`

Transforma o dicionário retornado pelo modelo em `ResultadoAvaliacaoIA`.

Ela normaliza:

- `nota`, limitada entre `0` e `100`;
- `similaridade_semantica`, limitada entre `0.0` e `1.0`;
- `feedback`, convertido para um dos rótulos aceitos;
- `pontos_corretos`, `lacunas` e `alertas`, convertidos para listas limpas.

Por que existe:

- modelos podem retornar valores fora do esperado;
- a interface precisa de um objeto consistente;
- reduz risco de erro ao exibir o resultado.

### 7.13. `carregar_resultado_json(conteudo: str) -> dict[str, Any]`

Converte o texto retornado pelo modelo em JSON.

Ela faz:

- tenta aplicar `json.loads`;
- se falhar, lança erro dizendo que o modelo não retornou JSON válido;
- verifica se o JSON é um objeto;
- retorna o dicionário.

Por que existe:

- a saída do modelo precisa ser confiável para o restante do código;
- evita tentar usar uma string comum como se fosse dicionário.

### 7.14. `limitar_float(valor, minimo, maximo) -> float`

Converte um valor para `float` e limita esse valor a uma faixa.

Exemplo:

```text
limitar_float(120, 0, 100) retorna 100
limitar_float(-5, 0, 100) retorna 0
```

Se o valor não puder ser convertido, usa o mínimo.

Por que existe:

- protege o sistema contra respostas fora da escala;
- garante que nota e similaridade fiquem em limites válidos.

### 7.15. `normalizar_feedback(feedback_modelo: str, nota: float) -> str`

Converte o feedback retornado pelo modelo para um dos rótulos aceitos:

- `Entendeu`;
- `Parcial`;
- `Nao entendeu`.

Ela aceita variações como:

- `correto`;
- `entende`;
- `entendeu parcialmente`;
- `meio certo`;
- `errado`;
- `incorreto`.

Se o texto não for reconhecido, usa a nota para decidir.

Regra de fallback:

- nota maior ou igual a `70`: `Entendeu`;
- nota maior ou igual a `30`: `Parcial`;
- nota abaixo de `30`: `Nao entendeu`.

Por que existe:

- modelos podem variar palavras;
- a aplicação precisa de feedback padronizado.

### 7.16. `normalizar_lista(valor: Any) -> list[str]`

Garante que um campo seja retornado como lista de strings limpas.

Comportamento:

- se `valor` não for lista, retorna lista vazia;
- transforma cada item em string;
- remove espaços extras;
- descarta itens vazios.

Por que existe:

- protege a interface contra formatos inesperados;
- evita imprimir listas com valores vazios ou inválidos.

## 8. Funções da CLI com IA

### 8.1. Arquivo `topzera/main.py`

Esse arquivo permite usar a versão com Azure OpenAI pelo terminal.

### 8.2. `construir_parser() -> argparse.ArgumentParser`

Cria o parser de argumentos da versão com IA.

Argumentos aceitos:

- `--pergunta`;
- `--esperada`;
- `--usuario`;
- `--check-config`.

Por que existe:

- permite uso por linha de comando;
- permite validar configuração sem gastar tokens com chamada à API.

### 8.3. `ler_entrada_interativa() -> tuple[str, str, str]`

Pede pergunta, resposta esperada e resposta do usuário no terminal.

Por que existe:

- facilita demonstração manual;
- permite usar o programa sem passar argumentos.

### 8.4. `exibir_resultado(resultado: ResultadoAvaliacaoIA) -> None`

Mostra a avaliação feita pela IA.

Exibe:

- feedback;
- nota;
- similaridade semântica;
- justificativa;
- pontos corretos;
- lacunas;
- alertas.

Por que existe:

- separa apresentação da avaliação;
- torna o resultado mais compreensível para quem está assistindo à demonstração.

### 8.5. `imprimir_lista(titulo: str, itens: list[str]) -> None`

Imprime uma lista com título, se houver itens.

Por que existe:

- evita repetir código para `pontos_corretos`, `lacunas` e `alertas`;
- não imprime seções vazias.

### 8.6. `executar_check_config() -> int`

Valida a configuração carregando as variáveis de ambiente e imprimindo endpoint, deployment e versão da API.

Ela não chama a API para avaliar uma resposta.

Por que existe:

- confirma se o `.env` está configurado;
- reduz risco de erro durante apresentação;
- evita gasto de tokens apenas para testar configuração básica.

### 8.7. `main() -> int`

É o ponto de entrada da CLI com IA.

Ela faz:

1. cria o parser;
2. lê os argumentos;
3. se `--check-config` estiver ativo, valida configuração e encerra;
4. valida se pergunta, esperada e usuário foram passados juntos;
5. usa argumentos ou modo interativo;
6. chama `avaliar_resposta_com_ia`;
7. chama `exibir_resultado`;
8. retorna `0` em sucesso;
9. captura erros, imprime no `stderr` e retorna `1`.

Por que existe:

- organiza o fluxo completo da versão com IA;
- permite que erros sejam mostrados sem quebrar o terminal com stack trace;
- retorna código de saída útil para automação.

## 9. Comparação prática entre as funções centrais

| Parte do problema | `mais_ou_menos` | `topzera` |
| --- | --- | --- |
| Entrada | `main()` e `ler_entrada_interativa()` | `main()` e `ler_entrada_interativa()` |
| Preparação | `preprocessar_texto()` | `montar_mensagens()` |
| Núcleo da avaliação | `avaliar_resposta()` | `avaliar_resposta_com_ia()` |
| Métrica principal | `calcular_similaridade_tfidf()` | julgamento do modelo via API |
| Explicação | `_gerar_observacoes()` | `justificativa`, `pontos_corretos`, `lacunas`, `alertas` |
| Padronização do resultado | `ResultadoAvaliacao` | `ResultadoAvaliacaoIA` |
| Validação | `_validar_configuracao()` | `carregar_configuracao()` e `carregar_resultado_json()` |
| Exibição | `exibir_resultado()` | `exibir_resultado()` |

## 10. Melhor forma de explicar o trabalho

A melhor explicação para apresentação é:

1. A versão `mais_ou_menos` mostra como PLN clássico transforma texto em dados comparáveis.
2. O pré-processamento reduz ruído, como acentos, pontuação e palavras comuns.
3. O TF-IDF mede a importância dos termos nos dois textos.
4. A similaridade do cosseno mede a proximidade entre os vetores.
5. A cobertura de palavras-chave adiciona uma regra simples para conceitos centrais.
6. A versão `topzera` usa um modelo de linguagem para avaliar significado, não só palavras parecidas.
7. A comparação entre as duas versões mostra que similaridade textual não é igual a compreensão real.

## 11. Validação recomendada

Para validar a versão clássica:

```powershell
venv\Scripts\python -m unittest discover -s mais_ou_menos -p "test*.py"
```

Para rodar exemplos preparados:

```powershell
venv\Scripts\python mais_ou_menos\testes_exemplos.py
```

Para validar a configuração da versão com IA:

```powershell
venv\Scripts\python topzera\main.py --check-config
```

Para testar manualmente a versão clássica:

```powershell
venv\Scripts\python mais_ou_menos\main.py --pergunta "O que é PLN?" --esperada "PLN é a área da computação que processa linguagem humana." --usuario "PLN analisa textos e linguagem humana." --detalhes
```

Para testar manualmente a versão com IA:

```powershell
venv\Scripts\python topzera\main.py --pergunta "O que é PLN?" --esperada "PLN é a área da computação que processa linguagem humana." --usuario "É uma área que ajuda computadores a analisar textos humanos."
```

## 12. Conclusão técnica

Fato: a versão `mais_ou_menos` é mais transparente, barata e reproduzível.

Fato: a versão `topzera` depende de API externa, credenciais, internet e possível custo por uso.

Inferência: a versão com IA tende a avaliar melhor paráfrases e respostas semanticamente corretas com palavras diferentes.

Opinião técnica: a melhor entrega é mostrar que a versão clássica cumpre a base do trabalho e que a versão com IA amplia a análise, mas exige cuidado operacional e validação humana.


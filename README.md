# Did It Understand?

Sistema em Python para avaliar se uma resposta do usuário está próxima de uma resposta esperada.

Hoje o projeto tem duas abordagens de avaliação e três formas práticas de uso:

- `mais_ou_menos`, motor clássico baseado em pré-processamento, TF-IDF, similaridade do cosseno e cobertura de palavras-chave.
- `topzera`, motor semântico com Azure OpenAI, voltado para paráfrases, nuances e leitura mais próxima de significado.
- `gui.py`, interface gráfica desktop que unifica os dois motores em uma única tela.

## Estado atual do projeto

As alterações mais relevantes já incorporadas no código e agora refletidas nesta documentação são:

- a adição da interface gráfica `gui.py`, que passou a ser o ponto de uso mais completo para demonstrações e avaliação manual;
- a manutenção das duas CLIs, o que preserva automação, depuração e execução reproduzível;
- a validação de configuração do Azure OpenAI sem consumir tokens, disponível tanto na CLI `topzera` quanto na GUI;
- o reaproveitamento dos exemplos de `mais_ou_menos/exemplos.json` dentro da interface gráfica;
- a consolidação da arquitetura em torno de dois motores reutilizáveis, sem duplicar regra de negócio na camada visual;
- a revisão da documentação interna e externa, com docstrings mais detalhadas e arquivos `.md` alinhados ao comportamento real das funções.

Impacto prático:

- a GUI reduz atrito operacional em apresentação, correção manual e testes exploratórios;
- as CLIs continuam sendo a melhor opção para validação repetível, comparação de cenários e automação;
- a separação entre motores e interface diminui custo de manutenção e reduz risco de divergência de regra entre telas e terminal.

## Objetivo

O trabalho responde à pergunta "a máquina entendeu?" de forma crítica.

Fato:

- a versão `mais_ou_menos` mede proximidade textual;
- a versão `topzera` pede para um modelo comparar o significado das respostas;
- a GUI não cria um terceiro algoritmo, ela apenas orquestra os dois motores existentes.

Inferência:

- a interface gráfica torna o projeto mais utilizável em ambiente real, porque reduz erro operacional e tempo de demonstração;
- a versão com IA tende a lidar melhor com paráfrases e sinônimos do que a abordagem puramente textual.

Opinião técnica:

- a melhor forma de apresentar o projeto é mostrar a GUI como camada de uso e, por trás dela, explicar os dois motores;
- isso é superior a documentar só a teoria, porque conecta implementação, usabilidade e trade-offs reais de operação.

## Como a documentação está organizada

O projeto agora separa a documentação em três níveis complementares:

- `README.md`, para onboarding rápido, execução e visão executiva;
- `documentation.md`, para arquitetura, decisões técnicas, trade-offs e fluxo operacional;
- `documentacao_funcoes_pln.md`, para leitura detalhada das funções, classes, variáveis principais e responsabilidades de cada camada.

Impacto prático:

- reduz tempo de entendimento para quem vai apresentar, manter ou evoluir o projeto;
- melhora rastreabilidade, porque a documentação externa agora conversa melhor com as docstrings do código;
- diminui risco de suporte, já que a lógica central dos motores ficou mais fácil de auditar.

## Estrutura real do repositório

```text
did-it-understand/
├── gui.py                          # Interface gráfica unificada em Tkinter
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
├── .env                            # Credenciais locais, não versionadas
├── .env.exemple                    # Exemplo de variáveis de ambiente
├── .gitignore
├── documentacao_funcoes_pln.md     # Guia detalhado das funções e da GUI
├── documentation.md                # Documentação técnica consolidada
├── GUIA_TRABALHO.md                # Guia do enunciado e da apresentação
├── LICENSE
├── README.md
└── requirements.txt
```

## Preparar ambiente

Se você ainda não trouxe o projeto para a sua máquina:

```powershell
git clone https://github.com/cidade-felipe/did-it-understand.git
cd did-it-understand
```

Se ainda não existir um ambiente virtual no projeto, crie com:

```powershell
python -m venv venv
```

Depois instale as dependências:

```powershell
venv\Scripts\python -m pip install -r requirements.txt
```

## Melhor forma de usar o projeto

Se o objetivo for apresentar, testar manualmente ou comparar os dois modos rapidamente, a melhor opção é a GUI:

```powershell
venv\Scripts\python gui.py
```

O que a GUI entrega:

- campos para pergunta, resposta esperada e resposta do usuário;
- troca entre `Mais ou Menos` e `Topzera` na mesma tela;
- carregamento de exemplos prontos para demonstração;
- painel de métricas e leitura técnica do resultado;
- verificação de credenciais do Azure OpenAI sem consumir tokens;
- execução em background para não travar a interface durante a avaliação.

Trade-off:

- a GUI é melhor para uso humano;
- as CLIs são melhores para automação, testes repetíveis e depuração fina.

## Executar a versão clássica por CLI

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

## Executar a versão com Azure OpenAI por CLI

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

## Configurar Azure OpenAI

Você pode usar o arquivo `.env.exemple` como base e criar um `.env` local na raiz.

Exemplo recomendado:

```env
AZURE_OPENAI_API_KEY=sua_chave
AZURE_OPENAI_ENDPOINT=https://seu-recurso.cognitiveservices.azure.com/
AZURE_OPENAI_DEPLOYMENT=nome_do_deployment
AZURE_OPENAI_API_VERSION=2024-12-01-preview
AZURE_OPENAI_TEMPERATURE=1
```

Observações importantes:

- o código aceita aliases como `OPENAI_API_KEY`, `AZURE_ENDPOINT`, `AZURE_DEPLOYMENT` e `OPENAI_MODEL`;
- o campo `model` enviado ao SDK precisa ser o nome do deployment no Azure, não necessariamente o nome comercial do modelo;
- se você colar uma URL com `/openai/...` e `api-version`, o código tenta normalizar essa URL para o endpoint base;
- `AZURE_OPENAI_TEMPERATURE` é opcional, porque alguns deployments rejeitam temperatura explícita.

## Como cada motor funciona

### `mais_ou_menos`

Fluxo resumido:

```text
pergunta
resposta esperada  -> pré-processamento -> TF-IDF -> similaridade do cosseno -> nota -> feedback
resposta usuário   -> pré-processamento -> palavras-chave --------------------^
```

A nota combina:

- `80%` da similaridade TF-IDF;
- `20%` da cobertura de palavras-chave.

Funções e variáveis que mais importam:

- `preprocessar_texto()` gera `tokens`, `tokens_comparacao` e `texto_processado`, que são a base da comparação;
- `calcular_similaridade_tfidf()` monta `documento_esperado`, `documento_usuario` e `matriz_tfidf` para medir proximidade lexical;
- `avaliar_resposta()` combina `similaridade` e `cobertura_palavras_chave` em `nota_base`, classifica o `feedback` e gera `observacoes`.

Classificação padrão:

- `70` ou mais: `Entendeu`;
- de `30` até `69,99`: `Parcial`;
- abaixo de `30`: `Não entendeu`.

### `topzera`

A saída mostra:

- `Feedback`;
- `Nota`;
- `Similaridade semântica`;
- `Justificativa`;
- `Pontos corretos`;
- `Lacunas`;
- `Alertas`.

Funções e variáveis que mais importam:

- `carregar_configuracao()` resolve `api_key`, `endpoint`, `deployment`, `api_version` e `temperatura`;
- `avaliar_resposta_com_ia()` monta o dicionário `parametros`, chama a API, extrai `conteudo` e converte a resposta em `dados`;
- `montar_resultado()` saneia `nota`, `similaridade_semantica`, `feedback` e listas explicativas para proteger a interface contra saídas inconsistentes.

Fato:

- o retorno é normalizado depois da resposta do modelo, o que reduz risco de JSON inconsistente quebrar a aplicação.

Inferência:

- isso melhora robustez operacional e reduz retrabalho durante demonstrações ou uso manual.

## Validação recomendada

Rode os testes automatizados da versão clássica:

```powershell
venv\Scripts\python -m unittest discover -s mais_ou_menos -p "test*.py"
```

Valide os módulos principais sem executar a GUI:

```powershell
venv\Scripts\python -m py_compile gui.py mais_ou_menos\avaliador.py mais_ou_menos\main.py mais_ou_menos\preprocessamento.py topzera\avaliador_openai.py topzera\main.py
```

Valide a configuração da IA:

```powershell
venv\Scripts\python topzera\main.py --check-config
```

Teste manualmente a GUI nos cenários abaixo:

- resposta correta com palavras parecidas;
- resposta correta com outras palavras;
- resposta incompleta;
- resposta errada com termos parecidos;
- resposta vazia no modo `Mais ou Menos`;
- falha de configuração no modo `Topzera`.

Fato:

- hoje os testes automatizados cobrem apenas o motor clássico.

Opinião técnica:

- isso é suficiente para proteger a base do trabalho, mas ainda existe espaço de melhoria em testes da GUI e em mocks para a integração com Azure OpenAI.

## Limites e trade-offs

Fato:

- TF-IDF compara palavras e distribuição de termos;
- Azure OpenAI oferece uma leitura mais semântica, mas depende de infraestrutura externa;
- a GUI melhora experiência de uso, mas não substitui validação técnica do motor.

Inferência:

- a versão clássica é mais barata, previsível e fácil de explicar;
- a versão com IA tende a ser melhor para paráfrases;
- a GUI reduz tempo de operação e risco de erro humano na condução da apresentação.

Opinião técnica:

- a combinação mais forte para defesa do trabalho é usar a GUI para mostrar o sistema e, em seguida, explicar os trade-offs dos dois motores;
- isso conecta fundamentos, experiência de uso e maturidade de engenharia em vez de apresentar só um script rodando.

# Repository Story

Ferramenta local que examina um repositório GitHub e ajuda a transformá-lo em uma apresentação para LinkedIn apoiada por referências a arquivos. Há uma interface web simples para preencher a URL, revisar a análise e copiar o texto. A API em Python e FastAPI continua acessível pelo Swagger. O projeto substitui a antiga API de classificação de incidentes; o nome do repositório remoto foi mantido.

## O que está implementado

A API valida URLs `https://github.com/owner/repository`, aceita `.git` e barra final, e permite escolher uma referência. Usa a branch padrão do GitHub quando ela não é informada. Resolve a referência para um SHA antes de coletar a árvore e lê blobs por SHA. Seleciona documentação, manifestos, entradas, serviços e testes; exclui caminhos sensíveis, dependências, builds, arquivos binários e lockfiles. Não clona nem executa o código analisado. Registra arquivos examinados, ignorados, árvore truncada e avisos de cobertura.

O Gemini recebe grupos de arquivos limitados, com instruções para tratar todo conteúdo do repositório como dado não confiável. A resposta JSON é validada por Pydantic. As afirmações são classificadas como observadas no código, declaradas na documentação, intenção em comentários ou inferência. O serviço aceita apenas referências a arquivos coletados e linhas válidas; trechos citados também precisam existir no conteúdo coletado. Essa validação não garante que toda interpretação do modelo seja correta. Commits recentes são apresentados separadamente, sem servir de prova isolada de funcionalidade.

A requisição ao Gemini usa saída JSON estruturada com o schema de análise ou de post. Falhas de chave, permissão, modelo, cota, timeout e formato de resposta são identificadas separadamente e exibidas na interface. Erros permanentes não são repetidos; falhas transitórias têm até três tentativas com espera progressiva limitada. Um `Retry-After` maior que o limite de espera local encerra a tentativa sem repetir cedo demais. Os logs registram apenas categoria e status HTTP, sem chave, prompt ou resposta completa.

A geração do post usa apenas afirmações observadas ou documentadas, aceita tom, tamanho, hashtags e contexto autoral opcional. Sem `confirmed_author=true`, o prompt proíbe afirmar que a pessoa desenvolveu o projeto. A resposta é rejeitada se ultrapassar o limite de caracteres ou omitir a URL. Não há publicação automática.

O frontend em `frontend/` usa HTML, CSS e JavaScript sem processo de build. O próprio FastAPI o serve na raiz `/`; as requisições do navegador usam caminhos relativos para a **API local**, na mesma origem. A interface mostra as evidências, a cobertura e os avisos, além de oferecer um botão para copiar o texto. Ela não envia dados diretamente ao GitHub, ao Gemini ou ao LinkedIn: o backend local faz as chamadas externas necessárias à análise e à geração.

## Requisitos e instalação

Python 3.10 ou superior. No bash:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[test]'
```

No fish, use `source .venv/bin/activate.fish`. As dependências e faixas de versão estão em `pyproject.toml`.

## Configuração

Copie `.env.example` para `.env` e configure as variáveis. Ao iniciar, a aplicação carrega automaticamente o arquivo `.env` da raiz do projeto. Os valores do arquivo têm prioridade sobre variáveis antigas definidas no processo. Você também pode configurá-las diretamente no bash se não usar o arquivo:

```bash
export GEMINI_API_KEY='sua-chave'
export GEMINI_MODEL='gemini-3.5-flash-lite'
export GITHUB_TOKEN='seu-token-opcional'
```

No fish, use `set -x GEMINI_API_KEY sua-chave`, e o mesmo formato para as outras variáveis, caso prefira configurá-las no shell. O modelo é configurável; confira a disponibilidade na sua conta. `GITHUB_TOKEN` é opcional para repositórios públicos e necessário para privados autorizados, com permissão de leitura de conteúdo. `.env` está ignorado pelo Git e não é enviado ao repositório. Não compartilhe tokens em exemplos ou logs.

| Variável | Padrão | Unidade / função |
| --- | ---: | --- |
| `MAX_FILES` | 24 | arquivos selecionados |
| `MAX_FILE_BYTES` | 30000 | bytes por arquivo |
| `MAX_TOTAL_BYTES` | 150000 | bytes coletados |
| `MAX_COMMITS` | 10 | commits recentes |
| `MAX_CONTEXT_CHARS` | 24000 | caracteres por grupo enviado ao LLM |

Esses limites têm máximos impostos pelo servidor: 100 arquivos, 100000 bytes por arquivo, 500000 bytes totais, 30 commits e 100000 caracteres por grupo. O cliente da API não pode aumentá-los. Cada grupo e a geração do post podem consumir uma chamada paga do provedor. A seleção não implica leitura integral do projeto.

## Executar

```bash
uvicorn app.main:app --reload
```

Abra `http://127.0.0.1:8000/` para usar a interface. O Swagger permanece em `http://127.0.0.1:8000/docs`. `GET /health` retorna `{"status":"ok"}` sem consultar serviços externos. Mantenha o backend em execução enquanto usa o frontend; não há servidor de frontend separado nem hospedagem publicada nesta etapa.

## Endpoints

`POST /api/v1/repositories/analyze` recebe URL, `reference` opcional e `allow_private_llm`. Exemplo:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/repositories/analyze \
  -H 'Content-Type: application/json' \
  -d '{"url":"https://github.com/octocat/Hello-World"}'
```

A resposta contém `repository`, `reference`, `commit`, `description`, `purpose`, `claims` (texto, tipo, categoria, caminho, linha, trecho e SHA), `uncertainties`, `commits`, `coverage` e `warnings`. Exemplo reduzido de formato: `{"repository":"https://github.com/octocat/Hello-World","commit":"<sha>","claims":[],"coverage":{"examined":[],"ignored":[],"tree_truncated":false},"warnings":[]}`. Os valores reais dependem do repositório e do modelo.

`POST /api/v1/posts/linkedin` aceita os mesmos campos e `tone` (`profissional` ou `conversacional`), `length` (`curto` ou `medio`), `hashtags`, `author_context`, `confirmed_author` e `max_characters` (300 a 3000; padrão 2200). Exemplo:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/posts/linkedin \
  -H 'Content-Type: application/json' \
  -d '{"url":"https://github.com/octocat/Hello-World","tone":"profissional","confirmed_author":false}'
```

A resposta inclui `post`, `characters`, `evidence_summary`, `limitations` e a `analysis` utilizada. Erros de entrada usam HTTP 422; falta de permissão, referência ausente, limite do GitHub e falha do LLM recebem mensagens sem tokens.

## Repositórios privados e segurança

Para analisar um repositório privado, configure um token GitHub com acesso de leitura e envie `"allow_private_llm":true` em cada solicitação. Isso autoriza o envio dos trechos selecionados ao Gemini. Sem essa opção, a API interrompe o fluxo antes do envio ao LLM. O cliente GitHub é o único componente que recebe o token. A API usa apenas `api.github.com` e não segue redirecionamentos. Arquivos `.env`, chaves privadas e caminhos conhecidos são excluídos; padrões conhecidos de segredos são redigidos antes do envio ao LLM. A detecção é limitada: revise o conteúdo e as políticas do provedor antes de usar dados sensíveis.

README, código, comentários e mensagens de commit são dados não confiáveis. O modelo não recebe ferramentas de execução. O conteúdo é delimitado no prompt, mas ataques de prompt injection ainda podem afetar a redação; revise o texto antes de publicar.

## Estrutura e testes

`app/repository_tool.py` contém validação de URL, coleta GitHub, seleção, redação, modelos de análise, cliente Gemini e serviço de orquestração. `app/main.py` define contratos e rotas FastAPI e serve o frontend. `frontend/` contém a interface estática. `tests/test_repository_flow.py` cobre URLs, seleção, redação, fluxo HTTP com GitHub e LLM simulados e entrega dos arquivos da interface.

```bash
python -m pytest -q
```

Os testes padrão não usam rede nem credenciais. Eles verificam contrato, tratamento de erros e fluxo, não a qualidade factual de um LLM real. Para validar o fluxo com um repositório, configure `GEMINI_API_KEY` e `GEMINI_MODEL`, inicie a API e use os exemplos acima com um repositório público pequeno. Essa chamada consome cota do GitHub e possivelmente custo do Gemini. Foi validada uma geração real mínima do schema `Findings` com o modelo configurado no `.env`; a análise completa de um repositório e o schema `PostOutput` foram verificados somente com mocks.

Para conferir a sintaxe do JavaScript, use `node --check frontend/app.js` se tiver Node.js instalado. A interface não precisa de Node.js para funcionar.

## Limitações

A árvore recursiva do GitHub pode ser truncada; a resposta sinaliza isso e não percorre subárvores adicionais. A seleção é heurística e pode deixar código relevante de fora. Não há cache nem paginação além do limite de uma página de commits recentes. Um 404 do GitHub pode representar repositório inexistente ou privado sem permissão. A redação de segredos é baseada em padrões e não é completa. A saída do modelo é validada estruturalmente e por referências simples, mas suas interpretações exigem revisão humana. A análise não executa testes do repositório observado nem comprova uso em produção.

Documentação consultada: [árvores GitHub](https://docs.github.com/en/rest/git/trees), [referências GitHub](https://docs.github.com/en/rest/git/refs), [Gemini generateContent](https://ai.google.dev/api/generate-content), [saídas estruturadas](https://ai.google.dev/gemini-api/docs/structured-output) e [modelos disponíveis](https://ai.google.dev/gemini-api/docs/models).

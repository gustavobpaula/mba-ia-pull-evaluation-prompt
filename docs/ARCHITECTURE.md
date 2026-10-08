# Architecture

## Context and Drivers
Projeto de desafio com escopo fixo: um pipeline de linha de comando (pull → edição do prompt em YAML → push → avaliação) sobre o LangSmith. Os drivers vêm de `docs/SPEC.md`: FR-1 (pull), FR-2/FR-3 (prompt v2 com técnicas), FR-4 (push com metadados), FR-5 (avaliação ≥ 0.8), FR-6 (testes do prompt) e as restrições "não alterar `evaluate.py`, `metrics.py`, `utils.py` e o dataset", "variável `{bug_report}`" e "estrutura de projeto exigida". A arquitetura deve ser mínima: a parte que muda ao longo do projeto é o conteúdo do prompt, não o código.

## Technology Baseline
| Concern | Decision | Role | Rationale / Constraint |
|---|---|---|---|
| Linguagem | Python 3.10+ | Scripts e testes | Exigido pelo desafio |
| Prompts | `langchain-core` (`ChatPromptTemplate`) | Representação do prompt enviado e lido do Hub | Exigido; `evaluate.py` consome `ChatPromptTemplate` |
| Plataforma | `langsmith` (`Client`) | Pull, push, dataset, experimentos e tracing | Exigido; fonte única do prompt avaliado |
| LLM | OpenAI via `langchain-openai`, selecionado por `LLM_PROVIDER=openai` | Geração e avaliação | Decisão do engenheiro (AD-6) |
| Configuração | `python-dotenv` + `.env` | Credenciais, handle, provider e modelos | `.env` fora do versionamento |
| Formato de prompt | YAML via `pyyaml` (`load_yaml`/`save_yaml` de `utils.py`) | Fonte editável do prompt | Exigido pelo desafio |
| Testes | `pytest` | Contrato do arquivo de prompt | Exigido por FR-6 |

## Architectural Style and Boundaries
Scripts independentes, um por etapa do pipeline, executados como `python src/<script>.py`. Não há camadas nem pacotes internos. Há três fronteiras:
- **Local (prompts YAML)**: onde o prompt é escrito e revisado.
- **LangSmith Hub**: onde fica o prompt publicado, que é o que a avaliação consome.
- **Provedor de LLM**: acessado apenas por `utils.get_llm` e `utils.get_eval_llm`.

```
prompts/*_v1.yml ◀── pull ── Hub ◀── push ── prompts/*_v2.yml
                                │
                           evaluate.py ──▶ experimento no LangSmith
```

## Directory Organization
| Pattern | Responsibility | Allowed dependencies | Forbidden |
|---|---|---|---|
| `src/<etapa>_prompts.py` | Um script de CLI por etapa (pull, push), com `main()` retornando o código de saída | `utils`, `langsmith`, `langchain_core`, `dotenv` | Importar outro script de etapa ou `evaluate`; acessar o LLM diretamente |
| `src/evaluate.py`, `src/metrics.py`, `src/utils.py` | Avaliação e helpers fornecidos (congelados) | — | Qualquer alteração |
| `prompts/<prompt_name>_v<N>.yml` | Dados do prompt (um prompt por arquivo) | — | Código, segredos |
| `datasets/` | Dataset de avaliação (congelado) | — | Alteração |
| `tests/` | Testes pytest offline | `utils`, funções dos scripts de etapa, leitura de `prompts/` | Rede, LangSmith, LLM (integrações substituídas por dublês) |

## Dependency Rules
- Scripts de `src/` importam helpers por import plano (`from utils import ...`), coerente com a execução `python src/<script>.py`.
- Lógica compartilhada nova não entra em `utils.py`, que é congelado. Ela fica no script que a usa até haver um segundo consumidor real (DD-1).
- Testes importam `utils` e os scripts de etapa adicionando `src/` ao `sys.path`, como em `tests/test_prompts.py`.

## State and Data Ownership
- `prompts/bug_to_user_story_v2.yml` é **escrito à mão** e é a fonte do prompt otimizado.
- `prompts/bug_to_user_story_v1.yml` é um **snapshot gerado pelo pull**. Pode ser sobrescrito e não deve ser editado à mão.
- O **Hub** guarda a versão publicada. `evaluate.py` lê só do Hub, então toda edição do v2 exige push antes da avaliação.
- O dataset `{LANGSMITH_PROJECT}-eval` é criado a partir do `.jsonl` e depois reutilizado. Experimentos e feedbacks ficam no LangSmith.

## External Integrations
- **LangSmith**: um `Client()` por execução, configurado pelo `.env`. O pull de `owner/nome` usa `dangerously_pull_public_prompt=True`. O push usa `is_public=True` e o identificador `{USERNAME_LANGSMITH_HUB}/<prompt_name>_v<N>`.
- **OpenAI**: só por `get_llm`/`get_eval_llm`. `LLM_MODEL` e `EVAL_MODEL` recebem o mesmo modelo, que deve aceitar `temperature=0`.
- Falha de integração (credencial, prompt inexistente, handle inválido) gera mensagem explícita e código de saída diferente de zero. Nada é publicado parcialmente.

## Domain Rules
- **Schema do YAML** (AD-2): uma única chave de topo igual ao nome do arquivo sem extensão, contendo `description`, `system_prompt`, `user_prompt`, `version`, `tags` e `techniques_applied`. `created_at` é opcional. Em um snapshot gerado pelo pull, `description` e `tags` só aparecem se existirem no Hub, e `techniques_applied` não se aplica, pois é exclusivo dos prompts otimizados.
- **Mapeamento YAML ↔ Hub** (AD-3): `system_prompt` ↔ mensagem `system` e `user_prompt` ↔ mensagem `human`, nessa ordem e sem outras mensagens.
- **Variáveis** (AD-4): o template usa o formato f-string, e `{bug_report}` é a única variável, presente apenas no `user_prompt`. Chaves literais nos exemplos são escapadas como `{{ }}`.
- **Few-shot** (AD-5): os exemplos ficam dentro do `system_prompt`, como texto delimitado.
- O push valida o arquivo com `validate_prompt_structure` e com as regras de variável acima antes de qualquer chamada ao Hub.
- `description`, `tags` e `techniques_applied` vão como metadados do push. Os metadados do Hub vêm somente do YAML.

## Naming Conventions
- Arquivos, módulos, funções e variáveis Python em `snake_case`. Constantes e variáveis de ambiente em `SCREAMING_SNAKE_CASE`.
- Testes em `tests/test_<assunto>.py` com funções `test_<comportamento>`.
- Prompts como `<prompt_name>_v<N>.yml` localmente e `<handle>/<prompt_name>_v<N>` no Hub.
- Tags em `kebab-case`. Técnicas com rótulos estáveis, como `Few-shot Learning`, `Role Prompting` e `Chain of Thought`.

## Feature Extension Rules
**Every new feature must** respeitar o schema do YAML e o mapeamento AD-3, ler a configuração somente do `.env`, terminar com código de saída diferente de zero em caso de falha e manter os testes pytest offline.

**A feature may** adicionar funções privadas ao seu próprio script e acrescentar testes em `tests/`.

**A feature must not** alterar arquivos congelados, criar novas camadas ou pacotes, instanciar LLMs fora de `utils` nem colocar segredos em prompts publicados.

## Testing Strategy
- **pytest (offline, determinístico)**: verifica o contrato de `prompts/bug_to_user_story_v2.yml` (FR-6, AC-2, AC-3). Testes de conversão YAML ↔ `ChatPromptTemplate` podem montar o template localmente, sem rede.
- **Execução manual dos scripts**: valida pull e push contra o LangSmith real (AC-1, AC-4, AC-5).
- **`evaluate.py`**: é o critério de aceite de qualidade do prompt (AC-6).

## Decisions and Trade-offs
- **AD-1**: Scripts planos por etapa, sem camadas. É suficiente para o escopo fixo e segue os esqueletos; o custo é alguma duplicação pequena entre pull e push.
- **AD-2**: Schema do v2 igual ao do v1, mais `techniques_applied`. Mantém compatibilidade com `validate_prompt_structure` e com o snapshot do pull (`docs/SPEC.md` Assumptions).
- **AD-3**: Duas mensagens fixas (system e human). É simples de converter nos dois sentidos, mas não usa mensagens de exemplo nativas.
- **AD-4**: Só a variável `{bug_report}`, no user prompt. Corrige a duplicação do v1 e casa com a chave do dataset; exige escapar chaves literais.
- **AD-5**: Few-shot embutido no `system_prompt`. Um único campo, fácil de testar (FR-6); o custo é um system prompt mais longo.
- **AD-6**: OpenAI, com o mesmo modelo para resposta e avaliação. É mais simples e barato e evita os limites do plano gratuito do Gemini; o juiz pode ser menos rigoroso. Nomes de modelo ficam só no `.env`.
- **AD-7**: YAML como fonte de escrita e Hub como fonte de avaliação. Segue o `evaluate.py` congelado e obriga a fazer push antes de cada avaliação.

## Deferred Decisions
- **DD-1**: Módulo compartilhado de conversão YAML ↔ template. Gatilho: um terceiro consumidor ou divergência entre a conversão do pull e a do push.
- **DD-2**: `EVAL_MODEL` mais capaz que `LLM_MODEL`. Gatilho: notas instáveis entre rodadas idênticas ou suspeita de juiz pouco rigoroso.
- **DD-3**: Few-shot como mensagens nativas (`FewShotChatMessagePromptTemplate` ou pares human/ai). Gatilho: a avaliação estagnar abaixo de 0.8 por causa da forma dos exemplos.

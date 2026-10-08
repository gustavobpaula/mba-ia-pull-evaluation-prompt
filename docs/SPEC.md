# Specification

## Goal
Entregar um software em Python que faz pull de um prompt de baixa qualidade do LangSmith Prompt Hub, permite otimizá-lo com técnicas de Prompt Engineering em YAML, publica a versão otimizada (v2) no Hub e a avalia até que as cinco métricas (Helpfulness, Correctness, F1-Score, Clarity, Precision) atinjam no mínimo 0.8, com o processo documentado no README e evidências públicas no LangSmith.

## Functional Requirements
- FR-1: `src/pull_prompts.py` conecta ao LangSmith com as credenciais do `.env`, faz pull de `leonanluppi/bug_to_user_story_v1` e salva o prompt em `prompts/bug_to_user_story_v1.yml`.
- FR-2: `prompts/bug_to_user_story_v2.yml` contém um prompt otimizado com system prompt e user prompt separados, instruções claras e específicas, regras explícitas de comportamento, exemplos de entrada/saída (few-shot) e tratamento de edge cases.
- FR-3: O prompt v2 aplica obrigatoriamente Few-shot Learning e pelo menos uma técnica entre Chain of Thought, Tree of Thought, Skeleton of Thought, ReAct e Role Prompting, listadas nos metadados do YAML.
- FR-4: `src/push_prompts.py` lê e valida o v2 e faz push público para `{USERNAME_LANGSMITH_HUB}/bug_to_user_story_v2` com descrição, tags e técnicas utilizadas.
- FR-5: A execução de `src/evaluate.py` sobre o v2 publicado gera um experimento no LangSmith com todas as cinco métricas ≥ 0.8 e média ≥ 0.8.
- FR-6: `tests/test_prompts.py` implementa com pytest, no mínimo: `test_prompt_has_system_prompt`, `test_prompt_has_role_definition`, `test_prompt_mentions_format`, `test_prompt_has_few_shot_examples`, `test_prompt_no_todos`, `test_minimum_techniques`.
- FR-7: O README contém as seções "Técnicas Aplicadas (Fase 2)", "Resultados Finais" e "Como Executar" com o conteúdo exigido pelo desafio.
- FR-8: Existem evidências públicas no LangSmith: dataset de avaliação com 15 exemplos, execuções do v2 com notas ≥ 0.8 e tracing detalhado de pelo menos 3 exemplos.

## Acceptance Criteria
- AC-1 [FR-1]: Com `.env` válido, `python src/pull_prompts.py` cria ou sobrescreve `prompts/bug_to_user_story_v1.yml` com o conteúdo do system prompt e do user prompt do Hub.
- AC-2 [FR-2]: O v2 contém `description`, `system_prompt`, `user_prompt`, `version`, `tags` e `techniques_applied`; a variável `{bug_report}` aparece no user prompt e não é duplicada no system prompt.
- AC-3 [FR-2, FR-3]: `validate_prompt_structure` (de `src/utils.py`) retorna válido para os dados do v2, com ao menos 2 técnicas em `techniques_applied`, incluindo Few-shot.
- AC-4 [FR-4]: Após `python src/push_prompts.py`, o prompt `{handle}/bug_to_user_story_v2` aparece público no Hub com descrição, tags e técnicas.
- AC-5 [FR-4]: Se a validação do v2 falhar, nenhum push é feito e os erros são exibidos.
- AC-6 [FR-5]: `python src/evaluate.py` exibe "STATUS: APROVADO" para o v2 e imprime o link do experimento.
- AC-7 [FR-6]: `pytest tests/test_prompts.py` passa os 6 testes contra o v2, e cada teste falha se a propriedade verificada for removida do arquivo.
- AC-8 [FR-7]: O README apresenta técnicas com justificativa e exemplos, link público do dataset, screenshots com notas ≥ 0.8, comparação v1 × v2, pré-requisitos e comandos de cada fase.
- AC-9 [FR-8]: O link gerado por `Client().share_dataset(...)` abre sem login e mostra os 15 exemplos e os experimentos do v2.

## Constraints
- Python 3.10+, LangChain (`langchain-core`), LangSmith (Prompt Hub, datasets, avaliação) e prompts em YAML, conforme `requirements.txt`.
- Não alterar `src/evaluate.py`, `src/metrics.py`, `src/utils.py` nem `datasets/bug_to_user_story.jsonl`.
- Manter a estrutura de projeto exigida pelo desafio.
- A variável do template deve ser `{bug_report}`, chave de entrada do dataset.
- Provider via `LLM_PROVIDER` (`openai` ou `google`), modelos via `LLM_MODEL` e `EVAL_MODEL`, compatíveis com `temperature=0`.
- O dataset de avaliação se chama `{LANGSMITH_PROJECT}-eval`.
- O pull de prompt `owner/nome` exige `dangerously_pull_public_prompt=True`.
- O handle do Hub precisa existir antes do push.

## Assumptions
- O v2 segue o formato do v1: chave de topo com o nome do prompt (`bug_to_user_story_v2`) e campos aninhados.
- Os testes de FR-6 validam o arquivo v2.

## Edge Cases
- Variáveis obrigatórias ausentes no `.env`: pull e push informam quais faltam e encerram com falha.
- Prompt inexistente no Hub ou handle inválido: o script informa o erro e encerra com falha.
- Avaliação com qualquer métrica < 0.8 resulta em REPROVADO, mesmo com média ≥ 0.8.
- Limites de requisição do plano gratuito do Gemini podem interromper a avaliação.

## Out of Scope
- Alterar o dataset ou os scripts fornecidos prontos (`evaluate.py`, `metrics.py`, `utils.py`).

## Open Questions
- O README final substitui o enunciado do desafio ou acrescenta as seções exigidas a ele?

## Feature Specifications
- [Pull do prompt semente](specs/pull-prompts.md)
- [Prompt otimizado v2 e testes de validação](specs/prompt-v2.md)
- [Push do prompt otimizado v2](specs/push-prompts.md)

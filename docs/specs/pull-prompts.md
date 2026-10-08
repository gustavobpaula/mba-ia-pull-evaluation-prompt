# Feature Specification: Pull do prompt semente

## Goal
Detalhar `docs/SPEC.md` FR-1: o script `src/pull_prompts.py` baixa o prompt semente do LangSmith Prompt Hub e grava um snapshot local em YAML, no schema definido em `docs/ARCHITECTURE.md` (AD-2, AD-3), refletindo apenas o que está publicado no Hub.

## Functional Requirements
- FR-1: Antes de conectar, o script verifica se `LANGSMITH_API_KEY` está configurada no `.env`.
- FR-2: O script faz pull de `leonanluppi/bug_to_user_story_v1` com `dangerously_pull_public_prompt=True`.
- FR-3: A mensagem `system` do prompt vira `system_prompt` e a mensagem `human` vira `user_prompt`, com o texto preservado sem alterações.
- FR-4: `description` e `tags` vêm dos metadados do Hub quando existirem; `version` é derivada do sufixo do nome (`v1`); campos sem valor no Hub são omitidos.
- FR-5: O resultado é gravado em `prompts/bug_to_user_story_v1.yml` sob uma única chave de topo `bug_to_user_story_v1`, sobrescrevendo o arquivo existente.
- FR-6: O script só grava se o prompt tiver exatamente uma mensagem `system` e uma `human`.
- FR-7: O script termina com código 0 em caso de sucesso e com código diferente de zero em qualquer falha, sempre com uma mensagem explicativa.

## Acceptance Criteria
- AC-1 [FR-2, FR-3, FR-5, FR-7]: Com `.env` válido, `python src/pull_prompts.py` termina com código 0, e `load_yaml` do arquivo retorna um dicionário com a única chave `bug_to_user_story_v1`, cujos `system_prompt` e `user_prompt` são idênticos aos textos das mensagens no Hub.
- AC-2 [FR-3]: Placeholders como `{bug_report}` aparecem no YAML exatamente como no Hub.
- AC-3 [FR-4]: `version` é `"v1"`; `description` e `tags` aparecem se, e somente se, existirem no Hub.
- AC-4 [FR-1, FR-7]: Sem `LANGSMITH_API_KEY`, o script informa a variável ausente, não chama o Hub, termina com código diferente de zero e deixa o arquivo local inalterado.
- AC-5 [FR-6, FR-7]: Se o prompt tiver estrutura diferente de uma mensagem `system` e uma `human`, o script informa os tipos de mensagem encontrados, termina com código diferente de zero e deixa o arquivo local inalterado.
- AC-6 [FR-7]: Em erro do Hub (prompt inexistente, credencial inválida ou falha de rede), o script exibe o erro, termina com código diferente de zero e deixa o arquivo local inalterado.

## Constraints
- Gravação via `save_yaml` de `src/utils.py`; `src/utils.py` não pode ser alterado (`docs/SPEC.md` Constraints).
- O snapshot v1 não é editado à mão (`docs/ARCHITECTURE.md`, State and Data Ownership).

## Assumptions
- O prompt semente no Hub é um `ChatPromptTemplate` com uma mensagem `system` e uma `human`, como sugere o arquivo v1 atual.

## Edge Cases
- Arquivo v1 já existente: é sobrescrito, e os comentários do arquivo atual se perdem.
- Diretório `prompts/` ausente: é criado na gravação.

## Out of Scope
- Nenhum item explícito.

## Open Questions
- Nenhuma.

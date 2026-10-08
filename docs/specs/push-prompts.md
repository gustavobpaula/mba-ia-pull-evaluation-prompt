# Feature Specification: Push do prompt otimizado v2

## Goal
Detalhar `docs/SPEC.md` FR-4: o script `src/push_prompts.py` lê e valida `prompts/bug_to_user_story_v2.yml` e o publica, público, no LangSmith Prompt Hub como `{USERNAME_LANGSMITH_HUB}/bug_to_user_story_v2`, com metadados vindos somente do YAML, para que `src/evaluate.py` possa avaliá-lo.

## Functional Requirements
- FR-1: Antes de qualquer chamada ao Hub, o script verifica se `LANGSMITH_API_KEY` e `USERNAME_LANGSMITH_HUB` estão configuradas no `.env`.
- FR-2: O script lê a chave `bug_to_user_story_v2` de `prompts/bug_to_user_story_v2.yml`.
- FR-3: Antes de qualquer chamada ao Hub, o script valida o prompt com `validate_prompt_structure` e com as regras de `docs/ARCHITECTURE.md` AD-4: `user_prompt` presente, `{bug_report}` como única variável do template e ausente do `system_prompt`. Todos os erros encontrados são listados.
- FR-4: O template publicado tem duas mensagens, `system` com o `system_prompt` seguida de `human` com o `user_prompt` (AD-3).
- FR-5: O push usa `is_public=True` e envia como metadados:
  - `description`: a do YAML;
  - `tags`: as tags do YAML mais cada técnica de `techniques_applied` em `kebab-case`, sem duplicatas;
  - `readme`: um texto curto que lista as técnicas com os rótulos originais.
- FR-6: Se o template não mudou desde o último push, os metadados são atualizados mesmo assim, o script avisa que o template já está publicado e termina com sucesso.
- FR-7: Em caso de sucesso, o script exibe a URL do prompt e termina com código 0. Em qualquer falha, exibe uma mensagem explicativa e termina com código diferente de zero.

## Acceptance Criteria
- AC-1 [FR-2, FR-4, FR-5, FR-7]: Com `.env` válido, `python src/push_prompts.py` termina com código 0 e exibe a URL. `client.pull_prompt("{handle}/bug_to_user_story_v2")` retorna as mensagens `system` e `human` com textos idênticos aos do YAML.
- AC-2 [FR-5]: No Hub, o prompt é público, tem a `description` do YAML, as tags do YAML mais `few-shot-learning`, `role-prompting` e `skeleton-of-thought`, e um README que lista as 3 técnicas.
- AC-3 [FR-1, FR-7]: Se faltar qualquer uma das duas variáveis, o script informa quais faltam, não chama o Hub e termina com código diferente de zero.
- AC-4 [FR-3, FR-7]: Com um v2 inválido (por exemplo, sem `system_prompt`, com menos de 2 técnicas, com `{bug_report}` no `system_prompt` ou com uma variável extra), o script lista os erros, não chama o Hub e termina com código diferente de zero.
- AC-5 [FR-6]: Ao rodar o push duas vezes seguidas sem alterar o v2, a segunda execução termina com código 0 e avisa que o template já está publicado.
- AC-6 [FR-7]: Em erro do Hub (credencial inválida, handle inexistente ou falha de rede), o script exibe o erro e termina com código diferente de zero.

## Constraints
- Leitura com `load_yaml` e validação com `validate_prompt_structure`, ambas de `src/utils.py`, que não pode ser alterado (`docs/SPEC.md` Constraints).
- Os metadados publicados vêm somente do YAML (`docs/ARCHITECTURE.md`, Domain Rules).
- O handle do Hub precisa existir antes do push (`docs/SPEC.md` Constraints).

## Assumptions
- O Hub recusa um commit com template idêntico ao último publicado com um erro de conflito, e é por esse erro que o script detecta a situação de FR-6.
- Para converter técnicas em `kebab-case`, as letras viram minúsculas e os espaços viram hífen (por exemplo, "Few-shot Learning" vira `few-shot-learning`).

## Edge Cases
- Arquivo v2 ausente ou com YAML inválido: o script informa o erro, não chama o Hub e termina com falha.
- Falha no commit depois que os metadados já foram criados ou atualizados: o script termina com falha, e uma nova execução completa a publicação.

## Out of Scope
- Publicar o v1 ou outros prompts.
- A avaliação (entrega 4) e a documentação no README do projeto (entrega 5), conforme a sequência de entregas acordada.

## Open Questions
- Nenhuma.

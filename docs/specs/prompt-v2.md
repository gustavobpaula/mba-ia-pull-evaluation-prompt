# Feature Specification: Prompt otimizado v2 e testes de validação

## Goal
Detalhar `docs/SPEC.md` FR-2, FR-3 e FR-6: criar `prompts/bug_to_user_story_v2.yml`, que converte relatos de bugs em user stories no estilo do dataset de avaliação aplicando Few-shot Learning, Role Prompting e Skeleton of Thought, e implementar em `tests/test_prompts.py` os testes que garantem esse contrato.

## Functional Requirements
- FR-1: O arquivo segue o schema de `docs/ARCHITECTURE.md` (AD-2) com chave `bug_to_user_story_v2`, `version: "v2"`, `description`, `tags` e `techniques_applied` igual a `Few-shot Learning`, `Role Prompting` e `Skeleton of Thought`.
- FR-2 (Role Prompting): O `system_prompt` define a persona de um Product Manager experiente em transformar relatos de bugs em user stories.
- FR-3 (Skeleton of Thought): O `system_prompt` define a estrutura da resposta em etapas, alinhada aos formatos do dataset:
  - relato com um único problema, mesmo que tenha vários sintomas, passos ou detalhes: "Como um <persona>, eu quero <ação>, para que <benefício>", seguido de "Critérios de Aceitação" em Dado/Quando/Então e, quando o relato trouxer detalhes técnicos, uma seção de contexto;
  - relato que descreve explicitamente mais de um problema distinto (por exemplo, uma lista de problemas numerados): formato estendido com uma user story principal e critérios agrupados por problema.
- FR-4 (Few-shot): O `system_prompt` contém pelo menos 2 exemplos originais de entrada (relato) e saída (user story), cobrindo um relato com um único problema e um com vários; nenhum exemplo é copiado do dataset de avaliação.
- FR-5: O `system_prompt` contém regras explícitas: responder em português do Brasil, devolver apenas a user story (sem preâmbulo nem explicações) e nunca contradizer o relato, completando-o com critérios de comportamento esperado mensuráveis, valores derivados dos dados do relato (por exemplo, totais calculados) e sugestões técnicas usuais para o problema.
- FR-6: O `system_prompt` instrui o tratamento destes edge cases:
  - relato vago ou curto: gera a user story no formato de um único problema, completando com comportamento esperado mensurável sem contradizer o relato;
  - vários problemas distintos: aplica o formato estendido;
  - dados técnicos citados (IDs, valores, mensagens de erro, endpoints): preservados nos critérios ou no contexto;
  - entrada que não descreve um bug: convertida mesmo assim em user story, sem recusa.
- FR-7: `tests/test_prompts.py` implementa os 6 testes de `docs/SPEC.md` FR-6 sobre o arquivo v2.

## Acceptance Criteria
- AC-1 [FR-1]: `load_yaml` do v2 retorna a única chave `bug_to_user_story_v2` com `version == "v2"` e as 3 técnicas em `techniques_applied`, e `validate_prompt_structure` o considera válido.
- AC-2 [FR-2]: O `system_prompt` contém "Você é" definindo a persona de Product Manager.
- AC-3 [FR-3]: O `system_prompt` descreve os dois formatos de saída, incluindo "Como um", "eu quero", "para que", "Critérios de Aceitação" e Dado/Quando/Então.
- AC-4 [FR-4]: O `system_prompt` contém pelo menos 2 pares de exemplo identificados como entrada e saída, e nenhum relato de exemplo é igual a um `bug_report` de `datasets/bug_to_user_story.jsonl`.
- AC-5 [FR-5, FR-6]: O `system_prompt` contém uma regra explícita para cada item de FR-5 e para cada edge case de FR-6.
- AC-6 [FR-1]: `ChatPromptTemplate.from_messages([("system", system_prompt), ("human", user_prompt)]).input_variables == ["bug_report"]`.
- AC-7 [FR-7]: `pytest tests/test_prompts.py` passa os 6 testes, e cada teste falha quando a propriedade que verifica é removida do v2:
  - system prompt vazio;
  - sem persona;
  - sem menção ao formato User Story;
  - sem exemplos;
  - com `[TODO]` em qualquer campo de texto;
  - menos de 2 técnicas.

## Constraints
- Regras de `docs/ARCHITECTURE.md`: few-shot embutido no `system_prompt` (AD-5); `{bug_report}` apenas no `user_prompt`, com chaves literais escapadas (AD-4); duas mensagens, system seguida de human (AD-3).
- Os testes rodam offline, sem LangSmith nem LLM (`docs/ARCHITECTURE.md`, Testing Strategy).
- O dataset não pode ser alterado (`docs/SPEC.md` Constraints).

## Assumptions
- Os marcadores textuais verificados pelos testes ("Você é", "User Story", identificação de entrada/saída nos exemplos) são os definidos nos AC-2 a AC-4.

## Edge Cases
- Se o arquivo v2 estiver ausente ou com YAML inválido, os testes falham em vez de serem pulados.

## Out of Scope
- Push do v2 ao Hub (entrega 3), atingir as notas ≥ 0.8 (entrega 4) e documentar as técnicas no README (entrega 5), conforme a sequência de entregas acordada.

## Open Questions
- Nenhuma.

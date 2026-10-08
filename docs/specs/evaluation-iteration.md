# Feature Specification: Avaliação e iteração do prompt v2

## Goal
Detalhar `docs/SPEC.md` FR-5: iterar `prompts/bug_to_user_story_v2.yml` em rodadas de avaliação com `src/evaluate.py` até que as cinco métricas e a média atinjam 0.8, dentro de um limite de rodadas, registrando cada rodada para a documentação final.

## Functional Requirements
- FR-1: Cada rodada segue, em ordem: editar o v2 → `pytest` passando → `python src/push_prompts.py` → `python src/evaluate.py`.
- FR-2: Cada rodada é registrada em `docs/evaluation-log.md` com número, resumo das mudanças no prompt, as 5 notas, a média, o status e o link do experimento no LangSmith.
- FR-3: A entrega tem no máximo 5 rodadas, contando a rodada 1 já executada (média 0.4778, reprovada).
- FR-4: Assim que uma rodada for aprovada, a iteração para.
- FR-5: Se a rodada 5 não for aprovada, a iteração para e o engenheiro recebe o diagnóstico e as opções (por exemplo, `docs/ARCHITECTURE.md` DD-2 ou DD-3) antes de qualquer nova mudança.
- FR-6: Entre rodadas, mudam apenas o v2, os testes que dependem do texto dele e o registro. Os modelos do `.env` não mudam sem decisão do engenheiro.

## Acceptance Criteria
- AC-1 [FR-1, FR-4]: Em alguma rodada ≤ 5, `src/evaluate.py` exibe "STATUS: APROVADO" para o v2 publicado, cumprindo `docs/SPEC.md` AC-6.
- AC-2 [FR-1]: Antes de cada avaliação, `pytest` passa e o push publica um template novo (termina com código 0, sem o aviso de "sem alterações").
- AC-3 [FR-2]: `docs/evaluation-log.md` tem uma linha por rodada executada, com todos os campos de FR-2.
- AC-4 [FR-3, FR-5]: Nenhuma sexta rodada é executada sem decisão explícita do engenheiro.
- AC-5 [FR-6]: Entre rodadas, o `git diff` não altera `src/`, `datasets/` nem os modelos configurados.

## Constraints
- `src/evaluate.py`, `src/metrics.py`, `src/utils.py` e o dataset não podem ser alterados (`docs/SPEC.md` Constraints).
- O mesmo modelo é usado para resposta e avaliação (`docs/ARCHITECTURE.md` AD-6).
- O v2 continua atendendo `docs/specs/prompt-v2.md` em todas as rodadas.

## Assumptions
- Como o juiz é um LLM, as notas podem variar um pouco entre rodadas com o mesmo prompt.

## Edge Cases
- Avaliação interrompida por erro de API ou limite de requisições: a rodada não conta no limite e é refeita.

## Out of Scope
- A documentação no README e as evidências públicas no LangSmith (entrega 5).

## Open Questions
- Nenhuma.

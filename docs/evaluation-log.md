# Registro de avaliações do prompt v2

Rodadas de `src/evaluate.py` sobre `{USERNAME_LANGSMITH_HUB}/bug_to_user_story_v2`, conforme `docs/specs/evaluation-iteration.md`. Modelos (`docs/ARCHITECTURE.md` AD-6): `gpt-5.4-nano` para gerar e avaliar nas rodadas 1 a 3; `gpt-5.4-mini` para gerar e avaliar na rodada 4; `gpt-5.4-mini` para gerar e `gpt-5.4` como juiz a partir da rodada 5. Critério de aprovação: as 5 métricas e a média ≥ 0.8.

| Rodada | Modelo | Mudanças no prompt | Helpfulness | Correctness | F1-Score | Clarity | Precision | Média | Status | Experimento |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | gpt-5.4-nano | Versão inicial: persona de PM, regras (incluindo "não inventar detalhes"), 3 formatos de saída e 3 exemplos originais | 0.43 | 0.50 | 0.59 | 0.45 | 0.41 | 0.4778 | Reprovado | [fullcycle-bug_to_user_story_v2-1b5083fa](https://smith.langchain.com/o/f6d1dbce-db8d-4668-84ed-5c2a18d3e5ec/datasets/742207c0-e986-476c-9f56-505da7c72bfd/compare?selectedSessions=9c0b01ba-c8b3-4c2e-9cf5-51e6b4d58ea5) |
| 2 | gpt-5.4-nano | Regra "não inventar" trocada por "completar sem contradizer" (critérios mensuráveis, cálculos, sugestões técnicas); critérios explícitos de escolha de formato; seções extras do Formato 2; exemplos 2 e 3 mais específicos | 0.47 | 0.51 | 0.66 | 0.59 | 0.36 | 0.5178 | Reprovado | [fullcycle-bug_to_user_story_v2-6877860e](https://smith.langchain.com/o/f6d1dbce-db8d-4668-84ed-5c2a18d3e5ec/datasets/742207c0-e986-476c-9f56-505da7c72bfd/compare?selectedSessions=4537dd77-1532-42d4-8e7d-661077e6c78f) |
| 3 | gpt-5.4-nano | Respostas enxutas: Formato 1 só com a história e 5 critérios; números só para desempenho/limite ou cálculos; sugestões técnicas só nos Formatos 2 e 3; checagem final contra `===`; novo exemplo no Formato 1 | 0.46 | 0.55 | 0.71 | 0.52 | 0.39 | 0.5283 | Reprovado | [fullcycle-bug_to_user_story_v2-6e210c3a](https://smith.langchain.com/o/f6d1dbce-db8d-4668-84ed-5c2a18d3e5ec/datasets/742207c0-e986-476c-9f56-505da7c72bfd/compare?selectedSessions=fb024975-49ab-4cbe-8ebd-7572052a5bdd) |
| 4 | gpt-5.4-mini | Troca do modelo de `gpt-5.4-nano` para `gpt-5.4-mini` (gerador e juiz); proibição dos elementos do Formato 3 nos Formatos 1 e 2; user prompt pede para decidir o formato antes de escrever | 0.78 | 0.77 | 0.83 | 0.86 | 0.71 | 0.7901 | Reprovado | [fullcycle-bug_to_user_story_v2-6958e9d6](https://smith.langchain.com/o/f6d1dbce-db8d-4668-84ed-5c2a18d3e5ec/datasets/742207c0-e986-476c-9f56-505da7c72bfd/compare?selectedSessions=29e760d7-6ba1-46bf-a595-86af13e036a9) |
| 5 | gpt-5.4-mini (juiz gpt-5.4) | Juiz trocado para `gpt-5.4` (DD-2); metas de desempenho melhores que o valor do relato; lista de critérios usuais por tipo de problema (interface, permissão, desempenho, integração, cálculo, compatibilidade) | 0.84 | 0.81 | 0.79 | 0.86 | 0.83 | 0.8265 | Reprovado (só F1 < 0.8) | [fullcycle-bug_to_user_story_v2-8b5efcda](https://smith.langchain.com/o/f6d1dbce-db8d-4668-84ed-5c2a18d3e5ec/datasets/742207c0-e986-476c-9f56-505da7c72bfd/compare?selectedSessions=f71a93ea-8208-4f67-9106-71e0c232113c) |
| 6 | gpt-5.4-mini (juiz gpt-5.4) | Rodada autorizada pelo engenheiro além do limite de 5. Formato 2 para qualquer relato com detalhes além de uma ou duas frases (na dúvida, Formato 2), sempre com uma seção de critérios extra (padrão: Critérios Técnicos) e uma seção de contexto com os dados do relato | 0.85 | 0.83 | 0.84 | 0.87 | 0.82 | 0.8403 | **Aprovado** | [fullcycle-bug_to_user_story_v2-852d5544](https://smith.langchain.com/o/f6d1dbce-db8d-4668-84ed-5c2a18d3e5ec/datasets/742207c0-e986-476c-9f56-505da7c72bfd/compare?selectedSessions=4dc910e3-2578-495e-a4d7-345c79acac2c) |

## Diagnóstico por rodada

### Rodada 1
- Formato errado em 12 de 12 relatos com um único problema: todos saíram no formato estendido (`===`), em média 2,7x maiores que a referência, o que derrubou Clarity.
- A regra "não inventar detalhes" deixou as respostas genéricas. As referências trazem critérios mensuráveis, cálculos e sugestões técnicas, e a falta deles derrubou Precision e F1.

### Rodada 2
- F1 (0.59 → 0.66) e Clarity (0.45 → 0.59) subiram, mas Precision caiu (0.41 → 0.36).
- Excesso: respostas simples e médias ficaram 4,6x maiores que a referência (eram 2,7x), com Critérios Técnicos, de Prevenção, códigos HTTP, prazos e testes em relatos de uma frase. O juiz de Precision pune o que não está na referência.
- O formato estendido (`===`) ainda apareceu em 8 de 12 relatos com um único problema.

### Rodada 3
- F1 subiu (0.66 → 0.71) e o tamanho caiu (2,2x nos relatos simples e médios), mas Clarity (0.52) e Precision (0.39) seguiram baixas.
- O formato estendido (`===`) ainda apareceu em 8 de 12 relatos com um único problema.
- Juiz pouco confiável: os comentários apontam como ausentes itens que estão na resposta. Reavaliando uma mesma resposta, o `gpt-5.4-mini` deu Precision 0.47 e 0.60 e Clarity 0.82 e 0.89, e penalizou o "ID 1234", que está no relato; o `gpt-5.4` deu 0.87 e 0.93 nas duas vezes.
- As rodadas 1 a 3 usaram `gpt-5.4-nano` como gerador e juiz, e não `gpt-5.4-mini` como se supunha. A partir da rodada 4, os dois papéis usam `gpt-5.4-mini`.

### Rodada 4
- F1 (0.83) e Clarity (0.86) passaram. O formato foi resolvido: 0 de 12 relatos com um único problema usaram `===`, e o tamanho caiu para 1,1x a referência.
- Precision (0.71) segue abaixo de 0.8 e puxa Helpfulness e Correctness, que são médias com ela. Cinco casos ficaram abaixo de 0.5.
- Em 3 desses 5 casos, o juiz penaliza itens que estão na própria referência ("contador do carrinho", "email de confirmação") ou o próprio formato de user story. Em um caso, a resposta usou como meta de desempenho o valor ruim do relato (2 minutos), e não uma meta melhor (a referência pede menos de 30 s).

Checagem offline entre as rodadas 4 e 5 (não conta como rodada): as 15 respostas da rodada 4, reavaliadas com o juiz `gpt-5.4`, deram F1 0.78, Clarity 0.87, Precision 0.80, Helpfulness 0.83, Correctness 0.79 e média 0.81. O juiz maior corrigiu as notas extremas de Precision, mas sozinho não aprovaria.

### Rodada 5
- 4 das 5 métricas passaram (Helpfulness 0.84, Correctness 0.81, Clarity 0.86, Precision 0.83); média 0.8265.
- F1 ficou em 0.79, puxado por três relatos médios (modal em telas pequenas, lista de notificações no Android e relatório lento) com F1 entre 0.65 e 0.66: as referências trazem critérios específicos que a resposta não cobre.
- Limite de 5 rodadas atingido (`docs/specs/evaluation-iteration.md` FR-5): iteração pausada até decisão do engenheiro.

### Rodada 6 (autorizada além do limite)
- Aprovado: as 5 métricas e a média ≥ 0.8 (Helpfulness 0.85, Correctness 0.83, F1 0.84, Clarity 0.87, Precision 0.82; média 0.8403).
- Os três relatos médios que puxavam o F1 na rodada 5 subiram (modal 0.66 → 0.78, Android 0.66 → 0.80, relatório 0.65 → 0.83) ao passarem a ter seções de critérios técnicos e de contexto.
- A menor nota individual da rodada foi 0.6904 (F1 do relato "Carrinho permite finalizar compra mesmo com produto fora de estoque"); todas as demais ficaram acima de 0.70.

# Feature Specification: Documentação e evidências

## Goal
Detalhar `docs/SPEC.md` FR-7 e FR-8: transformar o `README.md` na documentação do projeto entregue (técnicas aplicadas, resultados finais e como executar) e disponibilizar evidências públicas da avaliação no LangSmith.

## Functional Requirements
- FR-1: O `README.md` substitui o enunciado do desafio: apresenta o projeto, aponta para o repositório base (https://github.com/devfullcycle/mba-ia-pull-evaluation-prompt) e contém as seções "Técnicas Aplicadas (Fase 2)", "Resultados Finais" e "Como Executar".
- FR-2: "Técnicas Aplicadas (Fase 2)" descreve Few-shot Learning, Role Prompting e Skeleton of Thought, cada uma com a justificativa da escolha e um exemplo prático tirado de `prompts/bug_to_user_story_v2.yml`.
- FR-3: "Resultados Finais" contém:
  - o link público do dataset de avaliação;
  - screenshots com as notas ≥ 0.8 do experimento aprovado;
  - a evolução das notas nas rodadas, a partir de `docs/evaluation-log.md`;
  - a comparação qualitativa entre v1 e v2: o que mudou e por quê.
- FR-4: "Como Executar" contém:
  - os pré-requisitos: Python 3.10+, contas e chaves do LangSmith e da OpenAI, e o handle do Hub;
  - a criação do venv e a instalação das dependências;
  - a configuração do `.env`, incluindo os modelos usados (gerador e juiz);
  - os comandos de cada fase: pull, edição do v2, testes, push e avaliação;
  - como gerar o link público do dataset.
- FR-5: O link público do dataset `{LANGSMITH_PROJECT}-eval` é gerado uma única vez com `Client().share_dataset(...)` e registrado no README.
- FR-6: As evidências mostram o dataset com 15 exemplos, o experimento aprovado e o tracing detalhado de pelo menos 3 exemplos, por meio do link público e de screenshots.
- FR-7: As imagens usadas no README ficam versionadas em `docs/images/` e são referenciadas por caminho relativo.

## Acceptance Criteria
- AC-1 [FR-1]: O `README.md` não contém mais o texto do enunciado, tem o link para o repositório base e as três seções exigidas.
- AC-2 [FR-2]: Cada uma das 3 técnicas tem justificativa e um trecho ou descrição concreta de como aparece no v2.
- AC-3 [FR-3]: "Resultados Finais" tem o link público, pelo menos um screenshot com as 5 notas ≥ 0.8, a tabela das rodadas e a comparação v1 × v2.
- AC-4 [FR-4]: Seguindo só "Como Executar" em um clone com `.env` preenchido, os comandos de pull, `pytest`, push e avaliação executam na ordem descrita.
- AC-5 [FR-5, FR-6]: O link público abre sem login e mostra os 15 exemplos e o experimento aprovado. O README tem screenshots do tracing de pelo menos 3 exemplos.
- AC-6 [FR-7]: Toda imagem referenciada no README existe em `docs/images/` e aparece ao abrir o README no GitHub.

## Constraints
- Nenhuma chave, token ou conteúdo do `.env` aparece no README nem nas imagens.
- `src/evaluate.py`, `src/metrics.py`, `src/utils.py` e o dataset não são alterados (`docs/SPEC.md` Constraints).
- A pasta `screenshots/` continua ignorada pelo `.gitignore`.

## Assumptions
- Os screenshots são capturados pelo engenheiro no LangSmith e salvos em `docs/images/`.
- O link gerado por `share_dataset` expõe junto os experimentos rodados contra o dataset, como descreve o enunciado.

## Edge Cases
- Se o dataset for compartilhado de novo, o link muda, e o README precisa ser atualizado com o novo link.

## Out of Scope
- Avaliar quantitativamente o v1 (a comparação é qualitativa).

## Open Questions
- Nenhuma.

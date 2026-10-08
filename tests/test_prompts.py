"""
Testes automatizados para validação de prompts.
"""
import json
import re
import pytest
import yaml
import sys
from pathlib import Path

from langchain_core.prompts import ChatPromptTemplate

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils import validate_prompt_structure

ROOT = Path(__file__).parent.parent
PROMPT_PATH = ROOT / "prompts" / "bug_to_user_story_v2.yml"
PROMPT_KEY = "bug_to_user_story_v2"
DATASET_PATH = ROOT / "datasets" / "bug_to_user_story.jsonl"


def load_prompts(file_path: str):
    """Carrega prompts do arquivo YAML."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def iter_strings(value):
    """Percorre recursivamente todos os textos de uma estrutura YAML."""
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from iter_strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from iter_strings(item)


@pytest.fixture
def prompt_file():
    return load_prompts(PROMPT_PATH)


@pytest.fixture
def prompt(prompt_file):
    return prompt_file[PROMPT_KEY]


class TestPrompts:
    def test_prompt_has_system_prompt(self, prompt):
        """Verifica se o campo 'system_prompt' existe e não está vazio."""
        assert prompt.get("system_prompt", "").strip()

    def test_prompt_has_role_definition(self, prompt):
        """Verifica se o prompt define uma persona (ex: "Você é um Product Manager")."""
        assert re.search(r"Você é (um|uma) [^.\n]*Product Manager", prompt.get("system_prompt", ""))

    def test_prompt_mentions_format(self, prompt):
        """Verifica se o prompt exige formato Markdown ou User Story padrão."""
        system_prompt = prompt.get("system_prompt", "")

        assert "user story" in system_prompt.lower()
        for marker in ["Como um", "eu quero", "para que", "Critérios de Aceitação", "Dado que", "Quando", "Então"]:
            assert marker in system_prompt, f"Formato sem o marcador: {marker}"

    def test_prompt_has_few_shot_examples(self, prompt):
        """Verifica se o prompt contém exemplos de entrada/saída (técnica Few-shot)."""
        system_prompt = prompt.get("system_prompt", "")

        inputs = re.findall(r"^\s*Entrada:", system_prompt, flags=re.MULTILINE)
        outputs = re.findall(r"^\s*Saída:", system_prompt, flags=re.MULTILINE)
        assert min(len(inputs), len(outputs)) >= 2

    def test_prompt_no_todos(self, prompt_file):
        """Garante que você não esqueceu nenhum `[TODO]` no texto."""
        for text in iter_strings(prompt_file):
            assert "TODO" not in text

    def test_minimum_techniques(self, prompt):
        """Verifica (através dos metadados do yaml) se pelo menos 2 técnicas foram listadas."""
        assert len(prompt.get("techniques_applied", [])) >= 2

    def test_prompt_metadata(self, prompt_file, prompt):
        """Verifica chave única, versão, técnicas da spec e a validação de utils."""
        assert list(prompt_file) == [PROMPT_KEY]
        assert prompt.get("version") == "v2"
        assert set(prompt.get("techniques_applied", [])) >= {
            "Few-shot Learning",
            "Role Prompting",
            "Skeleton of Thought",
        }
        is_valid, errors = validate_prompt_structure(prompt)
        assert is_valid, errors

    def test_examples_not_copied_from_dataset(self, prompt):
        """Garante que nenhum relato do dataset de avaliação foi usado como exemplo."""
        system_prompt = prompt.get("system_prompt", "")

        with open(DATASET_PATH, encoding="utf-8") as f:
            reports = [json.loads(line)["inputs"]["bug_report"] for line in f if line.strip()]

        for report in reports:
            first_line = report.strip().splitlines()[0]
            assert first_line not in system_prompt, f"Exemplo copiado do dataset: {first_line}"

    def test_template_uses_only_bug_report(self, prompt):
        """Verifica que o template monta com {bug_report} como única variável."""
        template = ChatPromptTemplate.from_messages([
            ("system", prompt.get("system_prompt", "")),
            ("human", prompt.get("user_prompt", "")),
        ])

        assert template.input_variables == ["bug_report"]
        assert "{bug_report}" not in prompt.get("system_prompt", "")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

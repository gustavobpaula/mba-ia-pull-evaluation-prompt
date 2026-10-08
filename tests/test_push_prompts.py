"""
Testes offline do push de prompts (docs/specs/push-prompts.md).
"""
import sys
from pathlib import Path

import pytest
import yaml
from langchain_core.prompts import HumanMessagePromptTemplate, SystemMessagePromptTemplate
from langsmith.utils import LangSmithConflictError

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import push_prompts
from push_prompts import build_hub_metadata, build_prompt_template, validate_prompt

ROOT = Path(__file__).parent.parent
V2_PATH = ROOT / "prompts" / "bug_to_user_story_v2.yml"


def valid_prompt_data():
    return {
        "description": "Converte bugs em user stories",
        "system_prompt": "Você é um Product Manager.",
        "user_prompt": "Relato:\n{bug_report}",
        "version": "v2",
        "tags": ["user-story", "few-shot-learning"],
        "techniques_applied": ["Few-shot Learning", "Role Prompting"],
    }


NOTHING_TO_COMMIT = (
    'Conflict for /commits/meu-handle/bug_to_user_story_v2. '
    '{"error":"Nothing to commit: prompt has not changed since latest commit"}'
)


class RecordingClient:
    """Client falso que registra as chamadas de push."""

    calls = []
    conflict_on_commit = None

    def push_prompt(self, prompt_name, object=None, **kwargs):
        RecordingClient.calls.append({"prompt_name": prompt_name, "object": object, **kwargs})
        if object is not None and RecordingClient.conflict_on_commit:
            raise LangSmithConflictError(RecordingClient.conflict_on_commit)
        return f"https://smith.langchain.com/prompts/{prompt_name}"


class FailingClient:
    def push_prompt(self, *args, **kwargs):
        raise RuntimeError("401 Authentication failed")


@pytest.fixture
def recording_client(monkeypatch):
    RecordingClient.calls = []
    RecordingClient.conflict_on_commit = None
    monkeypatch.setattr(push_prompts, "Client", RecordingClient)
    return RecordingClient


@pytest.fixture
def env(monkeypatch):
    monkeypatch.setenv("LANGSMITH_API_KEY", "fake-key")
    monkeypatch.setenv("USERNAME_LANGSMITH_HUB", "meu-handle")


@pytest.fixture
def prompt_file(tmp_path, monkeypatch):
    """Grava um YAML de prompt em tmp_path e aponta o script para ele."""

    def write(prompt_data):
        path = tmp_path / "bug_to_user_story_v2.yml"
        path.write_text(yaml.safe_dump({"bug_to_user_story_v2": prompt_data}, allow_unicode=True), encoding="utf-8")
        monkeypatch.setattr(push_prompts, "PROMPT_PATH", str(path))

    return write


class TestValidatePrompt:
    def test_accepts_real_v2_prompt(self):
        data = yaml.safe_load(V2_PATH.read_text(encoding="utf-8"))["bug_to_user_story_v2"]

        assert validate_prompt(data) == (True, [])

    @pytest.mark.parametrize(
        "field, value, expected_error",
        [
            ("system_prompt", "", "system_prompt"),
            ("techniques_applied", ["Few-shot Learning"], "técnicas"),
            ("system_prompt", "Você é um PM. {bug_report}", "apenas no user_prompt"),
            ("user_prompt", "{bug_report} {extra}", "apenas a variável"),
            ("user_prompt", "", "user_prompt"),
        ],
    )
    def test_rejects_invalid_prompt(self, field, value, expected_error):
        data = valid_prompt_data()
        data[field] = value

        is_valid, errors = validate_prompt(data)

        assert not is_valid
        assert any(expected_error in error for error in errors), errors

    @pytest.mark.parametrize(
        "field, value, expected_error",
        [
            ("system_prompt", None, "system_prompt deve ser um texto"),
            ("techniques_applied", None, "techniques_applied deve ser uma lista"),
            ("tags", "user-story", "tags deve ser uma lista"),
        ],
    )
    def test_lists_type_errors_instead_of_crashing(self, field, value, expected_error):
        data = valid_prompt_data()
        data[field] = value

        assert validate_prompt(data) == (False, [expected_error])

    def test_accepts_escaped_braces_in_system_prompt(self):
        data = valid_prompt_data()
        data["system_prompt"] = 'Exemplo de JSON: {{"campo": 1}}'

        assert validate_prompt(data) == (True, [])


class TestBuilders:
    def test_template_is_system_then_human(self):
        data = valid_prompt_data()

        messages = build_prompt_template(data).messages

        assert [type(m) for m in messages] == [SystemMessagePromptTemplate, HumanMessagePromptTemplate]
        assert messages[0].prompt.template == data["system_prompt"]
        assert messages[1].prompt.template == data["user_prompt"]

    def test_metadata_adds_techniques_as_kebab_case_tags_and_readme(self):
        metadata = build_hub_metadata(valid_prompt_data())

        assert metadata["description"] == "Converte bugs em user stories"
        assert metadata["tags"] == ["user-story", "few-shot-learning", "role-prompting"]
        assert "- Few-shot Learning" in metadata["readme"]
        assert "- Role Prompting" in metadata["readme"]


class TestMain:
    @pytest.mark.parametrize("missing", ["LANGSMITH_API_KEY", "USERNAME_LANGSMITH_HUB"])
    def test_missing_env_fails_without_calling_hub(self, monkeypatch, env, recording_client, missing):
        monkeypatch.delenv(missing)

        assert push_prompts.main() != 0
        assert recording_client.calls == []

    def test_invalid_prompt_fails_without_calling_hub(self, env, recording_client, prompt_file):
        data = valid_prompt_data()
        data["techniques_applied"] = []
        prompt_file(data)

        assert push_prompts.main() != 0
        assert recording_client.calls == []

    def test_missing_file_fails_without_calling_hub(self, monkeypatch, env, recording_client, tmp_path):
        monkeypatch.setattr(push_prompts, "PROMPT_PATH", str(tmp_path / "ausente.yml"))

        assert push_prompts.main() != 0
        assert recording_client.calls == []

    def test_pushes_public_prompt_with_metadata(self, env, recording_client, prompt_file, capsys):
        prompt_file(valid_prompt_data())

        assert push_prompts.main() == 0
        [call] = recording_client.calls
        assert call["prompt_name"] == "meu-handle/bug_to_user_story_v2"
        assert call["is_public"] is True
        assert call["tags"] == ["user-story", "few-shot-learning", "role-prompting"]
        assert call["object"].input_variables == ["bug_report"]
        assert "https://smith.langchain.com/prompts/meu-handle/bug_to_user_story_v2" in capsys.readouterr().out

    def test_unchanged_template_succeeds_with_notice(self, env, recording_client, prompt_file, capsys):
        prompt_file(valid_prompt_data())
        recording_client.conflict_on_commit = NOTHING_TO_COMMIT

        assert push_prompts.main() == 0
        assert "sem alterações" in capsys.readouterr().out

    def test_other_conflict_fails_without_notice(self, env, recording_client, prompt_file, capsys):
        prompt_file(valid_prompt_data())
        recording_client.conflict_on_commit = "Conflict for /repos: repository already exists"

        assert push_prompts.main() != 0
        output = capsys.readouterr().out
        assert "sem alterações" not in output
        assert "Prompt publicado" not in output

    def test_hub_error_fails(self, monkeypatch, env, prompt_file):
        prompt_file(valid_prompt_data())
        monkeypatch.setattr(push_prompts, "Client", FailingClient)

        assert push_prompts.main() != 0

"""
Testes offline do pull de prompts (docs/specs/pull-prompts.md).
"""
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pull_prompts
from pull_prompts import prompt_to_yaml_data

SYSTEM_TEXT = "Você é um assistente.\n\nRelato:\n{bug_report}\n"
USER_TEXT = "{bug_report}"


def seed_template():
    return ChatPromptTemplate.from_messages([("system", SYSTEM_TEXT), ("human", USER_TEXT)])


def fake_client(metadata):
    """Cria um Client falso que devolve o prompt semente e os metadados dados."""

    class FakeClient:
        def pull_prompt(self, *args, **kwargs):
            return seed_template()

        def get_prompt(self, *args, **kwargs):
            return metadata

    return FakeClient


class FailingClient:
    """Client falso cujo pull falha como um erro do Hub."""

    def pull_prompt(self, *args, **kwargs):
        raise RuntimeError("404 not found")

    def get_prompt(self, *args, **kwargs):
        raise RuntimeError("404 not found")


@pytest.fixture
def existing_output(tmp_path, monkeypatch):
    output = tmp_path / "bug_to_user_story_v1.yml"
    output.write_text("conteudo original\n", encoding="utf-8")
    monkeypatch.setattr(pull_prompts, "OUTPUT_PATH", str(output))
    return output


class TestPromptToYamlData:
    def test_converts_system_and_human_messages(self):
        data = prompt_to_yaml_data("leonanluppi/bug_to_user_story_v1", seed_template())

        assert list(data) == ["bug_to_user_story_v1"]
        prompt = data["bug_to_user_story_v1"]
        assert prompt["system_prompt"] == SYSTEM_TEXT
        assert prompt["user_prompt"] == USER_TEXT
        assert prompt["version"] == "v1"

    def test_includes_hub_metadata_when_present(self):
        data = prompt_to_yaml_data(
            "leonanluppi/bug_to_user_story_v1",
            seed_template(),
            description="Descrição do Hub",
            tags=["user-story"],
        )

        prompt = data["bug_to_user_story_v1"]
        assert prompt["description"] == "Descrição do Hub"
        assert prompt["tags"] == ["user-story"]

    def test_omits_hub_metadata_when_absent(self):
        data = prompt_to_yaml_data("leonanluppi/bug_to_user_story_v1", seed_template(), tags=[])

        prompt = data["bug_to_user_story_v1"]
        assert "description" not in prompt
        assert "tags" not in prompt

    @pytest.mark.parametrize(
        "messages",
        [
            [("system", SYSTEM_TEXT)],
            [("system", SYSTEM_TEXT), ("human", USER_TEXT), ("ai", "resposta")],
            [("human", USER_TEXT), ("system", SYSTEM_TEXT)],
        ],
    )
    def test_rejects_unexpected_structure(self, messages):
        template = ChatPromptTemplate.from_messages(messages)

        with pytest.raises(ValueError, match="SystemMessagePromptTemplate"):
            prompt_to_yaml_data("leonanluppi/bug_to_user_story_v1", template)

    def test_rejects_non_chat_prompt(self):
        template = PromptTemplate.from_template(USER_TEXT)

        with pytest.raises(ValueError, match="Recebido: PromptTemplate"):
            prompt_to_yaml_data("leonanluppi/bug_to_user_story_v1", template)


class TestMain:
    @pytest.mark.parametrize(
        "metadata, expected_extra",
        [
            (
                SimpleNamespace(description="Descrição do Hub", tags=["user-story"]),
                {"description": "Descrição do Hub", "tags": ["user-story"]},
            ),
            (None, {}),
        ],
    )
    def test_pull_writes_snapshot(self, monkeypatch, existing_output, metadata, expected_extra):
        monkeypatch.setenv("LANGSMITH_API_KEY", "fake-key")
        monkeypatch.setattr(pull_prompts, "Client", fake_client(metadata))

        assert pull_prompts.main() == 0
        saved = yaml.safe_load(existing_output.read_text(encoding="utf-8"))
        assert saved == {
            "bug_to_user_story_v1": {
                "system_prompt": SYSTEM_TEXT,
                "user_prompt": USER_TEXT,
                "version": "v1",
                **expected_extra,
            }
        }

    def test_missing_api_key_fails_without_calling_hub(self, monkeypatch, existing_output):
        monkeypatch.delenv("LANGSMITH_API_KEY", raising=False)
        monkeypatch.setattr(pull_prompts, "Client", lambda: pytest.fail("Hub não deveria ser chamado"))

        assert pull_prompts.main() != 0
        assert existing_output.read_text(encoding="utf-8") == "conteudo original\n"

    def test_hub_error_fails_without_writing(self, monkeypatch, existing_output):
        monkeypatch.setenv("LANGSMITH_API_KEY", "fake-key")
        monkeypatch.setattr(pull_prompts, "Client", FailingClient)

        assert pull_prompts.main() != 0
        assert existing_output.read_text(encoding="utf-8") == "conteudo original\n"

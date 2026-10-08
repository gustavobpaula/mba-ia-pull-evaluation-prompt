"""
Script para fazer pull de prompts do LangSmith Prompt Hub.

Este script:
1. Conecta ao LangSmith usando credenciais do .env
2. Faz pull do prompt semente do desafio
3. Salva localmente em prompts/bug_to_user_story_v1.yml

DICAS DE IMPLEMENTAÇÃO:

- O pull é feito pelo cliente do LangSmith:

      from langsmith import Client
      client = Client()
      prompt = client.pull_prompt(
          "leonanluppi/bug_to_user_story_v1",
          dangerously_pull_public_prompt=True,
      )

- O parâmetro `dangerously_pull_public_prompt=True` é obrigatório sempre que o
  identificador tem dono explícito ("owner/nome"). O LangSmith bloqueia esse pull
  por padrão porque um prompt do Hub é um objeto LangChain serializado, que pode
  vir de terceiros. Aqui o prompt é o do desafio, então o risco é conhecido.

- O retorno é um ChatPromptTemplate. Para extrair o conteúdo das mensagens,
  use a serialização nativa do LangChain (`prompt.messages`, e o atributo
  `.prompt.template` de cada mensagem).

- Use `save_yaml` de utils.py para gravar o resultado no arquivo .yml.
"""

import re
import sys
from dotenv import load_dotenv
from langsmith import Client
from langchain_core.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)
from utils import save_yaml, check_env_vars, print_section_header

load_dotenv()

SEED_PROMPT = "leonanluppi/bug_to_user_story_v1"
OUTPUT_PATH = "prompts/bug_to_user_story_v1.yml"


def prompt_to_yaml_data(
    prompt_name: str,
    template: ChatPromptTemplate,
    description: str | None = None,
    tags: list | None = None,
) -> dict:
    """
    Converte um ChatPromptTemplate do Hub no schema YAML do projeto.

    Args:
        prompt_name: Identificador do prompt ("owner/nome" ou "nome")
        template: Prompt retornado pelo pull
        description: Descrição do prompt no Hub, se houver
        tags: Tags do prompt no Hub, se houver

    Returns:
        Dicionário {nome: {campos}} pronto para save_yaml

    Raises:
        ValueError: Se o prompt não for uma mensagem system seguida de uma human
    """
    if not isinstance(template, ChatPromptTemplate):
        raise ValueError(
            "Estrutura inesperada: o prompt deve ser um ChatPromptTemplate. "
            f"Recebido: {type(template).__name__}"
        )

    messages = template.messages
    if (
        len(messages) != 2
        or not isinstance(messages[0], SystemMessagePromptTemplate)
        or not isinstance(messages[1], HumanMessagePromptTemplate)
    ):
        found = ", ".join(type(m).__name__ for m in messages) or "nenhuma"
        raise ValueError(
            "Estrutura inesperada: o prompt deve ter uma mensagem system seguida "
            f"de uma human. Encontradas: {found}"
        )

    system, human = messages
    name = prompt_name.split("/")[-1]
    data = {}
    if description:
        data["description"] = description
    data["system_prompt"] = system.prompt.template
    data["user_prompt"] = human.prompt.template

    version = re.search(r"_(v\d+)$", name)
    if version:
        data["version"] = version.group(1)
    if tags:
        data["tags"] = list(tags)

    return {name: data}


def pull_prompts_from_langsmith() -> bool:
    """
    Faz pull do prompt semente e grava o snapshot local em YAML.

    Nada é gravado se o pull ou a conversão falharem.

    Returns:
        True se sucesso, False caso contrário
    """
    try:
        client = Client()
        print(f"Puxando prompt: {SEED_PROMPT}")
        template = client.pull_prompt(SEED_PROMPT, dangerously_pull_public_prompt=True)
        metadata = client.get_prompt(SEED_PROMPT)

        data = prompt_to_yaml_data(
            SEED_PROMPT,
            template,
            description=getattr(metadata, "description", None),
            tags=getattr(metadata, "tags", None),
        )
    except Exception as e:
        print(f"❌ Erro ao fazer pull de '{SEED_PROMPT}': {e}")
        return False

    if not save_yaml(data, OUTPUT_PATH):
        return False

    print(f"✓ Prompt salvo em {OUTPUT_PATH}")
    return True


def main():
    """Função principal"""
    print_section_header("Pull de prompts do LangSmith Hub")

    if not check_env_vars(["LANGSMITH_API_KEY"]):
        return 1

    return 0 if pull_prompts_from_langsmith() else 1


if __name__ == "__main__":
    sys.exit(main())

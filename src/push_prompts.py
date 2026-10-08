"""
Script para fazer push de prompts otimizados ao LangSmith Prompt Hub.

Este script:
1. Lê os prompts otimizados de prompts/bug_to_user_story_v2.yml
2. Valida os prompts
3. Faz push PÚBLICO para o LangSmith Hub
4. Adiciona metadados (tags, descrição, técnicas utilizadas)

DICAS DE IMPLEMENTAÇÃO:

- O push é feito pelo cliente do LangSmith:

      from langsmith import Client
      from langchain_core.prompts import ChatPromptTemplate

      client = Client()
      prompt = ChatPromptTemplate.from_messages([
          ("system", system_prompt),
          ("user", user_prompt),
      ])
      url = client.push_prompt(
          f"{username}/bug_to_user_story_v2",
          object=prompt,
          is_public=True,
          description="...",
          tags=[...],
      )

- `username` vem de USERNAME_LANGSMITH_HUB no .env e precisa ser o seu handle
  do Hub. Se você ainda não tem um handle, veja as instruções no .env.example.

- A variável do template precisa ser {bug_report}, que é a chave de entrada
  usada no dataset de avaliação.

- Use `load_yaml` de utils.py para ler o arquivo .yml.
"""

import os
import sys
from dotenv import load_dotenv
from langsmith import Client
from langsmith.utils import LangSmithConflictError
from langchain_core.prompts import ChatPromptTemplate
from utils import load_yaml, check_env_vars, print_section_header, validate_prompt_structure

load_dotenv()

PROMPT_KEY = "bug_to_user_story_v2"
PROMPT_PATH = f"prompts/{PROMPT_KEY}.yml"
TEMPLATE_VARIABLE = "bug_report"


def build_prompt_template(prompt_data: dict) -> ChatPromptTemplate:
    """Monta o template publicado: mensagem system seguida de human (AD-3)."""
    return ChatPromptTemplate.from_messages([
        ("system", prompt_data.get("system_prompt", "")),
        ("human", prompt_data.get("user_prompt", "")),
    ])


def build_hub_metadata(prompt_data: dict) -> dict:
    """
    Monta os metadados do Hub a partir do YAML.

    As técnicas entram nas tags em kebab-case e são listadas no README
    com os rótulos originais.
    """
    techniques = prompt_data.get("techniques_applied", [])
    tags = list(prompt_data.get("tags", []))
    for technique in techniques:
        tag = technique.lower().replace(" ", "-")
        if tag not in tags:
            tags.append(tag)

    readme_lines = [f"# {PROMPT_KEY}", "", prompt_data.get("description", ""), "", "## Técnicas aplicadas", ""]
    readme_lines += [f"- {technique}" for technique in techniques]

    return {
        "description": prompt_data.get("description"),
        "tags": tags,
        "readme": "\n".join(readme_lines) + "\n",
    }


def push_prompt_to_langsmith(prompt_name: str, prompt_data: dict) -> bool:
    """
    Faz push do prompt otimizado para o LangSmith Hub (PÚBLICO).

    Args:
        prompt_name: Nome do prompt
        prompt_data: Dados do prompt

    Returns:
        True se sucesso, False caso contrário
    """
    metadata = build_hub_metadata(prompt_data)

    try:
        client = Client()
        print(f"Publicando prompt: {prompt_name}")
        try:
            url = client.push_prompt(
                prompt_name,
                object=build_prompt_template(prompt_data),
                is_public=True,
                **metadata,
            )
        except LangSmithConflictError as e:
            # O Hub recusa commit com template idêntico ao último publicado.
            # Os metadados já foram atualizados; só recuperamos a URL.
            # Qualquer outro conflito é falha real e não pode virar sucesso.
            if "Nothing to commit" not in str(e):
                raise
            url = client.push_prompt(prompt_name, is_public=True, **metadata)
            print("ℹ️  Template sem alterações desde o último push; metadados atualizados.")
    except Exception as e:
        print(f"❌ Erro ao fazer push de '{prompt_name}': {e}")
        return False

    print(f"✓ Prompt publicado: {url}")
    return True


def validate_prompt(prompt_data: dict) -> tuple[bool, list]:
    """
    Valida estrutura básica de um prompt (versão simplificada).

    Args:
        prompt_data: Dados do prompt

    Returns:
        (is_valid, errors) - Tupla com status e lista de erros
    """
    # validate_prompt_structure (utils, congelado) quebra com campos nulos ou de
    # outro tipo; esses casos viram erros listados antes de chamá-lo.
    type_errors = [
        f"{field} deve ser um texto"
        for field in ("description", "system_prompt", "user_prompt")
        if field in prompt_data and not isinstance(prompt_data[field], str)
    ] + [
        f"{field} deve ser uma lista"
        for field in ("tags", "techniques_applied")
        if field in prompt_data and not isinstance(prompt_data[field], list)
    ]
    if type_errors:
        return (False, type_errors)

    _, errors = validate_prompt_structure(prompt_data)

    if not prompt_data.get("user_prompt", "").strip():
        errors.append("user_prompt está vazio ou ausente")
        return (False, errors)

    try:
        system_variables = ChatPromptTemplate.from_messages(
            [("system", prompt_data.get("system_prompt", ""))]
        ).input_variables
        template_variables = build_prompt_template(prompt_data).input_variables
    except Exception as e:
        errors.append(f"Template inválido: {e}")
        return (False, errors)

    if TEMPLATE_VARIABLE in system_variables:
        errors.append(f"{{{TEMPLATE_VARIABLE}}} deve aparecer apenas no user_prompt")
    if template_variables != [TEMPLATE_VARIABLE]:
        errors.append(
            f"O template deve ter apenas a variável {{{TEMPLATE_VARIABLE}}}; "
            f"encontradas: {template_variables}"
        )

    return (len(errors) == 0, errors)


def main():
    """Função principal"""
    print_section_header("Push de prompts para o LangSmith Hub")

    if not check_env_vars(["LANGSMITH_API_KEY", "USERNAME_LANGSMITH_HUB"]):
        return 1

    data = load_yaml(PROMPT_PATH)
    prompt_data = data.get(PROMPT_KEY) if isinstance(data, dict) else None
    if not isinstance(prompt_data, dict):
        print(f"❌ Prompt '{PROMPT_KEY}' não encontrado em {PROMPT_PATH}")
        return 1

    is_valid, errors = validate_prompt(prompt_data)
    if not is_valid:
        print("❌ Prompt inválido, push cancelado:")
        for error in errors:
            print(f"   - {error}")
        return 1

    prompt_name = f"{os.getenv('USERNAME_LANGSMITH_HUB')}/{PROMPT_KEY}"
    return 0 if push_prompt_to_langsmith(prompt_name, prompt_data) else 1


if __name__ == "__main__":
    sys.exit(main())

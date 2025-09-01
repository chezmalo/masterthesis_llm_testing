import json
import re
from pydantic import ValidationError
from openai import OpenAI
from src import config
from src.llm_output_format import LLMAnswer
from src.model_prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE

# erster Prompting-Ansatz (Zero-Shot, mittelspezifisch)
SYSTEM_PROMPT = (
    '''Du bist ein Database-Engineer und verantwortlich für die Analyse von Datenherkünften (Data Lineage)
    und technischen Datentransformationen. Deine Aufgabe ist es, gegebene Datenflüsse mitsamt ihren 
    Transformationen zu verstehen und auf Fehler zu überprüfen. Anschließend sollst du den gegebenen 
    ETL-Prozess kurz beschreiben und anschließend Feedback geben, inwiefern er funktionstüchtig ist 
    oder mögliche Fehlerquellen beinhaltet. Informiere auch über Verbesserungspotenziale, ohne, 
    dass sich das Endergebnis des Datenflusses verändert. Antworte ausschließlich als gültiges JSON 
    nach dem bereitgestellten Schema. Keine Kommentare, keine zusätzlichen Felder.'''
)

def build_user_prompt(case: dict) -> str:
    case_id = case["id"]
    desc = case["description"]
    inputs = case["input_tables"]
    sql_transformation = case["sql_script"]
    focus = case.get("focus", "Datentypen, Transformationen, Rechenlogik")
    schema_json = LLMAnswer.json_schema_str()

    return USER_PROMPT_TEMPLATE.format(
        case_id=case_id,
        desc=desc,
        inputs=json.dumps(inputs, ensure_ascii=False),
        sql_transformation=sql_transformation,
        focus=focus,
        schema_json=schema_json
    )

# Aufruf der OpenAI-kompatiblen API (llm-stats.com mit api_key)
def _client() -> OpenAI:
    return OpenAI(api_key=config.OPENAI_API_KEY, base_url=config.OPENAI_BASE_URL)

# API-Aufruf an das LLM
def prompt_llm(model: str, system_prompt: str, user_prompt: str) -> str:
    client = _client()
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=config.TEMPERATURE,
        # testen des forced JSON-Outputs
        response_format={"type": "json_object"}
    )
    # return raw text
    return resp.choices[0].message.content

# JSON-Extraktion aus der LLM-Antwort
def _extract_json(text: str) -> dict:
    """
    Erwartet die JSON LLMANSWER. Textangaben außerhalb der JSON wird der Text abgeschnitten.
    """
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Fallback: größtes JSON-Objekt extrahieren
        m = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not m:
            raise ValueError("Es konnte kein JSON-Objekt im Text gefunden werden.")
        return json.loads(m.group(0))

# parse Antwort und validiere gegen das Schema LLMAnswer
def parse_answer(raw: str) -> LLMAnswer:
    data = _extract_json(raw)
    try:
        return LLMAnswer.model_validate(data)
    except ValidationError as e:
        raise ValueError(f"Antwort entspricht nicht dem Schema: {e}")

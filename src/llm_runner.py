import json
import re
from typing import Literal, Optional, List
from pydantic import BaseModel, Field, ValidationError
from openai import OpenAI
from src import config
from src.model_prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE

# JSON SCHEMA FÜR DIE LLM-ANTWORT
class TraceStep(BaseModel):
    step: int
    description: str
    formula: Optional[str] = None
    notes: Optional[str] = None

# einzelne Findings (Risiken, Fehler, Verbesserungsvorschläge)
class Finding(BaseModel):
    id: str
    severity: Literal["info", "low", "medium", "high", "critical"]
    message: str
    source: Optional[str] = None

# llm answer schema
class LLMAnswer(BaseModel):
    case_id: str = Field(..., description="ID des Testfalls")
    task_understanding: str
    data_lineage: List[str] = Field(default_factory=list)
    transformations: List[TraceStep] = Field(default_factory=list)
    computations_valid: bool
    computation_details: Optional[str] = None
    risks_or_errors: List[Finding] = Field(default_factory=list)
    final_answer: str

    @classmethod
    def json_schema_str(cls) -> str:
        # gibt das JSON-Schema als formatierten String zurück mithilfe von Pydantic (cls referenziert die Klasse selbst)
        return json.dumps(cls.model_json_schema(), ensure_ascii=False, indent=2)

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
    focus = case.get("focus", "Datenherkunft, Transformationen, Rechenlogik")
    schema_json = LLMAnswer.json_schema_str()

    return USER_PROMPT_TEMPLATE.format(
        case_id=case_id,
        desc=desc,
        inputs=json.dumps(inputs, ensure_ascii=False),
        focus=focus,
        schema_json=schema_json
    )

# Aufruf der OpenAI-kompatiblen API (llm-stats.com mit api_key)
def _client() -> OpenAI:
    return OpenAI(api_key=config.OPENAI_API_KEY, base_url=config.OPENAI_BASE_URL)

# API-Aufruf an das LLM
def ask_llm(model: str, system_prompt: str, user_prompt: str) -> str:
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

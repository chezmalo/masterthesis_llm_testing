from typing import Literal, Optional, List
from pydantic import BaseModel, Field
import json

# beschreibung jedes transformationsschrittes
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

# JSON SCHEMA FÜR DIE LLM-ANTWORT
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
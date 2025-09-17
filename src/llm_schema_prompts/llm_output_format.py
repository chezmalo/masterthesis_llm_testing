from typing import Literal, Optional, List
from pydantic import BaseModel, Field, ConfigDict, constr
import json

# beschreibung jedes transformationsschrittes
class TransformationStep(BaseModel):
    model_config = ConfigDict(extra="forbid")
    step_count: int = Field(..., ge=1, description="Nummer des Transformation-Schrittes")
    description: str = Field(..., min_length=3, max_length=400, description="Beschreibung des Transformation-Schrittes")
    formula: Optional[str] = Field(None , min_length=3, max_length=600, description="Formel oder SQL-Ausdruck")
    improvement: Optional[str] = Field(None, min_length=3, max_length=600, description="Verbesserungsvorschlag")

# einzelne Findings (Risiken, Fehler, Verbesserungsvorschläge)
class Risks(BaseModel):
    model_config = ConfigDict(extra="forbid")
    severity: Literal["info", "low", "medium", "high", "critical"] = Field(..., description="Einstufung des Risikos")
    source_of_risk: str = Field(..., min_length=3, max_length=600, description="Quelle des Risikos")
    fix_suggestion: str = Field(..., min_length=3, max_length=400, description="Vorschlag zur Behebung des Risikos")

# JSON SCHEMA FÜR DIE LLM-ANTWORT
class LLMAnswer(BaseModel):
    model_config = ConfigDict(extra="forbid")
    transformation_understanding: str = Field(..., min_length=3, max_length=2000, description="Kurze Beschreibung des ETL-Prozesses")
    data_lineage: List[str] = Field(default_factory=list, description="Liste der Data-Lineage-Schritte")
    transformations: List[TransformationStep] = Field(default_factory=list, description="Liste der Transformation-Schritte")
    computations_valid: bool = Field(..., description="Ist die Transformation valide")
    computation_details: Optional[str] = Field(None, min_length=3, max_length=2000, description="Details zu den Berechnungen")
    error_risks: List[Risks] = Field(default_factory=list, description="Liste der identifizierten Risiken")
    final_feedback: str = Field(..., min_length=3, max_length=2000, description="Endgültige Einschätzung")

    @classmethod
    def json_schema_str(cls) -> str:
        # gibt das JSON-Schema als formatierten String zurück mithilfe von Pydantic (cls referenziert die Klasse selbst)
        return json.dumps(cls.model_json_schema(), ensure_ascii=False, indent=2)
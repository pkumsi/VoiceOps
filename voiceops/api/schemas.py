from pydantic import BaseModel
from typing import List, Optional, Dict
from pydantic import BaseModel
from typing import Optional, Dict, Any, List


class ChunkTranscriptionResponse(BaseModel):
    session_id: str
    chunk_index: int
    raw_chunk_transcript: str
    corrected_chunk_transcript: str
    session_raw_transcript: Optional[str] = None
    session_corrected_transcript: Optional[str] = None
    extraction: Dict[str, Any]
    corrections: List[Dict[str, Any]]

class CorrectionRecord(BaseModel):
    type: str
    original: str
    corrected: str
    reason: Optional[str] = None

class FinalizeSessionRequest(BaseModel):
    session_id: str
    audience: str = "clinician"


class FinalizeSessionResponse(BaseModel):
    session_id: str
    normalized_transcript: str
    corrected_transcript: str
    corrections: List[Dict[str, Any]]
    extraction: Dict[str, Any]
    redaction: Dict[str, Any]
    summary: Dict[str, Any]

class ExtractionResult(BaseModel):
    medications: List[str] = []
    dosages: List[str] = []
    frequencies: List[str] = []
    negations: List[str] = []
    symptoms: List[str] = []
    intent: Optional[str] = None
    risk_flag: bool = False


class TranscriptionResponse(BaseModel):
    raw_transcript: str
    corrected_transcript: str
    corrections: List[CorrectionRecord]
    extraction: ExtractionResult


class EvaluationResponse(BaseModel):
    wer: float
    cer: float
    keyword_accuracy: float
    numeric_accuracy: float
    negation_accuracy: float
    details: Dict[str, str] = {}

from pydantic import BaseModel
from typing import List, Optional, Dict, Any


class CorrectionRecord(BaseModel):
    type: str
    original: str
    corrected: str
    reason: Optional[str] = None


class ExtractionResult(BaseModel):
    medications: List[str] = []
    dosages: List[str] = []
    frequencies: List[str] = []
    negations: List[str] = []
    intent: Optional[str] = None
    risk_flag: bool = False


class TranscriptionResponse(BaseModel):
    raw_transcript: str
    corrected_transcript: str
    corrections: List[Dict[str, Any]]
    extraction: ExtractionResult


class EvaluationResponse(BaseModel):
    wer: float
    cer: float
    keyword_accuracy: float
    numeric_accuracy: float
    negation_accuracy: float
    details: Dict[str, str] = {}


class RedactionResponse(BaseModel):
    original_text: str
    redacted_text: str
    redactions: List[Dict[str, Any]]


class SummaryRequest(BaseModel):
    transcript: str
    audience: str = "clinician"


class SummaryResponse(BaseModel):
    provider: str
    audience: str
    result: Dict[str, Any]


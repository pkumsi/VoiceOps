import uuid
import os
import tempfile

from fastapi import FastAPI, UploadFile, File, Form
from voiceops.api.schemas import (
    TranscriptionResponse,
    EvaluationResponse,
    RedactionResponse,
    SummaryRequest,
    SummaryResponse,
    ChunkTranscriptionResponse,
)
from voiceops.pipeline.transcribe import Transcriber
from voiceops.pipeline.normalize import normalize_transcript
from voiceops.pipeline.correct import correct_transcript_with_gated_retrieval
from voiceops.pipeline.preprocess import preprocess_audio
from voiceops.pipeline.redact import redact_pii
from voiceops.extraction.entities import extract_entities
from voiceops.extraction.summary_llm import summarize_transcript
from jiwer import wer, cer
from fastapi.middleware.cors import CORSMiddleware
from collections import defaultdict
from voiceops.api.schemas import FinalizeSessionRequest, FinalizeSessionResponse

LIVE_SESSIONS = defaultdict(lambda: {
    "raw_parts": [],
    "normalized_parts": []
})

MAX_SESSIONS = 50

app = FastAPI(title="VoiceOps API")
transcriber = Transcriber(model_size="base")


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/finalize-session", response_model=FinalizeSessionResponse)
async def finalize_session(payload: FinalizeSessionRequest):
    session_id = payload.session_id

    if session_id not in LIVE_SESSIONS:
        return {
            "session_id": session_id,
            "normalized_transcript": "",
            "corrected_transcript": "",
            "corrections": [],
            "extraction": {},
            "redaction": {},
            "summary": {}
        }

    normalized_transcript = " ".join(
        LIVE_SESSIONS[session_id]["normalized_parts"]
    ).strip()

    correction_result = correct_transcript_with_gated_retrieval(normalized_transcript)
    corrected_transcript = correction_result["corrected_text"]
    corrections = correction_result["corrections"]

    extraction = extract_entities(corrected_transcript)
    redaction = redact_pii(corrected_transcript)
    summary = summarize_transcript(
        redacted_transcript=redaction["redacted_text"],
        audience=payload.audience,
    )

    return {
        "session_id": session_id,
        "normalized_transcript": normalized_transcript,
        "corrected_transcript": corrected_transcript,
        "corrections": corrections,
        "extraction": extraction,
        "redaction": redaction,
        "summary": summary,
    }

@app.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(file: UploadFile = File(...)):
    suffix = os.path.splitext(file.filename)[1] or ".wav"

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        raw_path = tmp.name

    raw_text = transcriber.transcribe(raw_path)
    normalized = normalize_transcript(raw_text)

    correction_result = correct_transcript_with_gated_retrieval(normalized)
    corrected_text = correction_result["corrected_text"]

    extraction = extract_entities(corrected_text)

    return {
        "raw_transcript": raw_text,
        "corrected_transcript": corrected_text,
        "corrections": correction_result["corrections"],
        "extraction": extraction,
    }

@app.post("/transcribe-chunk", response_model=ChunkTranscriptionResponse)
async def transcribe_chunk(
    file: UploadFile = File(...),
    session_id: str = Form(None),
    chunk_index: int = Form(0),
):
    if not session_id:
        session_id = str(uuid.uuid4())

    suffix = os.path.splitext(file.filename)[1] or ".wav"

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_in:
        content = await file.read()
        tmp_in.write(content)
        input_path = tmp_in.name

    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_out:
        output_path = tmp_out.name

    preprocess_audio(
        input_path=input_path,
        output_path=output_path,
        target_sr=16000,
        apply_denoise=True,
        apply_normalize=True,
    )

    raw_text = transcriber.transcribe(output_path)
    normalized_text = normalize_transcript(raw_text)

    if session_id not in LIVE_SESSIONS:
        LIVE_SESSIONS[session_id] = {
            "raw_parts": [],
            "normalized_parts": []
        }

    LIVE_SESSIONS[session_id]["raw_parts"].append(raw_text)
    LIVE_SESSIONS[session_id]["normalized_parts"].append(normalized_text)

    if len(LIVE_SESSIONS) > MAX_SESSIONS:
        oldest_key = next(iter(LIVE_SESSIONS))
        del LIVE_SESSIONS[oldest_key]

    extraction = extract_entities(normalized_text)

    return {
        "session_id": session_id,
        "chunk_index": chunk_index,
        "raw_chunk_transcript": raw_text,
        "corrected_chunk_transcript": normalized_text,
        "session_raw_transcript": " ".join(LIVE_SESSIONS[session_id]["raw_parts"]),
        "session_corrected_transcript": " ".join(LIVE_SESSIONS[session_id]["normalized_parts"]),
        "extraction": extraction,
        "corrections": []
    }

@app.post("/preprocess-transcribe", response_model=TranscriptionResponse)
async def preprocess_and_transcribe(file: UploadFile = File(...)):
    suffix = os.path.splitext(file.filename)[1] or ".wav"

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_in:
        content = await file.read()
        tmp_in.write(content)
        input_path = tmp_in.name

    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_out:
        output_path = tmp_out.name

    preprocess_audio(
        input_path=input_path,
        output_path=output_path,
        target_sr=16000,
        apply_denoise=True,
        apply_normalize=True,
    )

    raw_text = transcriber.transcribe(output_path)
    normalized = normalize_transcript(raw_text)
    correction_result = correct_transcript_with_gated_retrieval(normalized)
    corrected_text = correction_result["corrected_text"]

    extraction = extract_entities(corrected_text)

    return {
        "raw_transcript": raw_text,
        "corrected_transcript": corrected_text,
        "corrections": correction_result["corrections"],
        "extraction": extraction,
    }


@app.post("/redact", response_model=RedactionResponse)
async def redact_endpoint(payload: SummaryRequest):
    result = redact_pii(payload.transcript)
    return result


@app.post("/summarize", response_model=SummaryResponse)
async def summarize_endpoint(payload: SummaryRequest):
    redaction = redact_pii(payload.transcript)
    summary = summarize_transcript(
        redacted_transcript=redaction["redacted_text"],
        audience=payload.audience,
    )
    return summary


@app.post("/evaluate", response_model=EvaluationResponse)
async def evaluate_audio(
    file: UploadFile = File(...),
    reference_text: str = File(...)
):
    suffix = os.path.splitext(file.filename)[1] or ".wav"

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    hypothesis = transcriber.transcribe(tmp_path)

    return {
        "wer": wer(reference_text, hypothesis),
        "cer": cer(reference_text, hypothesis),
        "keyword_accuracy": 0.0,
        "numeric_accuracy": 0.0,
        "negation_accuracy": 0.0,
        "details": {
            "reference": reference_text,
            "hypothesis": hypothesis
        }
    }
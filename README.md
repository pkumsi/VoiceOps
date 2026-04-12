# VoiceOps

VoiceOps is a real-time clinical voice assistant that converts raw audio into structured, privacy-safe medical summaries.  
The system is designed to be robust to noisy environments and domain-specific transcription errors, with a focus on safety and interpretability.

In real-world healthcare settings, clinicians often rely on voice notes or live conversations to capture patient information. However, automatic speech recognition systems frequently struggle with:
- medical terminology (e.g., “lisinopril” misheard as “liz and opryl”)
- numeric accuracy (e.g., “fifteen” vs “fifty”)
- negations (e.g., “no chest pain” vs “chest pain”)
- noisy environments such as clinics, calls, or crowded spaces

These errors are not just inconvenient — they can lead to incorrect clinical understanding, unsafe decisions, and loss of trust in automated systems.

VoiceOps addresses this by combining:
- real-time transcription for low-latency interaction
- domain-aware correction using retrieval and a learned gating model
- structured extraction of clinically relevant entities
- privacy-first redaction before any downstream processing
- controlled summarization tailored for clinician or patient use

The system is built with a core focus on:
- **robustness** to noisy and imperfect input  
- **safety** through guarded correction and PII handling  
- **interpretability**, ensuring every correction and decision can be inspected  

VoiceOps is not just a transcription tool — it is a reliability layer on top of speech systems for high-stakes domains like healthcare.
---
## Demo Video
https://www.youtube.com/watch?v=RgzeLhEI9T8&t=18s

## Hosted Website
https://voice-ops-virid.vercel.app/

---
## Overview

VoiceOps processes clinical speech through a multi-stage pipeline:

1. Speech-to-text transcription using Whisper
2. Text normalization and cleanup
3. Domain-specific correction using retrieval and a learned gating model
4. Entity extraction (medications, symptoms, dosages)
5. PII redaction before any LLM interaction
6. Structured summary generation for clinician or patient audiences

The system supports both live streaming transcription and post-session correction.

---

## Key Features

### Real-time transcription
- Chunked audio processing (2–5 seconds)
- Low-latency Whisper inference
- Session-level transcript accumulation

### Domain-aware correction
- n-gram candidate generation from transcript spans
- Ranking using:
  - semantic similarity (embeddings)
  - fuzzy string matching
  - phonetic similarity
- Logistic regression gate to prevent unsafe corrections

### Privacy-first design
- Redacts:
  - SSN (including partial and spoken forms)
  - phone numbers
  - email
  - DOB
  - MRN
- Redaction occurs before LLM usage

### Structured summarization
- Generates clinician or patient summaries
- Extracts:
  - medications
  - symptoms
  - dosages
  - follow-up steps
- Enforces strict JSON output and parsing

### Benchmarking framework
- Evaluates across multiple conditions:
  - clean
  - telephony
  - noisy
  - synthetic school-noise
- Metrics:
  - WER / CER
  - keyword accuracy
  - numeric accuracy
  - negation accuracy
- Includes ablation study:
  - Baseline 0: raw Whisper
  - Baseline 1: normalization
  - Baseline 2: retrieval (ungated)
  - Baseline 3: gated retrieval

---

## System Architecture

### Live pipeline (low latency)
Audio → Whisper → Normalize → Live Transcript



### Finalization pipeline (high accuracy)
Session Transcript
→ Retrieval (n-gram candidates)
→ Gating Model (Logistic Regression)
→ Corrected Transcript
→ PII Redaction
→ LLM Summary


---

## Project Structure

voiceops/
api/ # FastAPI endpoints
pipeline/ # transcription + correction pipeline
models/
retriever/ # candidate ranking
detectors/ # gating model
extraction/ # entity extraction + summarization
eval/ # evaluation + ablation scripts
benchmark/
audio/ # datasets (clean, noisy, etc.)
scripts/ # dataset generation utilities

frontend/
src/
components/ # UI components
api/ # API client

---

## Setup

### 1. Clone repository

git clone https://github.com/pkumsi/VoiceOps.git

cd VoiceOps


### 2. Create virtual environment

python -m venv .venv
source .venv/bin/activate


### 3. Install dependencies

pip install -r requirements.txt


### 4. Environment variables
Create `.env`:

OPENROUTER_API_KEY=your_key

SUMMARY_PROVIDER=openrouter


---

## Running the backend

API runs at: http://127.0.0.1:8000

---

## Running the frontend

cd frontend
npm install
npm run dev


Frontend runs at: http://localhost:3000


---

## API Endpoints

### POST `/transcribe-chunk`
Processes short audio chunks for live transcription.

**Input**
- multipart/form-data
  - file
  - session_id
  - chunk_index

**Output**
- raw transcript
- session transcript
- extracted entities

---

### POST `/finalize-session`
Runs full correction + redaction + extraction on session transcript.

---

### POST `/redact`
Redacts PII from transcript.

---

### POST `/summarize`
Generates structured summary.

**Input**

{
"transcript": "...",
"audience": "clinician" | "patient"
}


---

## Evaluation

Run baseline evaluation:


python -m voiceops.eval.run_eval


Run ablation study:
python -m voiceops.eval.ablation


---

## Example Failure Modes

- Medical term fragmentation (e.g. "lisinopril" → "liz and opryl")
- Numeric ambiguity ("fifty" vs "fifteen")
- Negation sensitivity ("not taking insulin")

The gated retrieval model is designed to correct domain terms while avoiding unsafe edits.

---

## Future Work

- Speaker diarization for multi-party conversations
- Streaming ASR with overlap-aware decoding
- Fine-tuned medical ASR models
- More robust PII detection (credit cards, addresses)
- Improved denoising and reverberation modeling

---

## Notes

- Live mode prioritizes latency and does not apply retrieval correction
- Full correction is applied only after session finalization
- Audio datasets are not included in the repository due to size

---



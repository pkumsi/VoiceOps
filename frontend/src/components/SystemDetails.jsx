import { useState } from 'react'

// Two separate pipelines reflecting actual system behavior
const LIVE_PIPELINE = [
  { label: 'Audio Input',        color: 'bg-slate-100 text-slate-700 border-slate-200' },
  { label: 'Whisper',            color: 'bg-blue-50 text-blue-700 border-blue-100' },
  { label: 'Normalize',          color: 'bg-purple-50 text-purple-700 border-purple-100' },
  { label: 'Live Transcript',    color: 'bg-emerald-50 text-emerald-700 border-emerald-100' },
]

const FINALIZATION_PIPELINE = [
  { label: 'Session Transcript', color: 'bg-slate-100 text-slate-700 border-slate-200' },
  { label: 'Retrieval',          color: 'bg-cyan-50 text-cyan-700 border-cyan-100' },
  { label: 'Gate',               color: 'bg-amber-50 text-amber-700 border-amber-100' },
  { label: 'Final Transcript',   color: 'bg-emerald-50 text-emerald-700 border-emerald-100' },
  { label: 'Redaction',          color: 'bg-red-50 text-red-700 border-red-100' },
  { label: 'Summary',            color: 'bg-indigo-50 text-indigo-700 border-indigo-100' },
]

const DESIGN_NOTES = [
  {
    title: 'Benchmark Design',
    body: '30+ synthesized VOX samples spanning 4 audio conditions (clean, telephony 8 kHz, telephony noise, telephony echo) and 3 accent profiles (General American, Indian English, Nigerian/British English). Ground truth consists of manually verified clinical phrases covering medications, dosages, negations, and numeric values.',
  },
  {
    title: 'n-gram Retrieval Correction',
    body: 'At finalization, candidate n-gram spans from a domain vocabulary (medications, symptoms) are scored against the session transcript using fuzzy string similarity (RapidFuzz), phonetic similarity (Metaphone/Soundex), and embedding-based semantic similarity. A correction is proposed when the combined similarity score exceeds a configurable threshold. This is Baseline 2.',
  },
  {
    title: 'Logistic Regression Gate',
    body: 'A logistic regression classifier (Baseline 3) gates retrieval corrections before they are applied. Input features include: fuzzy score, semantic score, phonetic score, span length, stopword presence, and digit presence in the span. The gate blocks corrections that are likely to introduce clinical errors — such as negation loss or numeric substitution.',
  },
  {
    title: 'Denoise Preprocessing',
    body: 'Optional preprocessing step: audio is resampled to 16 kHz and passed through a spectral gating denoiser, followed by amplitude normalization. This can improve Whisper accuracy on telephony and noisy inputs. It is available as a toggle in the UI and applied server-side via the /transcribe-chunk endpoint when enabled.',
  },
  {
    title: 'Near-Live Chunked Transcription',
    body: 'The frontend records audio in 4-second cycles using the MediaRecorder API. Each completed chunk is sent to POST /transcribe-chunk with a stable session_id. The backend applies Whisper transcription and text normalization only — retrieval and gating are deferred to the finalization step. The UI displays the normalized live transcript as chunks arrive.',
  },
]

function CollapseIcon({ open }) {
  return (
    <svg className={`w-5 h-5 text-slate-400 transition-transform ${open ? 'rotate-180' : ''}`}
      fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
    </svg>
  )
}

function PipelineRow({ steps }) {
  return (
    <div className="flex items-center gap-0 min-w-max">
      {steps.map((step, i) => (
        <div key={i} className="flex items-center">
          <div className={`rounded-lg px-3 py-2 border text-xs font-semibold whitespace-nowrap ${step.color}`}>
            {step.label}
          </div>
          {i < steps.length - 1 && (
            <div className="flex items-center px-1">
              <div className="h-px w-4 bg-slate-300" />
              <svg className="w-3 h-3 text-slate-300" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd"
                  d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z"
                  clipRule="evenodd" />
              </svg>
            </div>
          )}
        </div>
      ))}
    </div>
  )
}

export default function SystemDetails() {
  const [open, setOpen] = useState(false)

  return (
    <div className="card">
      <button
        className="w-full flex items-center justify-between"
        onClick={() => setOpen(v => !v)}
      >
        <div className="flex items-center gap-2">
          <span className="card-title mb-0">System Architecture</span>
          <span className="badge bg-slate-100 text-slate-500">2 pipelines · design notes</span>
        </div>
        <CollapseIcon open={open} />
      </button>

      {open && (
        <div className="mt-5 space-y-8">

          {/* ── Pipelines ── */}
          <div className="space-y-5">
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Pipelines</p>

            <div className="space-y-3">
              <div>
                <p className="text-xs font-medium text-slate-500 mb-2">Live (per chunk)</p>
                <div className="overflow-x-auto pb-1">
                  <PipelineRow steps={LIVE_PIPELINE} />
                </div>
              </div>

              <div>
                <p className="text-xs font-medium text-slate-500 mb-2">Finalization (on stop)</p>
                <div className="overflow-x-auto pb-1">
                  <PipelineRow steps={FINALIZATION_PIPELINE} />
                </div>
              </div>
            </div>
          </div>

          {/* ── Design Notes ── */}
          <div>
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">Design Notes</p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {DESIGN_NOTES.map((d, i) => (
                <div key={i} className="rounded-xl bg-slate-50 border border-slate-200 px-4 py-3">
                  <p className="font-semibold text-sm text-slate-800 mb-1.5">{d.title}</p>
                  <p className="text-xs text-slate-600 leading-relaxed">{d.body}</p>
                </div>
              ))}
            </div>
          </div>

        </div>
      )}
    </div>
  )
}

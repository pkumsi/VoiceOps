import { useState } from 'react'
import { summarize, redact } from '../api/client'

export default function SummarySection({ correctedTranscript, onError }) {
  const [audience, setAudience] = useState('clinician')
  const [summaryResult, setSummaryResult] = useState(null)
  const [redactionResult, setRedactionResult] = useState(null)
  const [loadingSummary, setLoadingSummary] = useState(false)
  const [loadingRedact, setLoadingRedact] = useState(false)
  const [approvalStatus, setApprovalStatus] = useState(null) // 'approved'|'editing'|'rejected'
  const [debugOpen, setDebugOpen] = useState(false)

  const handleRedact = async () => {
    if (!correctedTranscript) return onError('No transcript to redact')
    setLoadingRedact(true)
    try {
      const result = await redact(correctedTranscript)
      setRedactionResult(result)
    } catch (err) {
      onError(err.message)
    } finally {
      setLoadingRedact(false)
    }
  }

  const handleSummarize = async () => {
    if (!correctedTranscript) return onError('No transcript to summarize')
    setLoadingSummary(true)
    setApprovalStatus(null)
    try {
      const result = await summarize(correctedTranscript, audience)
      setSummaryResult(result)
    } catch (err) {
      onError(err.message)
    } finally {
      setLoadingSummary(false)
    }
  }

  const noTranscript = !correctedTranscript
  // Summarize is most useful after redaction, but allow it directly too
  const summaryReady = !!redactionResult

  return (
    <div className="card space-y-6">
      <p className="card-title">Post-Processing</p>

      {/* ── Audience toggle ── */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="flex items-center gap-1 bg-slate-100 rounded-xl p-1">
          {['clinician', 'patient'].map(a => (
            <button
              key={a}
              onClick={() => setAudience(a)}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-all capitalize ${
                audience === a
                  ? 'bg-white text-brand-700 shadow-sm'
                  : 'text-slate-500 hover:text-slate-700'
              }`}
            >
              {a}
            </button>
          ))}
        </div>
      </div>

      {/* ── Step flow ── */}
      <div className="space-y-5">

        {/* Step 1: Redaction */}
        <StepBlock
          step={1}
          label="Preview Redaction"
          description="Confirm PII is removed before generating the summary."
          active={!redactionResult}
          done={!!redactionResult}
        >
          <button
            className={redactionResult ? 'btn-secondary' : 'btn-primary'}
            onClick={handleRedact}
            disabled={noTranscript || loadingRedact}
          >
            {loadingRedact ? <Spinner /> : <RedactIcon />}
            {redactionResult ? 'Re-run Redaction' : 'Preview Redaction'}
          </button>
        </StepBlock>

        {/* Redacted transcript result */}
        {redactionResult && (
          <div className="ml-8 space-y-3">
            <div className="transcript-box text-xs">
              <RedactedText text={redactionResult.redacted_text} />
            </div>
            {redactionResult.redactions?.length > 0 && (
              <div className="space-y-1 max-h-28 overflow-y-auto">
                {redactionResult.redactions.map((r, i) => (
                  <div key={i} className="text-xs text-slate-600 bg-slate-50 rounded-lg px-2 py-1.5 flex items-center gap-2 border border-slate-100">
                    <span className="badge bg-slate-200 text-slate-600 shrink-0">{r.type || 'PII'}</span>
                    <span className="text-slate-400 line-through truncate">{r.original}</span>
                    <span className="text-slate-300 shrink-0">→</span>
                    <span className="font-mono text-slate-600 truncate">{r.replacement || '[REDACTED]'}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Connector arrow */}
        {redactionResult && (
          <div className="ml-8 flex items-center gap-2 text-slate-300">
            <div className="h-5 w-px bg-slate-200 ml-2" />
          </div>
        )}

        {/* Step 2: Summary */}
        <StepBlock
          step={2}
          label="Generate Summary"
          description="Structured clinical summary extracted from the redacted transcript."
          active={summaryReady && !summaryResult}
          done={!!summaryResult}
          dimmed={!summaryReady}
        >
          <button
            className={summaryResult ? 'btn-secondary' : 'btn-primary'}
            onClick={handleSummarize}
            disabled={noTranscript || loadingSummary}
          >
            {loadingSummary ? <Spinner /> : <SummaryIcon />}
            {summaryResult ? 'Regenerate Summary' : 'Generate Summary'}
          </button>
        </StepBlock>

        {/* Summary card result */}
        {summaryResult && (
          <div className="ml-8 space-y-4">
            <div className="flex items-center gap-2">
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                {capitalize(summaryResult.audience)} Summary
              </p>
              <span className="badge bg-slate-100 text-slate-500 capitalize">{summaryResult.provider}</span>
            </div>

            <PolishedSummaryCard result={summaryResult.result} />

            {/* Approval actions — directly below card */}
            {!approvalStatus
              ? (
                <div className="flex gap-2">
                  <button className="btn-success" onClick={() => setApprovalStatus('approved')}>
                    <CheckIcon /> Approve
                  </button>
                  <button className="btn-secondary" onClick={() => setApprovalStatus('editing')}>
                    <EditIcon /> Mark for Edit
                  </button>
                  <button className="btn-danger" onClick={() => setApprovalStatus('rejected')}>
                    <XIcon /> Reject
                  </button>
                </div>
              )
              : (
                <div className={`flex items-center gap-2 rounded-xl px-4 py-2.5 text-sm font-medium border
                  ${approvalStatus === 'approved'
                    ? 'bg-emerald-50 border-emerald-200 text-emerald-700'
                    : approvalStatus === 'rejected'
                    ? 'bg-red-50 border-red-200 text-red-700'
                    : 'bg-amber-50 border-amber-200 text-amber-700'}`}>
                  <span>
                    {approvalStatus === 'approved' && 'Approved'}
                    {approvalStatus === 'rejected' && 'Rejected'}
                    {approvalStatus === 'editing' && 'Marked for editing'}
                  </span>
                  <button
                    className="ml-auto text-xs underline opacity-60 hover:opacity-100 transition-opacity"
                    onClick={() => setApprovalStatus(null)}
                  >
                    Undo
                  </button>
                </div>
              )
            }

            {/* Debug accordion */}
            <div className="border border-slate-200 rounded-xl overflow-hidden">
              <button
                className="w-full flex items-center justify-between px-4 py-2.5 bg-slate-50 text-xs font-semibold text-slate-400 uppercase tracking-wider hover:bg-slate-100 transition-colors"
                onClick={() => setDebugOpen(v => !v)}
              >
                Debug Output
                <CollapseIcon open={debugOpen} />
              </button>
              {debugOpen && (
                <div className="px-4 py-3 bg-white">
                  <pre className="text-xs text-slate-500 font-mono whitespace-pre-wrap break-words max-h-60 overflow-y-auto">
                    {JSON.stringify(summaryResult.result, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

// ── Step Block ────────────────────────────────────────────────────────────────

function StepBlock({ step, label, description, active, done, dimmed, children }) {
  return (
    <div className={`flex gap-4 ${dimmed && !active && !done ? 'opacity-40' : ''}`}>
      {/* Step number */}
      <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold shrink-0 mt-0.5
        ${done
          ? 'bg-emerald-100 text-emerald-700'
          : active
          ? 'bg-brand-600 text-white'
          : 'bg-slate-200 text-slate-500'}`}>
        {done
          ? <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
            </svg>
          : step
        }
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex flex-wrap items-center gap-3 mb-1">
          <span className="font-semibold text-sm text-slate-800">{label}</span>
          {children}
        </div>
        <p className="text-xs text-slate-400">{description}</p>
      </div>
    </div>
  )
}

// ── Polished Summary Card ─────────────────────────────────────────────────────

function PolishedSummaryCard({ result }) {
  if (!result) return null
  if (typeof result === 'string') {
    return (
      <div className="rounded-xl border border-slate-300 bg-white p-5 shadow-sm">
        <p className="text-sm text-slate-700 leading-relaxed">{result}</p>
      </div>
    )
  }

  const r = result
  const riskFlag = r.risk_flag ?? r.risk
  const isRisky = riskFlag === true || riskFlag === 'true' || riskFlag === 'high' || riskFlag === 'yes'
  const hasRisk = riskFlag !== undefined && riskFlag !== null

  // Clinician returns `follow_up`; patient returns `next_steps`
  const followUp = r.follow_up ?? r.next_steps ?? null

  return (
    <div className="rounded-xl border border-slate-300 bg-white shadow-sm overflow-hidden">

      {/* Risk flag banner */}
      {hasRisk && (
        <div className={`px-5 py-3 flex items-center gap-3 border-b
          ${isRisky ? 'bg-red-50 border-red-200' : 'bg-emerald-50 border-emerald-200'}`}>
          <span className={`inline-block w-2.5 h-2.5 rounded-full shrink-0
            ${isRisky ? 'bg-red-500' : 'bg-emerald-500'}`}
          />
          <p className={`font-semibold text-sm ${isRisky ? 'text-red-700' : 'text-emerald-700'}`}>
            {isRisky ? 'Risk Flagged — Review Required' : 'No Risk Detected'}
          </p>
        </div>
      )}

      <div className="divide-y divide-slate-100">

        {/* Narrative summary — full-width, prominent */}
        {r.summary && (
          <div className="px-5 py-4">
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Summary</p>
            <p className="text-base text-slate-800 leading-relaxed font-medium">{r.summary}</p>
          </div>
        )}

        {/* Medications */}
        <SummaryRow label="Medications">
          <TagList items={r.medications} emptyLabel="None mentioned" />
        </SummaryRow>

        {/* Symptoms */}
        <SummaryRow label="Symptoms">
          <TagList items={r.symptoms} emptyLabel="None mentioned" />
        </SummaryRow>

        {/* Dosages */}
        <SummaryRow label="Dosages">
          <TagList items={r.dosages} emptyLabel="None specified" />
        </SummaryRow>

        {/* Follow-up / Next Steps */}
        {followUp !== null && followUp !== undefined && (
          <SummaryRow label="Next Steps">
            <BulletList items={followUp} emptyLabel="None specified" />
          </SummaryRow>
        )}

      </div>
    </div>
  )
}

function SummaryRow({ label, children }) {
  return (
    <div className="px-5 py-3 flex gap-5">
      <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider w-24 shrink-0 pt-1">{label}</p>
      <div className="flex-1 min-w-0">{children}</div>
    </div>
  )
}

function TagList({ items, emptyLabel }) {
  const list = normalizeList(items)
  if (!list.length) return <span className="text-sm text-slate-400 italic">{emptyLabel}</span>
  return (
    <div className="flex flex-wrap gap-1.5">
      {list.map((item, i) => (
        <span key={i} className="inline-block px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-700 text-sm font-medium">
          {item}
        </span>
      ))}
    </div>
  )
}

function BulletList({ items, emptyLabel }) {
  const list = normalizeList(items)
  if (!list.length) return <span className="text-sm text-slate-400 italic">{emptyLabel}</span>
  if (list.length === 1) return <p className="text-sm text-slate-700">{list[0]}</p>
  return (
    <ul className="space-y-1">
      {list.map((item, i) => (
        <li key={i} className="flex items-start gap-2 text-sm text-slate-700">
          <span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-slate-400 shrink-0" />
          {item}
        </li>
      ))}
    </ul>
  )
}

/** Safely coerce a field value to a string array. */
function normalizeList(value) {
  if (!value) return []
  if (Array.isArray(value)) return value.filter(Boolean).map(String)
  if (typeof value === 'string') {
    if (value.includes(',')) return value.split(',').map(s => s.trim()).filter(Boolean)
    return value.trim() ? [value.trim()] : []
  }
  return [String(value)]
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function RedactedText({ text }) {
  if (!text) return null
  const parts = text.split(/(\[.*?\])/g)
  return (
    <>
      {parts.map((part, i) =>
        part.startsWith('[') && part.endsWith(']')
          ? <mark key={i} className="bg-orange-100 text-orange-700 rounded px-0.5">{part}</mark>
          : <span key={i}>{part}</span>
      )}
    </>
  )
}

function CollapseIcon({ open }) {
  return (
    <svg className={`w-4 h-4 transition-transform ${open ? 'rotate-180' : ''}`}
      fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
    </svg>
  )
}

function Spinner() {
  return (
    <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
    </svg>
  )
}

function RedactIcon() {
  return (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
        d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
    </svg>
  )
}

function SummaryIcon() {
  return (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
        d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
    </svg>
  )
}

function CheckIcon() {
  return (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
    </svg>
  )
}

function EditIcon() {
  return (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
        d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
    </svg>
  )
}

function XIcon() {
  return (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
    </svg>
  )
}

function capitalize(str) {
  return str ? str.charAt(0).toUpperCase() + str.slice(1) : ''
}

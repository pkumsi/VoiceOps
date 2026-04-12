/**
 * Highlights corrected spans in the final transcript using the corrections list.
 */
function highlightCorrections(text, corrections) {
  if (!corrections?.length || !text) return [{ text, highlighted: false }]

  const markers = []
  corrections.forEach(c => {
    if (c.corrected && text.toLowerCase().includes(c.corrected.toLowerCase())) {
      const idx = text.toLowerCase().indexOf(c.corrected.toLowerCase())
      markers.push({ start: idx, end: idx + c.corrected.length, label: c.type || 'correction', reason: c.reason })
    }
  })
  markers.sort((a, b) => a.start - b.start)

  let pos = 0
  const parts = []
  for (const m of markers) {
    if (m.start > pos) parts.push({ text: text.slice(pos, m.start), highlighted: false })
    parts.push({ text: text.slice(m.start, m.end), highlighted: true, label: m.label, reason: m.reason })
    pos = m.end
  }
  if (pos < text.length) parts.push({ text: text.slice(pos), highlighted: false })
  return parts.length ? parts : [{ text, highlighted: false }]
}

export default function TranscriptPanel({
  rawTranscript, correctedTranscript, corrections, isProcessing, isRecording, transcriptSource,
}) {
  const correctedParts = highlightCorrections(correctedTranscript, corrections)

  // Show the corrected transcript only for file uploads — not for live recording.
  const showCorrected = transcriptSource === 'upload' && !!correctedTranscript

  return (
    <div className="card flex-1 min-w-0">
      <p className="card-title">Transcripts</p>

      <div className="space-y-4">
        {/* Raw Whisper Output */}
        <div>
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-xs font-semibold text-slate-500">Raw Whisper Output</span>
            {isProcessing && <ProcessingBadge />}
          </div>
          <div className="transcript-box">
            {rawTranscript
              ? rawTranscript
              : <span className="text-slate-400 italic">Waiting for audio...</span>
            }
          </div>
          {isRecording && (
            <p className="text-xs text-slate-400 mt-1.5">
              Live mode applies Whisper with lightweight normalization server-side.
              Full domain correction runs after recording stops.
            </p>
          )}
        </div>

        {/* Final Corrected Transcript — shown only after recording stops */}
        {showCorrected && (
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-xs font-semibold text-slate-500">Final Corrected Transcript</span>
              {corrections?.length > 0 && (
                <span className="badge bg-slate-200 text-slate-600">
                  {corrections.length} correction{corrections.length !== 1 ? 's' : ''}
                </span>
              )}
            </div>
            <div className="transcript-box">
              {correctedParts.map((part, i) =>
                part.highlighted
                  ? (
                    <mark
                      key={i}
                      title={part.reason ? `${part.label}: ${part.reason}` : part.label}
                      className="bg-blue-100 text-blue-800 rounded px-0.5 cursor-help"
                    >
                      {part.text}
                    </mark>
                  )
                  : <span key={i}>{part.text}</span>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

function ProcessingBadge() {
  return (
    <span className="inline-flex items-center gap-1 text-xs text-brand-600 font-medium">
      <svg className="w-3 h-3 animate-spin" fill="none" viewBox="0 0 24 24">
        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
      </svg>
      Processing
    </span>
  )
}

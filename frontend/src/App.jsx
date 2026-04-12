import { useState, useCallback } from 'react'
import Header from './components/Header'
import RecordingSection from './components/RecordingSection'
import TranscriptPanel from './components/TranscriptPanel'
import InsightsPanel from './components/InsightsPanel'
import SummarySection from './components/SummarySection'
import BenchmarkSection from './components/BenchmarkSection'
import SystemDetails from './components/SystemDetails'

export default function App() {
  // ── Transcript state ──────────────────────────────────────────────────────
  const [rawTranscript, setRawTranscript] = useState('')
  const [correctedTranscript, setCorrectedTranscript] = useState('')
  const [extraction, setExtraction] = useState(null)
  const [corrections, setCorrections] = useState([])

  // ── UI state ──────────────────────────────────────────────────────────────
  const [isRecording, setIsRecording] = useState(false)
  const [transcriptSource, setTranscriptSource] = useState(null) // 'upload' | 'recording'
  const [isProcessing, setIsProcessing] = useState(false)
  const [error, setError] = useState(null)

  // Called by RecordingSection after each successful /transcribe-chunk response
  const handleChunkResult = useCallback((result) => {
    // Prefer session-level accumulated transcripts; fall back to chunk-level
    setRawTranscript(result.session_raw_transcript ?? result.raw_chunk_transcript ?? '')
    setCorrectedTranscript(result.session_corrected_transcript ?? result.corrected_chunk_transcript ?? '')
    if (result.extraction) setExtraction(result.extraction)
    if (result.corrections) setCorrections(result.corrections)
    setTranscriptSource(result._source === 'upload' ? 'upload' : 'recording')
    setError(null)
  }, [])

  const handleError = useCallback((msg) => {
    setError(msg)
  }, [])

  const dismissError = () => setError(null)

  return (
    <div className="min-h-screen flex flex-col">
      <Header />

      <main className="flex-1 max-w-7xl mx-auto w-full px-4 sm:px-6 py-6 space-y-5">

        {/* Error banner */}
        {error && (
          <div className="flex items-start gap-3 bg-red-50 border border-red-200 rounded-2xl px-5 py-4 text-red-700">
            <svg className="w-5 h-5 mt-0.5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <div className="flex-1 min-w-0">
              <p className="font-semibold text-sm">Error</p>
              <p className="text-sm mt-0.5 opacity-80 break-words">{error}</p>
            </div>
            <button
              onClick={dismissError}
              className="text-red-400 hover:text-red-600 transition-colors ml-2 mt-0.5"
              aria-label="Dismiss error"
            >
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd"
                  d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                  clipRule="evenodd" />
              </svg>
            </button>
          </div>
        )}

        {/* ── Section 1: Recording ── */}
        <RecordingSection
          onChunkResult={handleChunkResult}
          onError={handleError}
          isProcessing={isProcessing}
          setIsProcessing={setIsProcessing}
          onRecordingChange={setIsRecording}
        />

        {/* ── Section 2: Transcripts + Insights ── */}
        <div className="flex flex-col lg:flex-row gap-5">
          <TranscriptPanel
            rawTranscript={rawTranscript}
            correctedTranscript={correctedTranscript}
            corrections={corrections}
            isProcessing={isProcessing}
            isRecording={isRecording}
            transcriptSource={transcriptSource}
          />
          <InsightsPanel
            extraction={extraction}
            corrections={corrections}
          />
        </div>

        {/* ── Section 3: Summary & Redaction ── */}
        <SummarySection
          correctedTranscript={correctedTranscript}
          onError={handleError}
        />

        {/* ── Section 4: Benchmark (collapsed) ── */}
        <BenchmarkSection />

        {/* ── Section 5: System Details (collapsed) ── */}
        <SystemDetails />

      </main>

      <footer className="border-t border-slate-200 bg-white py-4 mt-4">
        <p className="text-center text-xs text-slate-400">
          VoiceOps · Healthcare Voice Intelligence ·{' '}
          <span className="font-mono">api: 127.0.0.1:8000</span>
        </p>
      </footer>
    </div>
  )
}

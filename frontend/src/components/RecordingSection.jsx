import { useRef, useState, useEffect, useCallback } from 'react'
import { v4 as uuidv4 } from 'uuid'
import { transcribeChunk, transcribeFile } from '../api/client'

const CHUNK_INTERVAL_MS = 4000

export default function RecordingSection({ onChunkResult, onError, isProcessing, setIsProcessing, onRecordingChange }) {
  const [isRecording, setIsRecording] = useState(false)
  const [applyDenoise, setApplyDenoise] = useState(true)
  const [uploadLoading, setUploadLoading] = useState(false)

  const mediaRecorderRef = useRef(null)
  const sessionIdRef = useRef(null)
  const chunkIndexRef = useRef(0)
  const intervalRef = useRef(null)
  const streamRef = useRef(null)
  const chunksRef = useRef([])

  const sendCurrentChunk = useCallback(async (blob) => {
    if (!blob || blob.size === 0) return
    try {
      const result = await transcribeChunk(blob, sessionIdRef.current, chunkIndexRef.current)
      chunkIndexRef.current += 1
      onChunkResult(result)
    } catch (err) {
      onError(err.message)
    }
  }, [onChunkResult, onError])

  const startNewRecorderCycle = useCallback(() => {
    if (!streamRef.current) return

    // Collect audio formats supported by this browser
    const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
      ? 'audio/webm;codecs=opus'
      : 'audio/webm'

    const recorder = new MediaRecorder(streamRef.current, { mimeType })
    chunksRef.current = []

    recorder.ondataavailable = (e) => {
      if (e.data.size > 0) chunksRef.current.push(e.data)
    }

    recorder.onstop = () => {
      const blob = new Blob(chunksRef.current, { type: mimeType })
      sendCurrentChunk(blob)
    }

    recorder.start()
    mediaRecorderRef.current = recorder
  }, [sendCurrentChunk])

  const startRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      streamRef.current = stream
      sessionIdRef.current = uuidv4()
      chunkIndexRef.current = 0

      startNewRecorderCycle()
      setIsRecording(true)
      onRecordingChange?.(true)

      // Every CHUNK_INTERVAL_MS, stop current recorder (triggers onstop → send) and start new one
      intervalRef.current = setInterval(() => {
        if (mediaRecorderRef.current?.state === 'recording') {
          mediaRecorderRef.current.stop()
        }
        startNewRecorderCycle()
      }, CHUNK_INTERVAL_MS)
    } catch (err) {
      onError('Microphone access denied: ' + err.message)
    }
  }, [startNewRecorderCycle, onError])

  const stopRecording = useCallback(() => {
    clearInterval(intervalRef.current)
    if (mediaRecorderRef.current?.state === 'recording') {
      mediaRecorderRef.current.stop()
    }
    streamRef.current?.getTracks().forEach(t => t.stop())
    streamRef.current = null
    setIsRecording(false)
    onRecordingChange?.(false)
  }, [onRecordingChange])

  // Cleanup on unmount
  useEffect(() => () => stopRecording(), [stopRecording])

  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    setUploadLoading(true)
    setIsProcessing(true)
    try {
      // File upload goes through /transcribe (single file, no session chunks)
      const result = await transcribeFile(file)
      // Wrap into ChunkTranscriptionResponse shape for uniform handling
      onChunkResult({
        session_id: uuidv4(),
        chunk_index: 0,
        raw_chunk_transcript: result.raw_transcript,
        corrected_chunk_transcript: result.corrected_transcript,
        session_raw_transcript: result.raw_transcript,
        session_corrected_transcript: result.corrected_transcript,
        extraction: result.extraction,
        corrections: result.corrections,
        _source: 'upload',
      })
    } catch (err) {
      onError(err.message)
    } finally {
      setUploadLoading(false)
      setIsProcessing(false)
      e.target.value = ''
    }
  }

  return (
    <div className="card">
      <p className="card-title">Recording & Input</p>

      <div className="flex flex-wrap items-center gap-3">
        {/* Recording dot indicator */}
        {isRecording && (
          <div className="flex items-center gap-2 mr-1">
            <span className="relative flex h-3 w-3">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-3 w-3 bg-red-500" />
            </span>
            <span className="text-xs text-red-600 font-semibold">Recording</span>
          </div>
        )}

        <button
          className="btn-primary"
          onClick={startRecording}
          disabled={isRecording || isProcessing}
        >
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
            <path d="M12 15a3 3 0 003-3V6a3 3 0 00-6 0v6a3 3 0 003 3z" />
            <path fillRule="evenodd" d="M5.5 10.5a.5.5 0 01.5.5 6 6 0 0012 0 .5.5 0 011 0A7 7 0 0112.5 17.93V20h2a.5.5 0 010 1h-5a.5.5 0 010-1h2v-2.07A7 7 0 015 11a.5.5 0 01.5-.5z" />
          </svg>
          Start Recording
        </button>

        <button
          className="btn-danger"
          onClick={stopRecording}
          disabled={!isRecording}
        >
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
            <rect x="6" y="6" width="12" height="12" rx="2" />
          </svg>
          Stop Recording
        </button>

        {/* File upload */}
        <label className={`btn-secondary cursor-pointer ${uploadLoading ? 'opacity-40 pointer-events-none' : ''}`}>
          {uploadLoading
            ? <Spinner />
            : (
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
              </svg>
            )
          }
          Upload Audio
          <input
            type="file"
            accept="audio/*"
            className="hidden"
            onChange={handleFileUpload}
            disabled={isRecording || uploadLoading}
          />
        </label>

        {/* Denoise toggle */}
        <label className="flex items-center gap-2 ml-auto cursor-pointer select-none">
          <span className="text-sm text-slate-600 font-medium">Denoise</span>
          <button
            type="button"
            role="switch"
            aria-checked={applyDenoise}
            onClick={() => setApplyDenoise(v => !v)}
            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none
              ${applyDenoise ? 'bg-brand-600' : 'bg-slate-300'}`}
          >
            <span className={`inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform
              ${applyDenoise ? 'translate-x-6' : 'translate-x-1'}`}
            />
          </button>
        </label>
      </div>

      <p className="mt-3 text-xs text-slate-400">
        Audio is chunked every 4 s and transcribed in near-real-time using Whisper + normalization.
        Retrieval correction and gating run at finalization, after recording stops.
      </p>
    </div>
  )
}

function Spinner() {
  return (
    <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
    </svg>
  )
}

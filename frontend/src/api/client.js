// All requests target the FastAPI backend running locally.
// const BASE_URL = 'http://127.0.0.1:8000'
const BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';
async function handleResponse(res) {
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText)
    throw new Error(`API ${res.status}: ${text}`)
  }
  return res.json()
}

/**
 * POST /transcribe-chunk
 * Sends a single audio blob chunk for transcription.
 * @param {Blob} audioBlob
 * @param {string} sessionId
 * @param {number} chunkIndex
 */
export async function transcribeChunk(audioBlob, sessionId, chunkIndex) {
  const form = new FormData()
  form.append('file', audioBlob, `chunk_${chunkIndex}.webm`)
  form.append('session_id', sessionId)
  form.append('chunk_index', String(chunkIndex))

  const res = await fetch(`${BASE_URL}/transcribe-chunk`, {
    method: 'POST',
    body: form,
  })
  return handleResponse(res)
}

/**
 * POST /transcribe (single file upload)
 * @param {File} file
 */
export async function transcribeFile(file) {
  const form = new FormData()
  form.append('file', file)

  const res = await fetch(`${BASE_URL}/transcribe`, {
    method: 'POST',
    body: form,
  })
  return handleResponse(res)
}

/**
 * POST /summarize
 * @param {string} transcript
 * @param {'clinician'|'patient'} audience
 */
export async function summarize(transcript, audience = 'clinician') {
  const res = await fetch(`${BASE_URL}/summarize`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ transcript, audience }),
  })
  return handleResponse(res)
}

/**
 * POST /redact
 * @param {string} transcript
 */
export async function redact(transcript) {
  const res = await fetch(`${BASE_URL}/redact`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ transcript, audience: 'clinician' }),
  })
  return handleResponse(res)
}

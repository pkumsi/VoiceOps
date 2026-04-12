import { useState } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts'

// Aggregate results from the offline eval run (voiceops/eval/run_eval.py).
const BASELINES = {
  baseline_0_raw:             { label: 'B0: Raw Whisper',     wer: 0.3706, cer: 0.2228, keyword_acc: 0.6042, numeric_acc: 0.875,  negation_acc: 0.9167 },
  baseline_1_normalized:      { label: 'B1: Normalized',      wer: 0.3239, cer: 0.1489, keyword_acc: 0.6319, numeric_acc: 0.875,  negation_acc: 0.9167 },
  baseline_2_retrieval:       { label: 'B2: + Retrieval',     wer: 0.4146, cer: 0.2723, keyword_acc: 0.5903, numeric_acc: 0.7917, negation_acc: 0.875  },
  baseline_3_gated_retrieval: { label: 'B3: Gated Retrieval', wer: 0.3637, cer: 0.2207, keyword_acc: 0.6319, numeric_acc: 0.875,  negation_acc: 0.9167 },
}

const METRICS = [
  { key: 'wer',          label: 'WER ↓',      lower: true,  color: '#f87171' },
  { key: 'cer',          label: 'CER ↓',      lower: true,  color: '#fb923c' },
  { key: 'keyword_acc',  label: 'Keyword ↑',  lower: false, color: '#34d399' },
  { key: 'numeric_acc',  label: 'Numeric ↑',  lower: false, color: '#60a5fa' },
  { key: 'negation_acc', label: 'Negation ↑', lower: false, color: '#a78bfa' },
]

const BENCHMARK_EXAMPLES = [
  {
    title: 'Raw ASR Failure',
    tag: 'asr',
    tagStyle: 'bg-red-50 text-red-700 border-red-200',
    ref: 'The patient needs metformin 500 milligrams twice daily with meals.',
    raw: 'The patient needs met form in five hundred milligrams twice daily with meals.',
    corrected: null,
    note: 'Observed failure mode: Whisper fragments "metformin" across tokens. Numeric spoken form is not normalized at this stage.',
  },
  {
    title: 'Retrieval Correction',
    tag: 'retrieval',
    tagStyle: 'bg-blue-50 text-blue-700 border-blue-200',
    ref: 'I need a refill for lisinopril ten milligrams once daily.',
    raw: 'I need a refill for liss in o pril ten milligrams once daily.',
    corrected: 'I need a refill for lisinopril ten milligrams once daily.',
    note: 'Benchmark example: n-gram candidates from the domain vocabulary matched the fragmented form. Fuzzy similarity score exceeded the acceptance threshold.',
  },
  {
    title: 'Unsafe Ungated Correction',
    tag: 'ungated',
    tagStyle: 'bg-amber-50 text-amber-700 border-amber-200',
    ref: 'The patient is not taking insulin and has no chest pain today.',
    raw: 'The patient is not taking insulin and has no chest pain today.',
    corrected: 'The patient is taking insulin and has no chest pain today.',
    note: 'Ungated retrieval can remove negation context. B2 proposed replacing "not taking" with "taking" — a clinically unsafe edit. The gated model (B3) blocked this change.',
  },
  {
    title: 'Gated Safe Correction',
    tag: 'gated',
    tagStyle: 'bg-slate-100 text-slate-600 border-slate-200',
    ref: 'Change torsemide from ten milligrams to twenty milligrams starting tomorrow.',
    raw: 'Change tors amide from ten milligrams to twenty milligrams starting tomorrow.',
    corrected: 'Change torsemide from ten milligrams to twenty milligrams starting tomorrow.',
    note: 'Gated correction: the logistic regression gate accepted the retrieval suggestion. Semantic score was high, no negation was present, and no digit spans were affected.',
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

export default function BenchmarkSection() {
  const [open, setOpen] = useState(false)
  const [activeMetric, setActiveMetric] = useState('wer')

  const chartData = Object.values(BASELINES).map(b => ({
    name: b.label.split(':')[0],
    fullLabel: b.label,
    wer:          +(b.wer          * 100).toFixed(1),
    cer:          +(b.cer          * 100).toFixed(1),
    keyword_acc:  +(b.keyword_acc  * 100).toFixed(1),
    numeric_acc:  +(b.numeric_acc  * 100).toFixed(1),
    negation_acc: +(b.negation_acc * 100).toFixed(1),
  }))

  const selectedMetric = METRICS.find(m => m.key === activeMetric)

  return (
    <div className="card">
      <button
        className="w-full flex items-center justify-between"
        onClick={() => setOpen(v => !v)}
      >
        <div className="flex items-center gap-2">
          <span className="card-title mb-0">Benchmark &amp; Baselines</span>
          <span className="badge bg-slate-100 text-slate-500">4 systems · 5 metrics</span>
        </div>
        <CollapseIcon open={open} />
      </button>

      {open && (
        <div className="mt-5 space-y-8">

          {/* ── Metric Table ── */}
          <div>
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">Metric Comparison</p>
            <div className="overflow-x-auto rounded-xl border border-slate-200">
              <table className="min-w-full text-sm">
                <thead>
                  <tr className="bg-slate-50 border-b border-slate-200">
                    <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">System</th>
                    {METRICS.map(m => (
                      <th key={m.key} className="text-center px-3 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider whitespace-nowrap">
                        {m.label}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {Object.values(BASELINES).map((b, ri) => (
                    <tr key={ri} className="hover:bg-slate-50 transition-colors">
                      <td className="px-4 py-3 text-slate-700 whitespace-nowrap font-medium">
                        {b.label}
                      </td>
                      {METRICS.map(m => {
                        const val = b[m.key]
                        const best = Object.values(BASELINES).reduce((acc, bx) =>
                          m.lower ? Math.min(acc, bx[m.key]) : Math.max(acc, bx[m.key])
                        , m.lower ? Infinity : -Infinity)
                        const isBest = val === best
                        return (
                          <td key={m.key} className={`text-center px-3 py-3 font-mono text-sm
                            ${isBest ? 'text-emerald-700 font-bold' : 'text-slate-500'}`}>
                            {(val * 100).toFixed(1)}%
                          </td>
                        )
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="text-xs text-slate-400 mt-1.5">Bold green = best value per metric. ↓ lower is better, ↑ higher is better.</p>
          </div>

          {/* ── Bar Chart ── */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Chart View</p>
              <div className="flex gap-1">
                {METRICS.map(m => (
                  <button
                    key={m.key}
                    onClick={() => setActiveMetric(m.key)}
                    className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-all
                      ${activeMetric === m.key ? 'bg-brand-100 text-brand-700' : 'text-slate-500 hover:bg-slate-100'}`}
                  >
                    {m.label}
                  </button>
                ))}
              </div>
            </div>
            <div className="h-52">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis dataKey="name" tick={{ fontSize: 11, fill: '#94a3b8' }} />
                  <YAxis
                    tick={{ fontSize: 11, fill: '#94a3b8' }}
                    domain={[0, 100]}
                    tickFormatter={v => `${v}%`}
                  />
                  <Tooltip
                    formatter={(v) => [`${v}%`, selectedMetric?.label]}
                    labelFormatter={(_, payload) => payload?.[0]?.payload?.fullLabel}
                    contentStyle={{ borderRadius: '12px', border: '1px solid #e2e8f0', fontSize: '12px' }}
                  />
                  <Bar
                    dataKey={activeMetric}
                    fill={selectedMetric?.color || '#60a5fa'}
                    radius={[4, 4, 0, 0]}
                    maxBarSize={56}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* ── Benchmark Examples ── */}
          <div>
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">Benchmark Examples</p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {BENCHMARK_EXAMPLES.map((ex, i) => (
                <div key={i} className="rounded-xl border border-slate-200 p-4 space-y-3 bg-white">
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-semibold text-sm text-slate-800">{ex.title}</span>
                    <span className={`badge border ${ex.tagStyle}`}>{ex.tag}</span>
                  </div>

                  <div className="space-y-1.5 text-xs font-mono">
                    <TranscriptLine label="Reference" text={ex.ref} style="text-slate-600 bg-slate-50" />
                    <TranscriptLine label="Raw ASR"   text={ex.raw}      style="text-red-700 bg-red-50" />
                    {ex.corrected && (
                      <TranscriptLine label="Corrected" text={ex.corrected} style="text-emerald-700 bg-emerald-50" />
                    )}
                  </div>

                  <p className="text-xs text-slate-500 leading-relaxed">{ex.note}</p>
                </div>
              ))}
            </div>
          </div>

        </div>
      )}
    </div>
  )
}

function TranscriptLine({ label, text, style }) {
  return (
    <div className={`rounded-lg px-2.5 py-1.5 ${style}`}>
      <span className="font-sans font-medium text-slate-400 mr-1.5">{label}:</span>
      {text}
    </div>
  )
}

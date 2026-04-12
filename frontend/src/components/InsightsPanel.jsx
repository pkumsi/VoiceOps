export default function InsightsPanel({ extraction, corrections }) {
  const {
    medications = [],
    dosages = [],
    frequencies = [],
    negations = [],
    symptoms = [],
    intent,
    risk_flag,
  } = extraction || {}

  const hasEntities = medications.length || dosages.length || frequencies.length ||
    negations.length || symptoms.length || intent

  return (
    <div className="card w-full lg:w-80 shrink-0 space-y-5">
      <p className="card-title">Insights</p>

      {/* Risk Flag */}
      {extraction && (
        <div className={`flex items-center gap-3 rounded-xl px-4 py-3 border
          ${risk_flag
            ? 'bg-red-50 border-red-200 text-red-700'
            : 'bg-emerald-50 border-emerald-200 text-emerald-700'
          }`}>
          <span className={`inline-block w-2 h-2 rounded-full flex-shrink-0 ${risk_flag ? 'bg-red-500' : 'bg-emerald-500'}`} />
          <div>
            <p className="font-semibold text-sm">{risk_flag ? 'Risk Flagged' : 'No Risk Detected'}</p>
            <p className="text-xs opacity-70">{risk_flag ? 'Review required' : 'Safe to proceed'}</p>
          </div>
        </div>
      )}

      {/* Entities */}
      <div>
        <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Extracted Entities</p>
        {!hasEntities
          ? <p className="text-xs text-slate-400 italic">No entities extracted yet</p>
          : (
            <div className="space-y-2">
              <EntityRow label="Medications" items={medications} color="purple" />
              <EntityRow label="Dosages"     items={dosages}     color="blue"   />
              <EntityRow label="Frequencies" items={frequencies} color="cyan"   />
              <EntityRow label="Negations"   items={negations}   color="red"    />
              <EntityRow label="Symptoms"    items={symptoms}    color="amber"  />
              {intent && (
                <div>
                  <span className="text-xs text-slate-500 font-medium">Intent</span>
                  <p className="text-sm text-slate-700 font-medium mt-0.5">{intent}</p>
                </div>
              )}
            </div>
          )
        }
      </div>

      {/* Corrections list */}
      <div>
        <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Corrections</p>
        {!corrections?.length
          ? <p className="text-xs text-slate-400 italic">No corrections applied</p>
          : (
            <div className="space-y-1.5 max-h-48 overflow-y-auto pr-1">
              {corrections.map((c, i) => (
                <div key={i} className="rounded-lg bg-slate-50 border border-slate-200 px-3 py-2 text-xs">
                  <div className="mb-0.5">
                    <span className="badge bg-slate-200 text-slate-600">{c.type || 'edit'}</span>
                  </div>
                  <p className="text-slate-400 line-through truncate">{c.original}</p>
                  <p className="text-slate-800 font-medium truncate">{c.corrected}</p>
                  {c.reason && <p className="text-slate-400 mt-0.5 truncate">{c.reason}</p>}
                </div>
              ))}
            </div>
          )
        }
      </div>
    </div>
  )
}

const COLOR_MAP = {
  purple: 'bg-purple-100 text-purple-700',
  blue:   'bg-blue-100 text-blue-700',
  cyan:   'bg-cyan-100 text-cyan-700',
  red:    'bg-red-100 text-red-700',
  amber:  'bg-amber-100 text-amber-700',
}

function EntityRow({ label, items, color }) {
  if (!items?.length) return null
  return (
    <div>
      <span className="text-xs text-slate-500 font-medium">{label}</span>
      <div className="flex flex-wrap gap-1 mt-1">
        {items.map((item, i) => (
          <span key={i} className={`badge ${COLOR_MAP[color] || 'bg-slate-100 text-slate-700'}`}>
            {item}
          </span>
        ))}
      </div>
    </div>
  )
}

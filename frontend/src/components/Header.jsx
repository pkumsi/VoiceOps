export default function Header() {
  return (
    <header className="bg-white border-b border-slate-200 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          {/* Mic icon */}
          <div className="w-9 h-9 rounded-xl bg-brand-600 flex items-center justify-center shadow-sm">
            <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
            </svg>
          </div>
          <div>
            <h1 className="text-xl font-bold text-slate-900 leading-tight">VoiceOps</h1>
            <p className="text-xs text-slate-500 font-medium">Healthcare Voice Intelligence System</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="badge bg-emerald-100 text-emerald-700">Live</span>
          <span className="text-xs text-slate-400 font-mono">api: 127.0.0.1:8000</span>
        </div>
      </div>
    </header>
  )
}

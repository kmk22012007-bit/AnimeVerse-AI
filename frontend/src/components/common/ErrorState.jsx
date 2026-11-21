import React from 'react'
import { AlertTriangle, RefreshCw, ServerCrash } from 'lucide-react'

export const ErrorState = ({
  title = 'Service Link Disrupted',
  message = 'Failed to load anime data from the AnimeVerse service.',
  onRetry,
  compact = false,
}) => {
  return (
    <div
      className={`rounded-2xl border border-rose-500/30 bg-gradient-to-b from-rose-950/20 to-purple-950/30 p-6 sm:p-8 text-center relative overflow-hidden backdrop-blur-md ${
        compact ? 'py-6' : 'my-6'
      }`}
    >
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-rose-500/10 via-transparent to-transparent pointer-events-none"></div>

      <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-rose-500/15 border border-rose-500/40 text-rose-400 mb-4 shadow-[0_0_20px_rgba(244,63,94,0.25)]">
        <AlertTriangle className="w-7 h-7" />
      </div>

      <h3 className="text-lg font-bold text-rose-200 tracking-wide mb-2 flex items-center justify-center gap-2">
        <span>{title}</span>
        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-rose-950 border border-rose-500/40 text-rose-300">
          ERR_STREAM
        </span>
      </h3>

      <p className="text-sm text-slate-300 max-w-md mx-auto mb-5 leading-relaxed">
        {message}
      </p>

      {onRetry && (
        <button
          onClick={onRetry}
          type="button"
          className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-medium text-sm transition-all duration-200 shadow-[0_0_15px_rgba(168,85,247,0.4)] hover:shadow-[0_0_25px_rgba(168,85,247,0.6)] cursor-pointer"
        >
          <RefreshCw className="w-4 h-4" />
          <span>Re-establish Uplink</span>
        </button>
      )}
    </div>
  )
}

export default ErrorState

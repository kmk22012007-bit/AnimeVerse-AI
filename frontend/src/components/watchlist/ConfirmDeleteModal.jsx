import React from 'react'
import { AlertTriangle, Trash2, X } from 'lucide-react'

export const ConfirmDeleteModal = ({ entry, isOpen, onClose, onConfirm, deleting = false }) => {
  if (!isOpen || !entry) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fadeIn">
      <div className="relative w-full max-w-md rounded-3xl bg-[#0c0e1e] border border-rose-500/40 shadow-[0_0_35px_rgba(244,63,94,0.3)] overflow-hidden">
        {/* Header Banner */}
        <div className="p-6 text-center space-y-3">
          <div className="w-14 h-14 rounded-2xl bg-rose-500/15 border border-rose-500/40 text-rose-400 flex items-center justify-center mx-auto shadow-[0_0_20px_rgba(244,63,94,0.3)]">
            <AlertTriangle className="w-7 h-7" />
          </div>

          <h3 className="text-lg font-bold text-white">
            Remove from Watchlist?
          </h3>

          <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">
            Are you sure you want to remove <span className="font-semibold text-purple-300">"{entry.title}"</span>?
          </p>

          <p className="text-[11px] text-slate-400 font-mono">
            This will permanently delete your episode progress, rating, and notes for this anime from your session records.
          </p>
        </div>

        {/* Actions */}
        <div className="p-4 border-t border-purple-500/20 bg-purple-950/40 flex items-center justify-end gap-3">
          <button
            onClick={onClose}
            disabled={deleting}
            type="button"
            className="px-4 py-2.5 rounded-xl text-xs sm:text-sm font-semibold text-slate-300 hover:text-white hover:bg-purple-900/40 transition-colors"
          >
            Keep in List
          </button>

          <button
            onClick={() => onConfirm(entry.id)}
            disabled={deleting}
            type="button"
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-rose-600 hover:bg-rose-500 text-white font-semibold text-xs sm:text-sm transition-all shadow-[0_0_15px_rgba(244,63,94,0.4)] cursor-pointer disabled:opacity-50"
          >
            <Trash2 className="w-4 h-4" />
            <span>{deleting ? 'Removing...' : 'Confirm Remove'}</span>
          </button>
        </div>
      </div>
    </div>
  )
}

export default ConfirmDeleteModal

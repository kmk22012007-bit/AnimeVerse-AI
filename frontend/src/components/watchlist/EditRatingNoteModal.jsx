import React, { useState } from 'react'
import { Star, X, Check, Loader2 } from 'lucide-react'

export const EditRatingNoteModal = ({ entry, isOpen, onClose, onSave }) => {
  if (!isOpen || !entry) return null

  const [rating, setRating] = useState(entry.rating || 0)
  const [hoverRating, setHoverRating] = useState(0)
  const [note, setNote] = useState(entry.note || '')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState(null)

  const handleSave = async () => {
    setSaving(true)
    setError(null)
    const result = await onSave(entry.id, {
      rating: rating > 0 ? rating : null,
      note: note.trim() || null,
    })
    setSaving(false)
    if (result?.success) {
      onClose()
    } else {
      setError(result?.error || 'Failed to save changes.')
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fadeIn">
      <div className="relative w-full max-w-lg rounded-3xl bg-[#0c0e1e] border border-purple-500/40 shadow-[0_0_35px_rgba(168,85,247,0.3)] overflow-hidden">
        {/* Header */}
        <div className="p-5 border-b border-purple-500/20 bg-purple-950/40 flex items-center justify-between">
          <div>
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <Star className="w-4 h-4 fill-amber-400 text-amber-400" />
              Rating & Personal Notes
            </h3>
            <p className="text-xs text-slate-400 truncate max-w-sm mt-0.5 font-mono">
              {entry.title}
            </p>
          </div>

          <button
            onClick={onClose}
            type="button"
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-purple-900/30 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {error && (
            <div className="p-3 rounded-xl bg-rose-950/40 border border-rose-500/40 text-rose-300 text-xs">
              {error}
            </div>
          )}

          {/* 10-Star Rating Bar */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="text-xs font-mono uppercase tracking-wider text-slate-300 font-semibold">
                Your Score (1 to 10)
              </label>
              <span className="text-xs font-mono font-bold text-amber-300">
                {rating > 0 ? `${rating} / 10` : 'Not Rated'}
              </span>
            </div>

            <div className="flex items-center gap-1.5 p-3 rounded-2xl bg-purple-950/30 border border-purple-500/20 justify-center">
              {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((starVal) => {
                const isLit = (hoverRating || rating) >= starVal
                return (
                  <button
                    key={starVal}
                    type="button"
                    onMouseEnter={() => setHoverRating(starVal)}
                    onMouseLeave={() => setHoverRating(0)}
                    onClick={() => setRating(rating === starVal ? 0 : starVal)}
                    className="p-1 text-slate-600 hover:scale-125 transition-transform cursor-pointer"
                    title={`Rate ${starVal} / 10`}
                  >
                    <Star
                      className={`w-5 h-5 transition-colors ${
                        isLit
                          ? 'fill-amber-400 text-amber-400 drop-shadow-[0_0_6px_rgba(251,191,36,0.6)]'
                          : 'text-slate-600'
                      }`}
                    />
                  </button>
                )
              })}
            </div>

            {rating > 0 && (
              <button
                type="button"
                onClick={() => setRating(0)}
                className="text-[11px] text-slate-400 hover:text-rose-300 font-mono transition-colors"
              >
                Clear Rating
              </button>
            )}
          </div>

          {/* Personal Note Textarea */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="text-xs font-mono uppercase tracking-wider text-slate-300 font-semibold">
                Personal Notes
              </label>
              <span className="text-[11px] font-mono text-slate-500">
                {note.length} / 2000
              </span>
            </div>

            <textarea
              value={note}
              onChange={(e) => setNote(e.target.value.slice(0, 2000))}
              rows={4}
              placeholder="Add your thoughts, favorite episodes, quotes, or thoughts on this anime..."
              className="w-full p-3.5 rounded-2xl bg-purple-950/30 border border-purple-500/30 text-sm text-slate-100 placeholder:text-slate-500 focus:outline-none focus:border-purple-400 focus:ring-1 focus:ring-purple-400/50 resize-none font-sans"
            />
          </div>
        </div>

        {/* Footer Actions */}
        <div className="p-4 border-t border-purple-500/20 bg-purple-950/40 flex items-center justify-end gap-3">
          <button
            onClick={onClose}
            type="button"
            className="px-4 py-2 rounded-xl text-xs sm:text-sm font-semibold text-slate-300 hover:text-white hover:bg-purple-900/40 transition-colors"
          >
            Cancel
          </button>

          <button
            onClick={handleSave}
            disabled={saving}
            type="button"
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-semibold text-xs sm:text-sm transition-all shadow-[0_0_15px_rgba(168,85,247,0.4)] cursor-pointer disabled:opacity-50"
          >
            {saving ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Check className="w-4 h-4" />
            )}
            <span>Save Entry</span>
          </button>
        </div>
      </div>
    </div>
  )
}

export default EditRatingNoteModal

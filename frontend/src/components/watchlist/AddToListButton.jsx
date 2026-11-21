import React, { useState, useRef, useEffect } from 'react'
import { BookmarkPlus, BookmarkCheck, ChevronDown, Check, Loader2 } from 'lucide-react'
import { useWatchlist } from '../../context/WatchlistContext'

const STATUS_OPTIONS = [
  { label: 'Watching', value: 'Watching', color: 'text-cyan-400' },
  { label: 'Plan to Watch', value: 'Plan to Watch', color: 'text-purple-400' },
  { label: 'Completed', value: 'Completed', color: 'text-emerald-400' },
  { label: 'On Hold', value: 'On Hold', color: 'text-amber-400' },
  { label: 'Dropped', value: 'Dropped', color: 'text-rose-400' },
]

export const AddToListButton = ({ malId, className = '', compact = false }) => {
  const { getEntryByMalId, addAnime, changeStatus } = useWatchlist()
  const [open, setOpen] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const menuRef = useRef(null)

  const existingEntry = getEntryByMalId(malId)
  const currentStatus = existingEntry?.status

  // Close dropdown on click outside
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) {
        setOpen(false)
      }
    }
    if (open) {
      document.addEventListener('mousedown', handleClickOutside)
    }
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [open])

  const handleSelectStatus = async (statusValue) => {
    setSubmitting(true)
    setOpen(false)
    if (existingEntry) {
      await changeStatus(existingEntry.id, statusValue)
    } else {
      await addAnime(malId, statusValue)
    }
    setSubmitting(false)
  }

  const activeOption = STATUS_OPTIONS.find((opt) => opt.value === currentStatus)

  if (compact) {
    return (
      <div className={`relative ${className}`} ref={menuRef}>
        <button
          onClick={(e) => {
            e.preventDefault()
            e.stopPropagation()
            setOpen((prev) => !prev)
          }}
          disabled={submitting}
          type="button"
          aria-label={existingEntry ? `Watchlist: ${activeOption?.label}` : 'Add to Watchlist'}
          className={`p-1.5 rounded-lg backdrop-blur-md border transition-all duration-200 cursor-pointer ${
            existingEntry
              ? 'bg-purple-900/80 border-purple-400/60 text-purple-200 shadow-[0_0_10px_rgba(168,85,247,0.4)]'
              : 'bg-black/60 border-purple-500/30 text-purple-300 hover:bg-purple-900/60 hover:border-purple-400'
          }`}
          title={existingEntry ? `Status: ${activeOption?.label}` : 'Add to Watchlist'}
        >
          {submitting ? (
            <Loader2 className="w-3.5 h-3.5 animate-spin text-purple-300" />
          ) : existingEntry ? (
            <BookmarkCheck className="w-3.5 h-3.5 fill-purple-400/40 text-purple-300" />
          ) : (
            <BookmarkPlus className="w-3.5 h-3.5" />
          )}
        </button>

        {open && (
          <div
            onClick={(e) => {
              e.preventDefault()
              e.stopPropagation()
            }}
            className="absolute right-0 bottom-full mb-1 w-36 py-1 rounded-xl bg-[#0e101f] border border-purple-500/40 shadow-[0_0_20px_rgba(0,0,0,0.8)] z-50 overflow-hidden"
          >
            {STATUS_OPTIONS.map((opt) => (
              <button
                key={opt.value}
                onClick={() => handleSelectStatus(opt.value)}
                type="button"
                className={`w-full px-3 py-1.5 text-left text-xs font-medium flex items-center justify-between hover:bg-purple-950/60 transition-colors cursor-pointer ${
                  currentStatus === opt.value ? 'bg-purple-900/40 font-bold' : ''
                }`}
              >
                <span className={opt.color}>{opt.label}</span>
                {currentStatus === opt.value && <Check className="w-3 h-3 text-cyan-400" />}
              </button>
            ))}
          </div>
        )}
      </div>
    )
  }

  return (
    <div className={`relative inline-block ${className}`} ref={menuRef}>
      <button
        onClick={() => setOpen((prev) => !prev)}
        disabled={submitting}
        type="button"
        className={`inline-flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs sm:text-sm font-semibold transition-all duration-200 cursor-pointer border ${
          existingEntry
            ? 'bg-purple-600/30 border-purple-400/60 text-purple-100 shadow-[0_0_15px_rgba(168,85,247,0.3)]'
            : 'bg-purple-600 hover:bg-purple-500 text-white border-purple-400 shadow-[0_0_15px_rgba(168,85,247,0.4)]'
        }`}
      >
        {submitting ? (
          <Loader2 className="w-4 h-4 animate-spin text-purple-300" />
        ) : existingEntry ? (
          <BookmarkCheck className="w-4 h-4 text-cyan-400" />
        ) : (
          <BookmarkPlus className="w-4 h-4" />
        )}

        <span>{existingEntry ? activeOption?.label : 'Add to Watchlist'}</span>
        <ChevronDown className="w-3.5 h-3.5 text-purple-300 ml-0.5" />
      </button>

      {open && (
        <div className="absolute left-0 mt-2 w-44 py-1.5 rounded-2xl bg-[#0c0e1e] border border-purple-500/40 shadow-[0_0_25px_rgba(0,0,0,0.85)] z-50 overflow-hidden backdrop-blur-md">
          <div className="px-3 py-1 text-[10px] font-mono uppercase tracking-wider text-slate-400 border-b border-purple-500/20 mb-1">
            {existingEntry ? 'Change Status' : 'Set Status'}
          </div>
          {STATUS_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              onClick={() => handleSelectStatus(opt.value)}
              type="button"
              className={`w-full px-3.5 py-2 text-left text-xs font-semibold flex items-center justify-between hover:bg-purple-950/60 transition-colors cursor-pointer ${
                currentStatus === opt.value ? 'bg-purple-900/40 text-white' : 'text-slate-300'
              }`}
            >
              <span className={opt.color}>{opt.label}</span>
              {currentStatus === opt.value && <Check className="w-3.5 h-3.5 text-cyan-400" />}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

export default AddToListButton

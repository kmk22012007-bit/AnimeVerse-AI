import React, { useState } from 'react'
import { Link } from 'react-router-dom'
import {
  Plus,
  Minus,
  Check,
  Star,
  FileText,
  Trash2,
  Play,
  CheckCircle2,
  Clock,
  PauseCircle,
  XCircle,
} from 'lucide-react'
import { useWatchlist } from '../../context/WatchlistContext'

const STATUS_CONFIG = {
  Watching: { label: 'Watching', color: 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40', icon: Play },
  Completed: { label: 'Completed', color: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40', icon: CheckCircle2 },
  'Plan to Watch': { label: 'Plan to Watch', color: 'bg-purple-500/20 text-purple-300 border-purple-500/40', icon: Clock },
  'On Hold': { label: 'On Hold', color: 'bg-amber-500/20 text-amber-300 border-amber-500/40', icon: PauseCircle },
  Dropped: { label: 'Dropped', color: 'bg-rose-500/20 text-rose-300 border-rose-500/40', icon: XCircle },
}

export const WatchlistRowCard = ({ entry, onEditRatingNote, onDelete }) => {
  const { incrementEpisode, decrementEpisode, changeStatus, setProgress } = useWatchlist()
  const [editingEp, setEditingEp] = useState(false)
  const [epInput, setEpInput] = useState(entry.watched_episodes || 0)

  if (!entry || entry.is_blocked || entry.anime?.is_blocked) return null

  const {
    id,
    mal_id,
    title,
    poster_url,
    total_episodes,
    status,
    watched_episodes,
    rating,
    note,
    updated_at,
  } = entry

  const total = total_episodes || 0
  const watched = watched_episodes || 0
  const progressPercent = total > 0 ? Math.min(100, Math.round((watched / total) * 100)) : 0
  const statusInfo = STATUS_CONFIG[status] || STATUS_CONFIG.plan_to_watch
  const StatusIcon = statusInfo.icon

  const handleEpInputSubmit = () => {
    const val = parseInt(epInput, 10)
    if (!isNaN(val) && val >= 0) {
      if (total > 0 && val > total) {
        setProgress(id, total)
      } else {
        setProgress(id, val)
      }
    }
    setEditingEp(false)
  }

  return (
    <div className="flex flex-col sm:flex-row gap-4 sm:gap-5 p-4 sm:p-5 rounded-2xl bg-[#0c0e1e] border border-purple-500/20 hover:border-purple-400/50 transition-all duration-300 hover:shadow-[0_0_25px_rgba(168,85,247,0.18)]">
      {/* 1. Poster Thumbnail with hover link */}
      <Link
        to={`/anime/${mal_id}`}
        className="relative w-20 sm:w-28 aspect-[3/4] rounded-xl overflow-hidden bg-purple-950/60 flex-shrink-0 group shadow-md"
      >
        {poster_url ? (
          <img
            src={poster_url}
            alt={title}
            className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-purple-400 text-xs font-mono">
            NO ART
          </div>
        )}
        <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
          <Play className="w-6 h-6 fill-white text-white" />
        </div>
      </Link>

      {/* 2. Middle Info Section */}
      <div className="flex-1 flex flex-col justify-between py-0.5 space-y-3">
        <div>
          {/* Top badges: Status picker & Rating pill */}
          <div className="flex flex-wrap items-center justify-between gap-2 mb-1.5">
            <div className="flex items-center gap-2">
              {/* Status Selector Dropdown */}
              <select
                value={status}
                onChange={(e) => changeStatus(id, e.target.value)}
                className={`text-xs font-mono font-bold uppercase tracking-wider px-2.5 py-1 rounded-lg border cursor-pointer focus:outline-none focus:ring-1 focus:ring-purple-400 ${statusInfo.color} bg-[#0c0e1e]`}
              >
                <option value="Watching">Watching</option>
                <option value="Completed">Completed</option>
                <option value="Plan to Watch">Plan to Watch</option>
                <option value="On Hold">On Hold</option>
                <option value="Dropped">Dropped</option>
              </select>
            </div>

            {/* Rating Pill */}
            <button
              onClick={() => onEditRatingNote(entry)}
              type="button"
              className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-purple-950/40 hover:bg-purple-900/60 border border-purple-500/30 text-xs font-mono font-semibold transition-colors cursor-pointer"
            >
              <Star
                className={`w-3.5 h-3.5 ${
                  rating ? 'fill-amber-400 text-amber-400' : 'text-slate-500'
                }`}
              />
              <span className={rating ? 'text-amber-300 font-bold' : 'text-slate-400'}>
                {rating ? `${rating}/10` : 'Rate'}
              </span>
            </button>
          </div>

          {/* Title */}
          <Link to={`/anime/${mal_id}`}>
            <h3 className="text-base font-bold text-white hover:text-purple-300 transition-colors line-clamp-1">
              {title}
            </h3>
          </Link>

          {/* Personal Note Preview */}
          {note && (
            <p className="text-xs text-slate-400 italic line-clamp-1 mt-1 bg-purple-950/20 px-2 py-0.5 rounded border border-purple-500/10">
              "{note}"
            </p>
          )}
        </div>

        {/* 3. Episode Stepper & Progress Bar */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-xs font-mono">
            <div className="flex items-center gap-2">
              <span className="text-slate-400">Progress:</span>

              {editingEp ? (
                <div className="inline-flex items-center gap-1">
                  <input
                    type="number"
                    min="0"
                    max={total > 0 ? total : 9999}
                    value={epInput}
                    onChange={(e) => setEpInput(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleEpInputSubmit()}
                    onBlur={handleEpInputSubmit}
                    autoFocus
                    className="w-14 px-1 py-0.5 rounded bg-purple-950 border border-purple-400 text-center text-xs font-mono text-white focus:outline-none"
                  />
                  <span className="text-slate-500">/ {total > 0 ? total : '??'} eps</span>
                </div>
              ) : (
                <button
                  onClick={() => {
                    setEpInput(watched)
                    setEditingEp(true)
                  }}
                  type="button"
                  title="Click to manually edit episode count"
                  className="font-bold text-purple-200 hover:text-cyan-300 transition-colors underline decoration-dotted"
                >
                  {watched} <span className="text-slate-500">/ {total > 0 ? total : '??'} eps</span>
                </button>
              )}
            </div>

            {/* Stepper Buttons: -1, +1 */}
            <div className="flex items-center gap-1.5">
              <button
                onClick={() => decrementEpisode(entry)}
                disabled={watched <= 0}
                type="button"
                aria-label="Decrease episode progress"
                className="w-7 h-7 rounded-lg bg-purple-950/50 hover:bg-purple-900/60 border border-purple-500/30 text-purple-300 hover:text-white flex items-center justify-center transition-colors disabled:opacity-30 disabled:pointer-events-none cursor-pointer"
                title="-1 Episode"
              >
                <Minus className="w-3.5 h-3.5" />
              </button>

              <button
                onClick={() => incrementEpisode(entry)}
                disabled={total > 0 && watched >= total}
                type="button"
                aria-label="Increase episode progress"
                className="w-7 h-7 rounded-lg bg-purple-600 hover:bg-purple-500 text-white flex items-center justify-center transition-all shadow-[0_0_10px_rgba(168,85,247,0.4)] disabled:opacity-30 disabled:pointer-events-none cursor-pointer"
                title="+1 Episode"
              >
                <Plus className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>

          {/* Progress Bar */}
          <div className="w-full h-2 rounded-full bg-purple-950/80 overflow-hidden border border-purple-500/20">
            <div
              className="h-full rounded-full bg-gradient-to-r from-purple-500 via-fuchsia-500 to-cyan-400 transition-all duration-300 shadow-[0_0_8px_rgba(168,85,247,0.6)]"
              style={{ width: `${progressPercent}%` }}
            ></div>
          </div>
        </div>
      </div>

      {/* 4. Action Icons Column */}
      <div className="flex sm:flex-col justify-end sm:justify-between items-end border-t sm:border-t-0 sm:border-l border-purple-500/20 pt-2 sm:pt-0 sm:pl-3 gap-2">
        <button
          onClick={() => onEditRatingNote(entry)}
          type="button"
          aria-label="Edit notes and rating"
          className="p-2 rounded-xl text-slate-400 hover:text-purple-300 hover:bg-purple-900/30 transition-colors"
          title="Edit Notes & Rating"
        >
          <FileText className="w-4 h-4" />
        </button>

        <button
          onClick={() => onDelete(entry)}
          type="button"
          aria-label="Remove from watchlist"
          className="p-2 rounded-xl text-slate-400 hover:text-rose-400 hover:bg-rose-950/30 transition-colors"
          title="Remove from Watchlist"
        >
          <Trash2 className="w-4 h-4" />
        </button>
      </div>
    </div>
  )
}

export default WatchlistRowCard

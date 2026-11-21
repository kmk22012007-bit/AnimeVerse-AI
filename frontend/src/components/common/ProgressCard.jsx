import React from 'react'
import { Play, Star, Plus, Minus } from 'lucide-react'
import { Link } from 'react-router-dom'
import { useWatchlist } from '../../context/WatchlistContext'

export const ProgressCard = ({ entry }) => {
  const { incrementEpisode, decrementEpisode } = useWatchlist()

  if (!entry) return null

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
  } = entry

  const total = total_episodes || 0
  const watched = watched_episodes || 0
  const progressPercent = total > 0 ? Math.min(100, Math.round((watched / total) * 100)) : 0

  return (
    <div className="flex gap-4 p-4 rounded-2xl bg-purple-950/25 border border-purple-500/20 hover:border-purple-400/50 transition-all duration-300 hover:shadow-[0_0_20px_rgba(168,85,247,0.2)]">
      {/* Anime Poster Thumbnail */}
      <Link to={`/anime/${mal_id}`} className="relative w-20 h-28 rounded-xl overflow-hidden bg-purple-950/50 flex-shrink-0 group">
        {poster_url ? (
          <img
            src={poster_url}
            alt={title}
            className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-purple-400 text-xs font-mono">
            ANIME
          </div>
        )}
        <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
          <Play className="w-5 h-5 text-white fill-white" />
        </div>
      </Link>

      {/* Progress Information */}
      <div className="flex flex-col justify-between flex-1 py-0.5">
        <div>
          <div className="flex items-center justify-between gap-2 mb-1">
            <span className="text-[10px] font-mono uppercase tracking-wider px-2 py-0.5 rounded-md bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 font-bold">
              {status}
            </span>
            {rating && (
              <div className="flex items-center gap-1 text-xs font-bold text-amber-300">
                <Star className="w-3 h-3 fill-amber-300 text-amber-300" />
                <span>{rating}/10</span>
              </div>
            )}
          </div>

          <Link to={`/anime/${mal_id}`}>
            <h4 className="text-sm font-bold text-slate-100 hover:text-purple-300 transition-colors line-clamp-1">
              {title}
            </h4>
          </Link>

          {note && (
            <p className="text-xs text-slate-400 italic line-clamp-1 mt-0.5">
              "{note}"
            </p>
          )}
        </div>

        {/* Episode Progress Bar with Stepper Buttons */}
        <div className="space-y-1.5 mt-2">
          <div className="flex items-center justify-between text-xs text-slate-300">
            <span className="font-mono text-purple-300">
              Ep {watched} <span className="text-slate-500">/</span> {total > 0 ? total : '??'}
            </span>

            <div className="flex items-center gap-1">
              <button
                onClick={() => decrementEpisode(entry)}
                disabled={watched <= 0}
                type="button"
                aria-label="Decrease episode progress"
                className="w-5 h-5 rounded bg-purple-950/60 hover:bg-purple-900 border border-purple-500/30 text-purple-300 flex items-center justify-center disabled:opacity-30 disabled:pointer-events-none cursor-pointer"
                title="-1 Ep"
              >
                <Minus className="w-3 h-3" />
              </button>
              <button
                onClick={() => incrementEpisode(entry)}
                disabled={total > 0 && watched >= total}
                type="button"
                aria-label="Increase episode progress"
                className="w-5 h-5 rounded bg-purple-600 hover:bg-purple-500 text-white flex items-center justify-center shadow-sm disabled:opacity-30 disabled:pointer-events-none cursor-pointer"
                title="+1 Ep"
              >
                <Plus className="w-3 h-3" />
              </button>
              <span className="text-[11px] font-mono text-slate-400 ml-1.5">{progressPercent}%</span>
            </div>
          </div>

          <div className="w-full h-2 rounded-full bg-purple-950/60 overflow-hidden border border-purple-500/20">
            <div
              className="h-full rounded-full bg-gradient-to-r from-purple-500 via-fuchsia-500 to-cyan-400 transition-all duration-300 shadow-[0_0_8px_rgba(168,85,247,0.7)]"
              style={{ width: `${progressPercent}%` }}
            ></div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ProgressCard

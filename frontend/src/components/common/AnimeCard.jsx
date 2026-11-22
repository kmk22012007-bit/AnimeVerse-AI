import React, { useState } from 'react'
import { Star, Play, ImageOff, Layers, Sparkles } from 'lucide-react'
import { Link } from 'react-router-dom'
import AddToListButton from '../watchlist/AddToListButton'

export const AnimeCard = ({ anime, priority = false }) => {
  const [imageError, setImageError] = useState(false)

  if (!anime || anime.is_blocked) return null

  const {
    mal_id,
    title,
    title_english,
    poster_url,
    score,
    anime_type,
    total_episodes,
    metadata_source,
    is_cached,
    is_franchise,
    franchise_id,
    entry_count,
    relationship_label,
  } = anime

  const displayTitle = title_english || title || `Anime #${mal_id}`
  const scoreFormatted = score ? Number(score).toFixed(2) : null
  const sourceNormalized = (metadata_source || '').toLowerCase()

  const destinationUrl = is_franchise && franchise_id ? `/franchise/${franchise_id}` : `/anime/${mal_id}`

  return (
    <Link
      to={destinationUrl}
      className="group relative flex flex-col rounded-2xl overflow-hidden bg-[#0d0f1e]/90 border border-purple-500/18 hover:border-purple-400/50 transition-all duration-200 hover:shadow-[0_8px_24px_rgba(168,85,247,0.2)] hover:-translate-y-1 focus:outline-none focus:ring-2 focus:ring-purple-400/60"
    >
      {/* 3:4 Aspect Ratio Poster Container */}
      <div className="relative w-full aspect-[3/4] bg-purple-950/40 overflow-hidden">
        {poster_url && !imageError ? (
          <img
            src={poster_url}
            alt={displayTitle}
            title={displayTitle}
            loading={priority ? 'eager' : 'lazy'}
            onError={() => setImageError(true)}
            className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
          />
        ) : (
          /* Honest neutral placeholder per SRS */
          <div className="w-full h-full flex flex-col items-center justify-center bg-gradient-to-b from-purple-950/40 to-[#0d0f1e] text-purple-400/60 p-4 text-center border border-purple-500/15">
            <div className="w-10 h-10 rounded-xl bg-purple-900/30 border border-purple-500/30 flex items-center justify-center mb-2 shadow-inner">
              <ImageOff className="w-5 h-5 text-purple-300 stroke-[1.5]" />
            </div>
            <span className="text-[10px] font-mono tracking-widest text-purple-300/80">NO ARTWORK</span>
            <span className="text-[9px] font-mono text-slate-500 mt-1 line-clamp-1">{displayTitle}</span>
          </div>
        )}

        {/* Top Badges: Score & Type (Left) & Watchlist Button (Right) */}
        <div className="absolute top-2 inset-x-2 flex items-center justify-between z-10 pointer-events-none">
          <div className="flex flex-wrap items-center gap-1 max-w-[70%]">
            {scoreFormatted && (
              <div className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-md bg-black/85 backdrop-blur-md border border-cyan-400/40 text-cyan-300 text-[11px] font-bold shadow-sm">
                <Star className="w-2.5 h-2.5 fill-cyan-400 text-cyan-400" />
                <span>{scoreFormatted}</span>
              </div>
            )}

            {anime_type && (
              <span className="px-1.5 py-0.5 rounded-md bg-black/85 backdrop-blur-md border border-purple-400/30 text-purple-300 text-[10px] font-semibold tracking-wider uppercase">
                {anime_type}
              </span>
            )}

            {is_franchise && entry_count > 1 && (
              <span
                className="px-1.5 py-0.5 rounded-md bg-indigo-950/90 backdrop-blur-md border border-indigo-400/50 text-indigo-300 text-[9px] font-bold tracking-wider uppercase flex items-center gap-1"
                title={`${entry_count} verified entries in this franchise`}
              >
                <Layers className="w-2.5 h-2.5 text-indigo-300" />
                <span>{entry_count}</span>
              </span>
            )}
          </div>

          <div className="pointer-events-auto">
            <AddToListButton malId={mal_id} compact />
          </div>
        </div>

        {/* Play Overlay Hover effect */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/85 via-black/35 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-200 flex items-center justify-center">
          <div className="w-11 h-11 rounded-full bg-purple-600/90 border border-purple-300 text-white flex items-center justify-center shadow-[0_0_18px_rgba(168,85,247,0.6)] transform scale-95 group-hover:scale-100 transition-transform">
            <Play className="w-4 h-4 fill-white ml-0.5" />
          </div>
        </div>

        {/* Bottom Ep / Provenance / Cache Status strip over poster */}
        <div className="absolute bottom-2 inset-x-2 flex items-center justify-between text-[11px] text-slate-300 opacity-95 group-hover:opacity-100 transition-opacity">
          {total_episodes ? (
            <span className="px-1.5 py-0.5 rounded bg-black/80 backdrop-blur-sm text-[10px] font-mono border border-white/10">
              {total_episodes} eps
            </span>
          ) : <span></span>}

          <div className="flex items-center gap-1">
            {metadata_source && (
              <span
                className={`px-1.5 py-0.5 rounded backdrop-blur-sm text-[9px] font-mono font-bold border uppercase ${
                  sourceNormalized === 'anilist'
                    ? 'bg-sky-950/90 text-sky-300 border-sky-400/50'
                    : sourceNormalized === 'tenrai'
                    ? 'bg-purple-950/90 text-purple-300 border-purple-400/50'
                    : 'bg-indigo-950/90 text-indigo-300 border-indigo-400/50'
                }`}
                title={`Metadata provided by ${metadata_source}`}
              >
                {metadata_source}
              </span>
            )}

            {is_cached && (
              <span
                className="px-1.5 py-0.5 rounded bg-emerald-950/80 backdrop-blur-sm text-[8px] font-mono font-semibold text-emerald-300 border border-emerald-500/40"
                title="Served from local fast cache"
              >
                CACHED
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Card Info Section with readable title */}
      <div className="p-3.5 flex flex-col justify-between flex-1 bg-[#101324] border-t border-purple-500/10">
        <div>
          <h4
            className="text-xs sm:text-sm font-semibold text-slate-100 group-hover:text-purple-300 transition-colors line-clamp-2 leading-snug min-h-[36px]"
            title={displayTitle}
          >
            {displayTitle}
          </h4>

          {title_english && title && title_english !== title && (
            <p className="text-[10px] sm:text-[11px] text-slate-400 truncate mt-0.5" title={title}>
              {title}
            </p>
          )}

          {anime.personalization_reason && (
            <div className="mt-2 inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-purple-500/15 border border-purple-400/25 text-purple-200 text-[10px] font-mono max-w-full">
              <Sparkles className="w-2.5 h-2.5 text-cyan-400 shrink-0" />
              <span className="truncate">{anime.personalization_reason}</span>
            </div>
          )}
        </div>
      </div>
    </Link>
  )
}

export default AnimeCard

import React, { useRef } from 'react'
import { ChevronLeft, ChevronRight } from 'lucide-react'
import AnimeCard from './AnimeCard'

export const AnimeCarousel = ({ items = [], title, subtitle }) => {
  const scrollRef = useRef(null)

  const handleScroll = (direction) => {
    if (scrollRef.current) {
      const scrollAmount = direction === 'left' ? -420 : 420
      scrollRef.current.scrollBy({ left: scrollAmount, behavior: 'smooth' })
    }
  }

  if (!items || items.length === 0) return null

  return (
    <div className="space-y-4 my-6">
      <div className="flex items-center justify-between">
        <div>
          {title && (
            <h3 className="text-xl font-bold text-slate-100 tracking-wide flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-purple-500 shadow-[0_0_8px_rgba(168,85,247,0.8)]"></span>
              {title}
            </h3>
          )}
          {subtitle && (
            <p className="text-xs text-slate-400 mt-0.5">{subtitle}</p>
          )}
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => handleScroll('left')}
            type="button"
            aria-label="Scroll left"
            className="p-2 rounded-xl bg-purple-950/40 border border-purple-500/20 hover:border-purple-400/60 hover:bg-purple-900/40 text-purple-300 hover:text-white transition-all shadow-sm cursor-pointer"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
          <button
            onClick={() => handleScroll('right')}
            type="button"
            aria-label="Scroll right"
            className="p-2 rounded-xl bg-purple-950/40 border border-purple-500/20 hover:border-purple-400/60 hover:bg-purple-900/40 text-purple-300 hover:text-white transition-all shadow-sm cursor-pointer"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>

      <div
        ref={scrollRef}
        className="flex gap-4 overflow-x-auto pb-3 pt-1 scrollbar-none snap-x snap-mandatory"
        style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}
      >
        {items.map((anime) => (
          <div key={anime.mal_id} className="w-40 sm:w-48 flex-shrink-0 snap-start">
            <AnimeCard anime={anime} />
          </div>
        ))}
      </div>
    </div>
  )
}

export default AnimeCarousel

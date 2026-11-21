import React, { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import {
  CalendarDays,
  Calendar as CalendarIcon,
  ChevronLeft,
  ChevronRight,
  Tv,
  Film,
  Sparkles,
  Clock,
  ExternalLink,
  Flame,
} from 'lucide-react'
import { getSeasonAnime, getUpcomingAnime } from '../api/calendar'

const SEASONS = ['winter', 'spring', 'summer', 'fall']

export const CalendarPage = () => {
  const currentYear = new Date().getFullYear()
  const currentMonth = new Date().getMonth() // 0 to 11

  // Map month to seasonal quarter
  const getDefaultSeason = (month) => {
    if (month >= 0 && month <= 2) return 'winter'
    if (month >= 3 && month <= 5) return 'spring'
    if (month >= 6 && month <= 8) return 'summer'
    return 'fall'
  }

  const [activeTab, setActiveTab] = useState('season') // 'season' | 'upcoming'
  const [selectedYear, setSelectedYear] = useState(currentYear)
  const [selectedSeason, setSelectedSeason] = useState(getDefaultSeason(currentMonth))
  const [page, setPage] = useState(1)

  const [animeList, setAnimeList] = useState([])
  const [pagination, setPagination] = useState({ page: 1, total_pages: 1, total: 0 })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const fetchCalendarData = async () => {
    setLoading(true)
    setError(null)
    try {
      let res
      if (activeTab === 'season') {
        res = await getSeasonAnime(selectedYear, selectedSeason, page)
      } else {
        res = await getUpcomingAnime(page)
      }

      setAnimeList(res?.results || [])
      setPagination(res?.pagination || { page: 1, total_pages: 1, total: res?.results?.length || 0 })
    } catch (err) {
      setError('Unable to retrieve seasonal calendar from anime provider.')
      setAnimeList([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchCalendarData()
  }, [activeTab, selectedYear, selectedSeason, page])

  const handleSeasonChange = (season) => {
    setSelectedSeason(season)
    setPage(1)
  }

  const handleYearChange = (delta) => {
    const newYear = selectedYear + delta
    if (newYear >= 2000 && newYear <= 2030) {
      setSelectedYear(newYear)
      setPage(1)
    }
  }

  // Format date helper
  const formatDate = (isoString) => {
    if (!isoString) return null
    try {
      const d = new Date(isoString)
      return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })
    } catch (e) {
      return null
    }
  }

  const todayStr = new Date().toLocaleDateString(undefined, {
    weekday: 'long',
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })

  return (
    <div className="space-y-8 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-wide flex items-center gap-2.5">
            <CalendarDays className="w-7 h-7 text-purple-400" />
            Seasonal Anime Calendar
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-1 font-mono">
            Upcoming schedules, verified premiere dates, and seasonal catalog releases
          </p>
        </div>

        {/* Today Badge */}
        <div className="flex items-center gap-2 px-3.5 py-1.5 rounded-xl bg-purple-950/40 border border-purple-500/30 text-xs font-mono text-cyan-300 self-start sm:self-auto shadow-sm">
          <CalendarIcon className="w-3.5 h-3.5 text-cyan-400" />
          <span>Today: {todayStr}</span>
        </div>
      </div>

      {/* Navigation & Filter Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-4 rounded-2xl bg-[#0c0e1e] border border-purple-500/25">
        {/* Mode Toggle: Current Season vs Upcoming */}
        <div className="flex items-center gap-1.5 p-1 rounded-xl bg-purple-950/60 border border-purple-500/20 text-xs font-mono">
          <button
            onClick={() => {
              setActiveTab('season')
              setPage(1)
            }}
            type="button"
            className={`px-3 py-1.5 rounded-lg transition-all cursor-pointer ${
              activeTab === 'season'
                ? 'bg-purple-600 text-white font-bold shadow-sm'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            Seasonal Releases
          </button>
          <button
            onClick={() => {
              setActiveTab('upcoming')
              setPage(1)
            }}
            type="button"
            className={`px-3 py-1.5 rounded-lg transition-all cursor-pointer ${
              activeTab === 'upcoming'
                ? 'bg-purple-600 text-white font-bold shadow-sm'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            Upcoming Future
          </button>
        </div>

        {/* Season & Year Selectors (Active when tab is 'season') */}
        {activeTab === 'season' && (
          <div className="flex flex-wrap items-center gap-3">
            {/* Year Navigator */}
            <div className="flex items-center gap-1 bg-purple-950/40 px-2 py-1 rounded-xl border border-purple-500/20 text-xs font-mono text-white">
              <button
                onClick={() => handleYearChange(-1)}
                type="button"
                className="p-1 rounded hover:bg-purple-800 text-purple-300 cursor-pointer"
                title="Previous Year"
              >
                <ChevronLeft className="w-3.5 h-3.5" />
              </button>
              <span className="font-bold px-1.5">{selectedYear}</span>
              <button
                onClick={() => handleYearChange(1)}
                type="button"
                className="p-1 rounded hover:bg-purple-800 text-purple-300 cursor-pointer"
                title="Next Year"
              >
                <ChevronRight className="w-3.5 h-3.5" />
              </button>
            </div>

            {/* Season Pills */}
            <div className="flex items-center gap-1">
              {SEASONS.map((s) => (
                <button
                  key={s}
                  onClick={() => handleSeasonChange(s)}
                  type="button"
                  className={`px-3 py-1.5 rounded-xl text-xs font-semibold capitalize font-mono transition-all cursor-pointer ${
                    selectedSeason === s
                      ? 'bg-purple-600 text-white border border-purple-400 shadow-sm'
                      : 'bg-purple-950/30 text-slate-400 hover:text-white border border-purple-500/20'
                  }`}
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Main Calendar Grid */}
      {loading ? (
        <div className="p-16 text-center text-xs font-mono text-purple-300">
          Loading seasonal anime calendar from verified registry...
        </div>
      ) : error ? (
        <div className="p-8 rounded-2xl bg-rose-950/20 border border-rose-500/20 text-center text-rose-300 text-xs font-mono">
          {error}
        </div>
      ) : animeList.length === 0 ? (
        <div className="p-12 rounded-3xl bg-[#0c0e1e] border border-purple-500/20 text-center space-y-3 max-w-md mx-auto">
          <CalendarIcon className="w-8 h-8 text-purple-400 mx-auto" />
          <h3 className="text-base font-bold text-white">No Releases Scheduled</h3>
          <p className="text-xs text-slate-400">
            No anime premieres currently scheduled for {selectedSeason} {selectedYear}.
          </p>
        </div>
      ) : (
        <div className="space-y-6">
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4">
            {animeList.map((anime) => {
              const formattedDate = formatDate(anime.aired_from) || anime.release_label

              return (
                <Link
                  key={anime.mal_id}
                  to={`/anime/${anime.mal_id}`}
                  className="rounded-2xl overflow-hidden bg-[#0c0e1e] border border-purple-500/20 hover:border-purple-400/60 transition-all duration-200 group flex flex-col justify-between shadow-sm hover:shadow-[0_0_20px_rgba(168,85,247,0.25)]"
                >
                  <div>
                    {/* Poster Image */}
                    <div className="aspect-[3/4] relative bg-purple-950 overflow-hidden">
                      {anime.poster_url ? (
                        <img
                          src={anime.poster_url}
                          alt={anime.title}
                          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                        />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center text-purple-400">
                          <Tv className="w-8 h-8" />
                        </div>
                      )}

                      {/* Format Badge Top Left */}
                      <span className="absolute top-2 left-2 px-2 py-0.5 rounded-lg bg-black/75 backdrop-blur-md border border-purple-500/30 text-[10px] font-mono text-purple-300 font-bold uppercase">
                        {anime.anime_type || 'TV'}
                      </span>
                    </div>

                    {/* Content */}
                    <div className="p-3 space-y-1">
                      <h3 className="text-xs font-semibold text-white group-hover:text-purple-300 transition-colors line-clamp-2">
                        {anime.title}
                      </h3>
                    </div>
                  </div>

                  {/* Release Label / Date Bottom Pill */}
                  <div className="p-3 pt-0">
                    <div className="p-1.5 rounded-xl bg-purple-950/40 border border-purple-500/20 flex items-center justify-between text-[10px] font-mono">
                      <span className="text-cyan-400 font-semibold truncate">
                        {formattedDate}
                      </span>
                    </div>
                  </div>
                </Link>
              )
            })}
          </div>

          {/* Pagination */}
          {pagination.total_pages > 1 && (
            <div className="flex items-center justify-center gap-3 pt-4 text-xs font-mono">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page <= 1}
                type="button"
                className="px-3 py-1.5 rounded-xl bg-purple-950/40 border border-purple-500/30 text-purple-300 disabled:opacity-30 cursor-pointer"
              >
                &larr; Prev
              </button>
              <span className="text-slate-400">
                Page {page} of {pagination.total_pages}
              </span>
              <button
                onClick={() => setPage((p) => Math.min(pagination.total_pages, p + 1))}
                disabled={page >= pagination.total_pages}
                type="button"
                className="px-3 py-1.5 rounded-xl bg-purple-950/40 border border-purple-500/30 text-purple-300 disabled:opacity-30 cursor-pointer"
              >
                Next &rarr;
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default CalendarPage

import React, { useEffect, useState, useCallback, useRef } from 'react'
import { useSearchParams, Link } from 'react-router-dom'
import {
  Search,
  Filter,
  Sparkles,
  ChevronLeft,
  ChevronRight,
  SlidersHorizontal,
  Flame,
  Star,
  Tv,
  Film,
  Calendar,
  X,
  RotateCcw,
  Bot,
  Volume2,
  Check,
  Layers,
  ArrowUpDown,
  Clock,
} from 'lucide-react'
import { browseAnime, getDiscoveryFilters } from '../api/anime'
import AnimeCard from '../components/common/AnimeCard'
import SearchBar from '../components/common/SearchBar'
import ErrorState from '../components/common/ErrorState'
import EmptyState from '../components/common/EmptyState'
import { CardSkeleton } from '../components/common/LoadingSkeleton'

const DEFAULT_GENRES = [
  'Action', 'Adventure', 'Comedy', 'Drama', 'Fantasy', 'Horror',
  'Mystery', 'Psychological', 'Romance', 'Sci-Fi', 'Shounen',
  'Slice of Life', 'Sports', 'Supernatural', 'Suspense', 'Award Winning'
]

const FORMAT_OPTIONS = [
  { label: 'All Formats', value: '' },
  { label: 'TV Series', value: 'tv' },
  { label: 'Movie', value: 'movie' },
  { label: 'OVA', value: 'ova' },
  { label: 'ONA', value: 'ona' },
  { label: 'Special', value: 'special' },
]

const STATUS_OPTIONS = [
  { label: 'All Statuses', value: '' },
  { label: 'Currently Airing', value: 'airing' },
  { label: 'Finished Airing', value: 'complete' },
  { label: 'Upcoming', value: 'upcoming' },
]

const SORT_OPTIONS = [
  { key: '-score', label: 'Highest Score' },
  { key: 'score', label: 'Lowest Score' },
  { key: '-start_date', label: 'Recently Released' },
  { key: 'start_date', label: 'Oldest Releases' },
  { key: '-episodes', label: 'Most Episodes' },
  { key: 'title', label: 'Title (A-Z)' },
  { key: 'relevance', label: 'Relevance' },
]

export const DiscoverPage = () => {
  const [searchParams, setSearchParams] = useSearchParams()

  // Primary Query & Filter States
  const [query, setQuery] = useState(searchParams.get('q') || '')
  const [selectedGenres, setSelectedGenres] = useState(() => {
    const g = searchParams.get('genres')
    return g ? g.split(',').filter(Boolean) : []
  })
  const [excludedGenres, setExcludedGenres] = useState(() => {
    const eg = searchParams.get('exclude_genres')
    return eg ? eg.split(',').filter(Boolean) : []
  })
  const [format, setFormat] = useState(searchParams.get('format') || '')
  const [yearFrom, setYearFrom] = useState(searchParams.get('year_from') || '')
  const [yearTo, setYearTo] = useState(searchParams.get('year_to') || '')
  const [minScore, setMinScore] = useState(searchParams.get('min_score') || '')
  const [status, setStatus] = useState(searchParams.get('status') || '')
  const [minEpisodes, setMinEpisodes] = useState(searchParams.get('min_episodes') || '')
  const [maxEpisodes, setMaxEpisodes] = useState(searchParams.get('max_episodes') || '')
  const [audioLanguage, setAudioLanguage] = useState(searchParams.get('audio_language') || '')
  const [sort, setSort] = useState(searchParams.get('sort') || '-score')
  const [personalized, setPersonalized] = useState(searchParams.get('personalized') === 'true')
  const [hideTracked, setHideTracked] = useState(searchParams.get('hide_tracked') === 'true')
  const [page, setPage] = useState(parseInt(searchParams.get('page') || '1', 10))

  // UI Panels
  const [isFilterDrawerOpen, setIsFilterDrawerOpen] = useState(false)
  const [availableFilters, setAvailableFilters] = useState(null)

  // Results & States
  const [items, setItems] = useState([])
  const [pagination, setPagination] = useState({ page: 1, total_pages: 1, total: 0 })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Fetch available filter options (verified languages, etc.)
  useEffect(() => {
    const fetchFilters = async () => {
      try {
        const data = await getDiscoveryFilters()
        setAvailableFilters(data)
      } catch (err) {
        // Fallback gracefully
      }
    }
    fetchFilters()
  }, [])

  // Sync state to URL search params
  const syncParamsToUrl = useCallback(() => {
    const nextParams = {}
    if (query.trim()) nextParams.q = query.trim()
    if (selectedGenres.length > 0) nextParams.genres = selectedGenres.join(',')
    if (excludedGenres.length > 0) nextParams.exclude_genres = excludedGenres.join(',')
    if (format) nextParams.format = format
    if (yearFrom) nextParams.year_from = yearFrom
    if (yearTo) nextParams.year_to = yearTo
    if (minScore) nextParams.min_score = minScore
    if (status) nextParams.status = status
    if (minEpisodes) nextParams.min_episodes = minEpisodes
    if (maxEpisodes) nextParams.max_episodes = maxEpisodes
    if (audioLanguage) nextParams.audio_language = audioLanguage
    if (sort && sort !== '-score') nextParams.sort = sort
    if (personalized) nextParams.personalized = 'true'
    if (hideTracked) nextParams.hide_tracked = 'true'
    if (page > 1) nextParams.page = page.toString()

    setSearchParams(nextParams, { replace: true })
  }, [
    query,
    selectedGenres,
    excludedGenres,
    format,
    yearFrom,
    yearTo,
    minScore,
    status,
    minEpisodes,
    maxEpisodes,
    audioLanguage,
    sort,
    personalized,
    hideTracked,
    page,
    setSearchParams,
  ])

  // Load Catalog Data
  const loadData = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const browseParams = {
        page,
        sort,
      }
      if (query.trim().length >= 2) browseParams.q = query.trim()
      if (selectedGenres.length > 0) browseParams.genres = selectedGenres.join(',')
      if (excludedGenres.length > 0) browseParams.exclude_genres = excludedGenres.join(',')
      if (format) browseParams.format = format
      if (yearFrom) browseParams.year_from = parseInt(yearFrom, 10)
      if (yearTo) browseParams.year_to = parseInt(yearTo, 10)
      if (minScore) browseParams.min_score = parseFloat(minScore)
      if (status) browseParams.status = status
      if (minEpisodes) browseParams.min_episodes = parseInt(minEpisodes, 10)
      if (maxEpisodes) browseParams.max_episodes = parseInt(maxEpisodes, 10)
      if (audioLanguage) browseParams.audio_language = audioLanguage
      if (personalized) browseParams.personalized = true
      if (hideTracked) browseParams.hide_tracked = true

      const res = await browseAnime(browseParams)
      setItems(res?.results || [])
      setPagination(res?.pagination || { page: 1, total_pages: 1, total: res?.results?.length || 0 })
    } catch (err) {
      setError(err.message || 'Unable to retrieve anime records matching your filter criteria.')
      setItems([])
    } finally {
      setLoading(false)
    }
  }, [
    query,
    selectedGenres,
    excludedGenres,
    format,
    yearFrom,
    yearTo,
    minScore,
    status,
    minEpisodes,
    maxEpisodes,
    audioLanguage,
    sort,
    personalized,
    hideTracked,
    page,
  ])

  useEffect(() => {
    syncParamsToUrl()
    loadData()
  }, [syncParamsToUrl, loadData])

  // Debounced Title Search
  const searchDebounceRef = useRef(null)
  const handleSearchChange = (val) => {
    if (searchDebounceRef.current) clearTimeout(searchDebounceRef.current)
    if (val === '') {
      setQuery('')
      setPage(1)
      return
    }
    searchDebounceRef.current = setTimeout(() => {
      setQuery(val.trim())
      setPage(1)
    }, 350)
  }

  const handleSearchSubmit = (searchTerm) => {
    setQuery(searchTerm.trim())
    setPage(1)
  }

  // Genre Toggles
  const toggleGenreInclude = (genreName) => {
    setPage(1)
    if (selectedGenres.includes(genreName)) {
      setSelectedGenres((prev) => prev.filter((g) => g !== genreName))
    } else {
      setSelectedGenres((prev) => [...prev, genreName])
      setExcludedGenres((prev) => prev.filter((g) => g !== genreName))
    }
  }

  const toggleGenreExclude = (genreName) => {
    setPage(1)
    if (excludedGenres.includes(genreName)) {
      setExcludedGenres((prev) => prev.filter((g) => g !== genreName))
    } else {
      setExcludedGenres((prev) => [...prev, genreName])
      setSelectedGenres((prev) => prev.filter((g) => g !== genreName))
    }
  }

  // Reset All Filters
  const handleResetFilters = () => {
    setQuery('')
    setSelectedGenres([])
    setExcludedGenres([])
    setFormat('')
    setYearFrom('')
    setYearTo('')
    setMinScore('')
    setStatus('')
    setMinEpisodes('')
    setMaxEpisodes('')
    setAudioLanguage('')
    setSort('-score')
    setPage(1)
    setSearchParams({})
  }

  // Active filter count for badge
  const activeFiltersCount =
    (query ? 1 : 0) +
    selectedGenres.length +
    excludedGenres.length +
    (format ? 1 : 0) +
    (yearFrom || yearTo ? 1 : 0) +
    (minScore ? 1 : 0) +
    (status ? 1 : 0) +
    (minEpisodes || maxEpisodes ? 1 : 0) +
    (audioLanguage ? 1 : 0)

  const verifiedLanguagesList = availableFilters?.verified_languages || [
    'Japanese', 'English', 'Hindi', 'Tamil', 'Telugu', 'Malayalam'
  ]

  return (
    <div className="space-y-6">
      {/* ======================================================== */}
      {/* 1. DISCOVERY HEADER & QUICK ACTION SHORTCUTS              */}
      {/* ======================================================== */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2.5">
            <span className="w-2.5 h-2.5 rounded-full bg-purple-500 shadow-[0_0_12px_rgba(168,85,247,0.9)] animate-pulse" />
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-wide">
              Advanced Anime Discovery
            </h1>
          </div>
          <p className="text-xs sm:text-sm text-slate-400 mt-1 font-mono">
            {pagination.total > 0
              ? `${pagination.total} anime titles discovered across verified records`
              : 'Explore and filter anime by verified streaming audio, score, format, and genres'}
          </p>
        </div>

        {/* Quick Discovery Presets */}
        <div className="flex items-center gap-2 overflow-x-auto pb-1 sm:pb-0">
          <button
            onClick={() => {
              handleResetFilters()
              setSort('-score')
            }}
            type="button"
            className="px-3 py-1.5 rounded-xl bg-purple-950/40 hover:bg-purple-900/40 border border-purple-500/25 text-xs font-mono text-purple-200 transition-colors flex items-center gap-1.5 shrink-0 cursor-pointer"
          >
            <Star className="w-3.5 h-3.5 text-amber-400 fill-amber-400" />
            <span>Top Rated</span>
          </button>

          <button
            onClick={() => {
              handleResetFilters()
              setSort('-start_date')
            }}
            type="button"
            className="px-3 py-1.5 rounded-xl bg-purple-950/40 hover:bg-purple-900/40 border border-purple-500/25 text-xs font-mono text-purple-200 transition-colors flex items-center gap-1.5 shrink-0 cursor-pointer"
          >
            <Flame className="w-3.5 h-3.5 text-rose-400" />
            <span>Trending Airing</span>
          </button>

          <Link
            to="/ryuk"
            className="px-3 py-1.5 rounded-xl bg-gradient-to-r from-purple-900/50 to-indigo-900/50 hover:from-purple-800/50 hover:to-indigo-800/50 border border-purple-400/40 text-xs font-mono text-cyan-300 transition-all flex items-center gap-1.5 shrink-0 shadow-[0_0_12px_rgba(168,85,247,0.2)]"
          >
            <Bot className="w-3.5 h-3.5 text-cyan-400" />
            <span>RYUK Recommendations</span>
          </Link>
        </div>
      </div>

      {/* ======================================================== */}
      {/* 2. SEARCH BAR & CONTROLS STRIP                           */}
      {/* ======================================================== */}
      <div className="grid grid-cols-1 sm:grid-cols-12 gap-3 items-center">
        {/* Search input */}
        <div className="sm:col-span-6 lg:col-span-7">
          <SearchBar
            value={query}
            placeholder="Search anime title in English or Japanese (e.g. Demon Slayer, 鬼滅)..."
            onSearch={handleSearchSubmit}
            onChange={handleSearchChange}
          />
        </div>

        {/* Filter Drawer Trigger Button */}
        <div className="sm:col-span-3 lg:col-span-2">
          <button
            onClick={() => setIsFilterDrawerOpen((prev) => !prev)}
            type="button"
            className={`w-full h-11 px-3.5 rounded-xl border text-xs font-mono font-semibold transition-all flex items-center justify-center gap-2 cursor-pointer ${
              isFilterDrawerOpen || activeFiltersCount > 0
                ? 'bg-purple-600 border-purple-400 text-white shadow-[0_0_15px_rgba(168,85,247,0.4)]'
                : 'bg-purple-950/40 border-purple-500/30 text-slate-300 hover:text-white hover:bg-purple-900/40'
            }`}
          >
            <SlidersHorizontal className="w-4 h-4 text-white" />
            <span>Filters</span>
            {activeFiltersCount > 0 && (
              <span className="px-1.5 py-0.5 rounded-full bg-white text-purple-900 text-[10px] font-bold">
                {activeFiltersCount}
              </span>
            )}
          </button>
        </div>

        {/* Sorting Dropdown */}
        <div className="sm:col-span-3 lg:col-span-3">
          <div className="relative">
            <select
              value={sort}
              onChange={(e) => {
                setSort(e.target.value)
                setPage(1)
              }}
              className="w-full h-11 px-3.5 rounded-xl bg-[#0c0e1e] border border-purple-500/30 text-white text-xs font-mono focus:outline-none focus:border-purple-400 cursor-pointer appearance-none"
            >
              {SORT_OPTIONS.map((opt) => (
                <option key={opt.key} value={opt.key} className="bg-[#0c0e1e] text-white">
                  Sort: {opt.label}
                </option>
              ))}
            </select>
            <ArrowUpDown className="w-3.5 h-3.5 text-purple-400 absolute right-3 top-3.5 pointer-events-none" />
          </div>
        </div>
      </div>

      {/* ======================================================== */}
      {/* 2.5 SMART PERSONALIZATION QUICK CONTROLS                 */}
      {/* ======================================================== */}
      <div className="flex flex-wrap items-center justify-between gap-3 px-4 py-2.5 rounded-2xl bg-[#0c0e1e]/80 border border-purple-500/25">
        <div className="flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-cyan-400" />
          <span className="text-xs font-mono text-purple-200">Smart Personalization</span>
        </div>
        <div className="flex flex-wrap items-center gap-2.5">
          <button
            type="button"
            onClick={() => {
              setPersonalized((prev) => !prev)
              setPage(1)
            }}
            className={`px-3 py-1.5 rounded-xl text-xs font-mono transition-all flex items-center gap-1.5 cursor-pointer ${
              personalized
                ? 'bg-gradient-to-r from-purple-600 to-indigo-600 text-white font-semibold border border-purple-400 shadow-[0_0_15px_rgba(168,85,247,0.4)]'
                : 'bg-purple-950/40 text-slate-400 border border-purple-500/20 hover:text-white'
            }`}
          >
            <Sparkles className={`w-3.5 h-3.5 ${personalized ? 'text-cyan-300' : 'text-slate-400'}`} />
            <span>Personalized For You: {personalized ? 'ON' : 'OFF'}</span>
          </button>

          <button
            type="button"
            onClick={() => {
              setHideTracked((prev) => !prev)
              setPage(1)
            }}
            className={`px-3 py-1.5 rounded-xl text-xs font-mono transition-all flex items-center gap-1.5 cursor-pointer ${
              hideTracked
                ? 'bg-purple-600 text-white font-semibold border border-purple-400 shadow-[0_0_15px_rgba(168,85,247,0.4)]'
                : 'bg-purple-950/40 text-slate-400 border border-purple-500/20 hover:text-white'
            }`}
          >
            <span>Hide Watched: {hideTracked ? 'ON' : 'OFF'}</span>
          </button>
        </div>
      </div>

      {/* ======================================================== */}
      {/* 3. EXPANDABLE ADVANCED FILTER PANEL                      */}
      {/* ======================================================== */}
      {isFilterDrawerOpen && (
        <div className="p-5 rounded-2xl bg-[#0c0e1e]/95 backdrop-blur-xl border border-purple-500/35 shadow-[0_10px_35px_rgba(0,0,0,0.8),0_0_20px_rgba(168,85,247,0.15)] space-y-6 text-xs transition-all">
          <div className="flex items-center justify-between border-b border-purple-500/20 pb-3">
            <span className="font-bold text-white text-sm flex items-center gap-2">
              <Filter className="w-4 h-4 text-purple-400" /> Advanced Discovery Matrix
            </span>
            <div className="flex items-center gap-3">
              {activeFiltersCount > 0 && (
                <button
                  onClick={handleResetFilters}
                  type="button"
                  className="inline-flex items-center gap-1 text-[11px] font-mono text-rose-400 hover:text-rose-300 cursor-pointer"
                >
                  <RotateCcw className="w-3 h-3" /> Reset All
                </button>
              )}
              <button
                onClick={() => setIsFilterDrawerOpen(false)}
                type="button"
                className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-purple-900/30 cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Filter Controls Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {/* Format Selection */}
            <div className="space-y-2">
              <label className="block text-slate-300 font-mono text-[11px] font-semibold uppercase tracking-wider">
                Anime Format
              </label>
              <div className="grid grid-cols-2 gap-1.5">
                {FORMAT_OPTIONS.map((f) => (
                  <button
                    key={f.value}
                    onClick={() => {
                      setFormat(f.value)
                      setPage(1)
                    }}
                    type="button"
                    className={`py-1.5 px-2.5 rounded-lg text-left text-xs transition-all cursor-pointer truncate ${
                      format === f.value
                        ? 'bg-purple-600 text-white font-semibold shadow-[0_0_10px_rgba(168,85,247,0.3)]'
                        : 'bg-purple-950/30 text-slate-400 hover:text-white border border-purple-500/15'
                    }`}
                  >
                    {f.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Airing Status */}
            <div className="space-y-2">
              <label className="block text-slate-300 font-mono text-[11px] font-semibold uppercase tracking-wider">
                Airing Status
              </label>
              <div className="grid grid-cols-2 gap-1.5">
                {STATUS_OPTIONS.map((s) => (
                  <button
                    key={s.value}
                    onClick={() => {
                      setStatus(s.value)
                      setPage(1)
                    }}
                    type="button"
                    className={`py-1.5 px-2.5 rounded-lg text-left text-xs transition-all cursor-pointer truncate ${
                      status === s.value
                        ? 'bg-cyan-600 text-white font-semibold shadow-[0_0_10px_rgba(6,182,212,0.3)]'
                        : 'bg-purple-950/30 text-slate-400 hover:text-white border border-purple-500/15'
                    }`}
                  >
                    {s.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Release Year Range */}
            <div className="space-y-2">
              <label className="block text-slate-300 font-mono text-[11px] font-semibold uppercase tracking-wider flex items-center gap-1.5">
                <Calendar className="w-3.5 h-3.5 text-purple-400" /> Release Year Range
              </label>
              <div className="flex items-center gap-2">
                <input
                  type="number"
                  placeholder="From (e.g. 2015)"
                  min={1950}
                  max={2030}
                  value={yearFrom}
                  onChange={(e) => {
                    setYearFrom(e.target.value)
                    setPage(1)
                  }}
                  className="w-full px-2.5 py-1.5 rounded-lg bg-purple-950/40 border border-purple-500/30 text-white text-xs placeholder:text-slate-500 focus:outline-none focus:border-purple-400 font-mono"
                />
                <span className="text-slate-500 font-mono">-</span>
                <input
                  type="number"
                  placeholder="To (e.g. 2026)"
                  min={1950}
                  max={2030}
                  value={yearTo}
                  onChange={(e) => {
                    setYearTo(e.target.value)
                    setPage(1)
                  }}
                  className="w-full px-2.5 py-1.5 rounded-lg bg-purple-950/40 border border-purple-500/30 text-white text-xs placeholder:text-slate-500 focus:outline-none focus:border-purple-400 font-mono"
                />
              </div>
            </div>

            {/* Verified Audio Language (From Local DB) */}
            <div className="space-y-2">
              <label className="block text-slate-300 font-mono text-[11px] font-semibold uppercase tracking-wider flex items-center justify-between">
                <span className="flex items-center gap-1.5">
                  <Volume2 className="w-3.5 h-3.5 text-cyan-400" /> Verified Audio Track
                </span>
                <span className="text-[9px] text-cyan-300 font-normal">Official Only</span>
              </label>
              <div className="relative">
                <select
                  value={audioLanguage}
                  onChange={(e) => {
                    setAudioLanguage(e.target.value)
                    setPage(1)
                  }}
                  className="w-full h-9 px-3 rounded-lg bg-purple-950/40 border border-purple-500/30 text-white text-xs font-mono focus:outline-none focus:border-purple-400 cursor-pointer"
                >
                  <option value="" className="bg-[#0c0e1e] text-slate-300">
                    All Verified Audio Languages
                  </option>
                  {verifiedLanguagesList.map((lang) => (
                    <option key={lang} value={lang} className="bg-[#0c0e1e] text-white">
                      {lang} Dub / Audio (Verified)
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Minimum Community Score */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <label className="text-slate-300 font-mono text-[11px] font-semibold uppercase tracking-wider">
                  Min Community Score
                </label>
                <span className="text-amber-300 font-mono font-bold">
                  {minScore ? `★ ${minScore}+` : 'Any Score'}
                </span>
              </div>
              <input
                type="range"
                min="0"
                max="9.5"
                step="0.5"
                value={minScore || 0}
                onChange={(e) => {
                  const val = parseFloat(e.target.value)
                  setMinScore(val > 0 ? val.toString() : '')
                  setPage(1)
                }}
                className="w-full accent-purple-500 cursor-pointer"
              />
              <div className="flex justify-between text-[9px] font-mono text-slate-500">
                <span>0.0</span>
                <span>5.0</span>
                <span>7.5</span>
                <span>9.0+</span>
              </div>
            </div>

            {/* Episode Count Range */}
            <div className="space-y-2">
              <label className="block text-slate-300 font-mono text-[11px] font-semibold uppercase tracking-wider flex items-center gap-1.5">
                <Clock className="w-3.5 h-3.5 text-purple-400" /> Episode Count Range
              </label>
              <div className="flex items-center gap-2">
                <input
                  type="number"
                  placeholder="Min eps"
                  min={1}
                  value={minEpisodes}
                  onChange={(e) => {
                    setMinEpisodes(e.target.value)
                    setPage(1)
                  }}
                  className="w-full px-2.5 py-1.5 rounded-lg bg-purple-950/40 border border-purple-500/30 text-white text-xs placeholder:text-slate-500 focus:outline-none focus:border-purple-400 font-mono"
                />
                <span className="text-slate-500 font-mono">-</span>
                <input
                  type="number"
                  placeholder="Max eps"
                  min={1}
                  value={maxEpisodes}
                  onChange={(e) => {
                    setMaxEpisodes(e.target.value)
                    setPage(1)
                  }}
                  className="w-full px-2.5 py-1.5 rounded-lg bg-purple-950/40 border border-purple-500/30 text-white text-xs placeholder:text-slate-500 focus:outline-none focus:border-purple-400 font-mono"
                />
              </div>
            </div>
          </div>

          {/* Genre Matrix Multi-Selector */}
          <div className="border-t border-purple-500/20 pt-4 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-slate-300 font-mono text-[11px] font-semibold uppercase tracking-wider flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-pink-400" /> Include / Exclude Genres
              </span>
              <span className="text-[10px] font-mono text-slate-400">
                Click once to Include • Right-click or long-press to Exclude
              </span>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {(availableFilters?.genres || DEFAULT_GENRES).map((genre) => {
                const isIncluded = selectedGenres.includes(genre)
                const isExcluded = excludedGenres.includes(genre)
                return (
                  <button
                    key={genre}
                    type="button"
                    onClick={() => toggleGenreInclude(genre)}
                    onContextMenu={(e) => {
                      e.preventDefault()
                      toggleGenreExclude(genre)
                    }}
                    className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-all cursor-pointer flex items-center gap-1 ${
                      isIncluded
                        ? 'bg-purple-600 text-white shadow-[0_0_10px_rgba(168,85,247,0.4)] border border-purple-400'
                        : isExcluded
                        ? 'bg-rose-950/60 text-rose-300 line-through border border-rose-500/40'
                        : 'bg-purple-950/30 text-slate-400 hover:text-white border border-purple-500/20'
                    }`}
                  >
                    <span>{genre}</span>
                    {isIncluded && <Check className="w-3 h-3 text-white" />}
                    {isExcluded && <X className="w-3 h-3 text-rose-400" />}
                  </button>
                )
              })}
            </div>
          </div>
        </div>
      )}

      {/* ======================================================== */}
      {/* 4. ACTIVE FILTER CHIPS STRIP                             */}
      {/* ======================================================== */}
      {activeFiltersCount > 0 && (
        <div className="flex flex-wrap items-center gap-2 pt-1 pb-1">
          <span className="text-[11px] font-mono text-slate-400 mr-1">Active Filters:</span>

          {query && (
            <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-purple-950/50 border border-purple-500/30 text-purple-300 text-xs font-mono">
              Search: "{query}"
              <button onClick={() => setQuery('')} className="hover:text-white cursor-pointer">
                <X className="w-3 h-3" />
              </button>
            </span>
          )}

          {selectedGenres.map((g) => (
            <span
              key={`inc-${g}`}
              className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-purple-950/50 border border-purple-500/40 text-purple-200 text-xs font-mono"
            >
              +{g}
              <button onClick={() => toggleGenreInclude(g)} className="hover:text-white cursor-pointer">
                <X className="w-3 h-3" />
              </button>
            </span>
          ))}

          {excludedGenres.map((eg) => (
            <span
              key={`exc-${eg}`}
              className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-rose-950/50 border border-rose-500/40 text-rose-300 text-xs font-mono line-through"
            >
              -{eg}
              <button onClick={() => toggleGenreExclude(eg)} className="hover:text-white cursor-pointer">
                <X className="w-3 h-3" />
              </button>
            </span>
          ))}

          {format && (
            <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-cyan-950/50 border border-cyan-500/30 text-cyan-300 text-xs font-mono">
              Format: {format.toUpperCase()}
              <button onClick={() => setFormat('')} className="hover:text-white cursor-pointer">
                <X className="w-3 h-3" />
              </button>
            </span>
          )}

          {audioLanguage && (
            <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-emerald-950/50 border border-emerald-500/30 text-emerald-300 text-xs font-mono">
              Audio: {audioLanguage}
              <button onClick={() => setAudioLanguage('')} className="hover:text-white cursor-pointer">
                <X className="w-3 h-3" />
              </button>
            </span>
          )}

          {minScore && (
            <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-amber-950/50 border border-amber-500/30 text-amber-300 text-xs font-mono">
              Score: ≥ {minScore}★
              <button onClick={() => setMinScore('')} className="hover:text-white cursor-pointer">
                <X className="w-3 h-3" />
              </button>
            </span>
          )}

          {(yearFrom || yearTo) && (
            <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-purple-950/50 border border-purple-500/30 text-purple-300 text-xs font-mono">
              Year: {yearFrom || 'Early'}–{yearTo || 'Current'}
              <button
                onClick={() => {
                  setYearFrom('')
                  setYearTo('')
                }}
                className="hover:text-white cursor-pointer"
              >
                <X className="w-3 h-3" />
              </button>
            </span>
          )}

          {status && (
            <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-blue-950/50 border border-blue-500/30 text-blue-300 text-xs font-mono">
              Status: {status}
              <button onClick={() => setStatus('')} className="hover:text-white cursor-pointer">
                <X className="w-3 h-3" />
              </button>
            </span>
          )}

          <button
            onClick={handleResetFilters}
            type="button"
            className="text-[11px] font-mono text-purple-400 hover:text-purple-200 underline cursor-pointer ml-1"
          >
            Clear All
          </button>
        </div>
      )}

      {/* ======================================================== */}
      {/* 5. ANIME GRID / SKELETON / EMPTY / ERROR STATES           */}
      {/* ======================================================== */}
      {loading ? (
        <CardSkeleton count={12} />
      ) : error ? (
        <ErrorState
          title="Catalog Query Error"
          message={error}
          onRetry={loadData}
        />
      ) : items.length === 0 ? (
        <EmptyState
          title="No Matching Anime Found"
          description={
            query
              ? `No anime records found matching "${query}" with your active filters. Try clearing some constraints or checking the spelling.`
              : 'No anime records match the selected combination of filters. Try broadening your criteria.'
          }
          actionLabel="Clear All Filters"
          onAction={handleResetFilters}
        />
      ) : (
        <div className="space-y-6">
          {/* Anime Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 2xl:grid-cols-6 gap-5 sm:gap-6">
            {items.map((anime, index) => (
              <AnimeCard
                key={anime.mal_id || index}
                anime={anime}
                priority={index < 6}
              />
            ))}
          </div>

          {/* Pagination Controls */}
          {pagination.total_pages > 1 && (
            <div className="flex items-center justify-center gap-3 pt-6 border-t border-purple-500/20">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page <= 1}
                type="button"
                className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-purple-950/40 border border-purple-500/30 text-purple-200 text-sm font-semibold hover:bg-purple-900/40 disabled:opacity-40 disabled:pointer-events-none transition-all cursor-pointer"
              >
                <ChevronLeft className="w-4 h-4" />
                <span>Previous</span>
              </button>

              <span className="text-xs font-mono text-purple-300 px-3 py-1.5 rounded-lg bg-purple-950/60 border border-purple-500/20">
                Page {page} of {pagination.total_pages}
              </span>

              <button
                onClick={() => setPage((p) => Math.min(pagination.total_pages, p + 1))}
                disabled={page >= pagination.total_pages}
                type="button"
                className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-purple-950/40 border border-purple-500/30 text-purple-200 text-sm font-semibold hover:bg-purple-900/40 disabled:opacity-40 disabled:pointer-events-none transition-all cursor-pointer"
              >
                <span>Next</span>
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default DiscoverPage

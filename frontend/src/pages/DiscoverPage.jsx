import React, { useEffect, useState, useCallback, useRef } from 'react'
import { useSearchParams } from 'react-router-dom'
import {
  Search,
  Filter,
  Sparkles,
  ChevronLeft,
  ChevronRight,
  SlidersHorizontal,
  Flame,
} from 'lucide-react'
import { searchAnime, getTrendingAnime, browseAnime } from '../api/anime'
import AnimeCard from '../components/common/AnimeCard'
import SearchBar from '../components/common/SearchBar'
import ErrorState from '../components/common/ErrorState'
import EmptyState from '../components/common/EmptyState'
import { CardSkeleton } from '../components/common/LoadingSkeleton'

const GENRES = [
  'All',
  'Action',
  'Adventure',
  'Comedy',
  'Drama',
  'Fantasy',
  'Sci-Fi',
  'Mystery',
  'Romance',
  'Supernatural',
  'Shounen',
  'Slice of Life',
]

const FORMATS = [
  { label: 'All Formats', value: '' },
  { label: 'TV Series', value: 'tv' },
  { label: 'Movie', value: 'movie' },
  { label: 'OVA / Special', value: 'ova' },
]

export const DiscoverPage = () => {
  const [searchParams, setSearchParams] = useSearchParams()
  const initialQuery = searchParams.get('q') || ''

  const [query, setQuery] = useState(initialQuery)
  const [selectedGenre, setSelectedGenre] = useState('All')
  const [selectedFormat, setSelectedFormat] = useState('')
  const [page, setPage] = useState(1)

  useEffect(() => {
    const qParam = searchParams.get('q') || ''
    if (qParam !== query) {
      setQuery(qParam)
      setPage(1)
    }
  }, [searchParams])

  const [items, setItems] = useState([])
  const [pagination, setPagination] = useState({ page: 1, total_pages: 1, total: 0 })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [mode, setMode] = useState('trending') // 'trending' | 'search' | 'browse'

  const loadData = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      let res
      if (query.trim().length >= 2) {
        setMode('search')
        res = await searchAnime(query.trim(), page)
      } else if (selectedGenre !== 'All' || selectedFormat) {
        setMode('browse')
        const filterParams = { page }
        if (selectedGenre !== 'All') filterParams.genre = selectedGenre
        if (selectedFormat) filterParams.type = selectedFormat
        res = await browseAnime(filterParams)
      } else {
        setMode('trending')
        res = await getTrendingAnime(page)
      }

      setItems(res?.results || [])
      setPagination(res?.pagination || { page: 1, total_pages: 1, total: res?.results?.length || 0 })
    } catch (err) {
      setError(err.message || 'Unable to retrieve anime records from the provider.')
      setItems([])
    } finally {
      setLoading(false)
    }
  }, [query, selectedGenre, selectedFormat, page])

  useEffect(() => {
    loadData()
  }, [loadData])

  const searchDebounceRef = useRef(null)

  const handleSearchChange = (val) => {
    if (searchDebounceRef.current) clearTimeout(searchDebounceRef.current)
    if (val === '') {
      handleSearchSubmit('')
      return
    }
    if (val.trim().length >= 2) {
      searchDebounceRef.current = setTimeout(() => {
        handleSearchSubmit(val.trim())
      }, 350)
    }
  }

  const handleSearchSubmit = (searchTerm) => {
    setQuery(searchTerm)
    setPage(1)
    if (searchTerm) {
      setSearchParams({ q: searchTerm })
    } else {
      setSearchParams({})
    }
  }

  const handleGenreSelect = (genre) => {
    setSelectedGenre(genre)
    setPage(1)
  }

  const handleFormatSelect = (fmt) => {
    setSelectedFormat(fmt)
    setPage(1)
  }

  const currentSource = items.length > 0 && items[0]?.metadata_source
    ? items[0].metadata_source.toUpperCase()
    : 'UPSTREAM'

  return (
    <div className="space-y-6">
      {/* Header section */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-wide flex items-center gap-2.5">
            <span className="w-2.5 h-2.5 rounded-full bg-purple-500 shadow-[0_0_10px_rgba(168,85,247,0.8)]"></span>
            Discover Anime
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-1 font-mono">
            {mode === 'search'
              ? `Results for "${query}" (${pagination.total || items.length} found) • Source: ${currentSource}`
              : mode === 'browse'
              ? `Filtered catalog (${pagination.total || items.length} found) • Source: ${currentSource}`
              : `Trending Anime • Live ${currentSource} Stream`}
          </p>
        </div>

        {/* Search Bar */}
        <div className="w-full sm:w-80">
          <SearchBar
            value={query}
            placeholder="Search anime title..."
            onSearch={handleSearchSubmit}
            onChange={handleSearchChange}
          />
        </div>
      </div>

      {/* Genre Pills Filter Strip */}
      <div className="flex items-center gap-2 overflow-x-auto pb-2 scrollbar-none">
        {GENRES.map((genre) => {
          const isSelected = selectedGenre === genre
          return (
            <button
              key={genre}
              onClick={() => handleGenreSelect(genre)}
              type="button"
              className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition-all duration-200 cursor-pointer ${
                isSelected
                  ? 'bg-purple-600 text-white shadow-[0_0_12px_rgba(168,85,247,0.5)] border border-purple-400'
                  : 'bg-purple-950/30 text-slate-400 hover:text-slate-200 border border-purple-500/20 hover:border-purple-400/40'
              }`}
            >
              {genre}
            </button>
          )
        })}
      </div>

      {/* Formats and Score filters row */}
      <div className="flex flex-wrap items-center justify-between gap-3 text-xs">
        <div className="flex items-center gap-2">
          <SlidersHorizontal className="w-3.5 h-3.5 text-purple-400" />
          <span className="text-slate-400 font-mono">Format:</span>
          {FORMATS.map((f) => (
            <button
              key={f.value}
              onClick={() => handleFormatSelect(f.value)}
              type="button"
              className={`px-2.5 py-1 rounded-lg text-xs font-medium cursor-pointer ${
                selectedFormat === f.value
                  ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-400/50'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>

        {pagination.total > 0 && (
          <div className="text-slate-400 font-mono text-[11px]">
            Page {pagination.page} of {pagination.total_pages}
          </div>
        )}
      </div>

      {/* Content Stream */}
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
              ? `No anime records found matching "${query}". Try checking the spelling or browse trending categories.`
              : 'No anime records match the current filter criteria.'
          }
          actionLabel="Reset Filters"
          onAction={() => {
            setQuery('')
            setSelectedGenre('All')
            setSelectedFormat('')
            setSearchParams({})
          }}
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
            <div className="flex items-center justify-center gap-3 pt-4 border-t border-purple-500/20">
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
                Page {page} / {pagination.total_pages}
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

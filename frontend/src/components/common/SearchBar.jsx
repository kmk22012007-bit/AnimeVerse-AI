import React, { useState, useEffect, useRef } from 'react'
import { Search, X, Loader2, Star, Tv, Film, Disc } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { searchAnime } from '../../api/anime'

// Simple in-memory client search cache
const searchCache = new Map()

export const SearchBar = ({
  value = '',
  onChange,
  onSearch,
  onSelect,
  placeholder = 'Search anime titles, genres, studios (min. 2 chars)...',
  className = '',
  autoFocus = false,
  liveSearch = false,
}) => {
  const navigate = useNavigate()
  const [internalValue, setInternalValue] = useState(value)
  const [liveResults, setLiveResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [isOpen, setIsOpen] = useState(false)
  const [selectedIndex, setSelectedIndex] = useState(-1)
  const containerRef = useRef(null)
  const inputRef = useRef(null)
  const debounceTimerRef = useRef(null)

  useEffect(() => {
    setInternalValue(value || '')
  }, [value])

  // Click outside listener to dismiss live results
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setIsOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  // Global '/' keyboard shortcut to focus search bar
  useEffect(() => {
    const handleGlobalSlash = (e) => {
      if (
        e.key === '/' &&
        document.activeElement?.tagName !== 'INPUT' &&
        document.activeElement?.tagName !== 'TEXTAREA' &&
        !document.activeElement?.isContentEditable
      ) {
        e.preventDefault()
        inputRef.current?.focus()
      }
    }
    window.addEventListener('keydown', handleGlobalSlash)
    return () => window.removeEventListener('keydown', handleGlobalSlash)
  }, [])

  const fetchLiveSuggestions = async (searchTerm) => {
    const trimmed = searchTerm.trim()
    if (trimmed.length < 2) {
      setLiveResults([])
      setIsOpen(false)
      setSelectedIndex(-1)
      setLoading(false)
      return
    }

    const cacheKey = trimmed.toLowerCase()
    if (searchCache.has(cacheKey)) {
      setLiveResults(searchCache.get(cacheKey))
      setIsOpen(true)
      setSelectedIndex(-1)
      setLoading(false)
      return
    }

    setLoading(true)
    try {
      const res = await searchAnime(trimmed, 1)
      const results = res?.results || []
      const sliced = results.slice(0, 8)
      searchCache.set(cacheKey, sliced)
      setLiveResults(sliced)
      setIsOpen(true)
      setSelectedIndex(-1)
    } catch (err) {
      setLiveResults([])
    } finally {
      setLoading(false)
    }
  }

  const handleChange = (e) => {
    const val = e.target.value
    setInternalValue(val)
    if (onChange) onChange(val)

    if (liveSearch) {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current)
      }
      if (val.trim().length >= 2) {
        setLoading(true)
        debounceTimerRef.current = setTimeout(() => {
          fetchLiveSuggestions(val)
        }, 220)
      } else {
        setLiveResults([])
        setIsOpen(false)
        setSelectedIndex(-1)
        setLoading(false)
      }
    }
  }

  const handleKeyDown = (e) => {
    if (isOpen && liveResults.length > 0) {
      if (e.key === 'ArrowDown') {
        e.preventDefault()
        setSelectedIndex((prev) => (prev < liveResults.length - 1 ? prev + 1 : 0))
        return
      }
      if (e.key === 'ArrowUp') {
        e.preventDefault()
        setSelectedIndex((prev) => (prev > 0 ? prev - 1 : liveResults.length - 1))
        return
      }
      if (e.key === 'Enter' && selectedIndex >= 0 && selectedIndex < liveResults.length) {
        e.preventDefault()
        handleItemClick(liveResults[selectedIndex])
        return
      }
    }

    if (e.key === 'Enter') {
      setIsOpen(false)
      if (onSearch) {
        onSearch(internalValue)
      } else if (internalValue.trim().length >= 2) {
        navigate(`/discover?q=${encodeURIComponent(internalValue.trim())}`)
      }
    } else if (e.key === 'Escape') {
      setIsOpen(false)
      setSelectedIndex(-1)
    }
  }

  const handleClear = () => {
    setInternalValue('')
    setLiveResults([])
    setIsOpen(false)
    if (onChange) onChange('')
    if (onSearch) onSearch('')
  }

  const handleItemClick = (item) => {
    setIsOpen(false)
    if (onSelect) {
      onSelect(item)
    } else {
      navigate(`/anime/${item.mal_id}`)
    }
  }

  const getTypeIcon = (type) => {
    const t = (type || '').toLowerCase()
    if (t === 'movie') return <Film className="w-3 h-3 text-cyan-400" />
    if (t === 'ova' || t === 'ona' || t === 'special') return <Disc className="w-3 h-3 text-amber-400" />
    return <Tv className="w-3 h-3 text-purple-400" />
  }

  return (
    <div ref={containerRef} className={`relative flex items-center w-full ${className}`}>
      <div className="absolute left-3.5 text-purple-400/80 pointer-events-none flex items-center">
        {loading ? (
          <Loader2 className="w-4 h-4 animate-spin text-purple-400" />
        ) : (
          <Search className="w-4 h-4" />
        )}
      </div>

      <input
        ref={inputRef}
        type="text"
        role="combobox"
        aria-autocomplete="list"
        aria-expanded={isOpen}
        aria-controls="search-suggestions-list"
        aria-label="Search anime titles"
        value={internalValue}
        onChange={handleChange}
        onKeyDown={handleKeyDown}
        onFocus={() => {
          if (liveSearch && internalValue.trim().length >= 2 && liveResults.length > 0) {
            setIsOpen(true)
          }
        }}
        placeholder={placeholder}
        autoFocus={autoFocus}
        className="w-full pl-10 pr-10 py-2.5 text-sm rounded-xl bg-purple-950/25 border border-purple-500/25 text-slate-100 placeholder:text-slate-400 focus:outline-none focus:border-purple-400 focus:ring-1 focus:ring-purple-400/50 shadow-inner transition-all duration-200"
      />

      {internalValue && (
        <button
          onClick={handleClear}
          type="button"
          aria-label="Clear search"
          className="absolute right-3 p-1 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-purple-900/40 transition-colors cursor-pointer"
        >
          <X className="w-4 h-4" />
        </button>
      )}

      {/* Floating Live Quick Search Dropdown */}
      {liveSearch && isOpen && (
        <div
          id="search-suggestions-list"
          role="listbox"
          className="absolute top-full left-0 right-0 mt-2 z-50 bg-[#0c0e1e]/95 backdrop-blur-xl border border-purple-500/40 rounded-2xl shadow-[0_15px_40px_rgba(0,0,0,0.8)] overflow-hidden animate-in fade-in slide-in-from-top-2 duration-150"
        >
          <div className="p-2 border-b border-purple-500/20 flex items-center justify-between text-[11px] font-mono text-purple-300 px-3">
            <span>QUICK SEARCH RESULTS</span>
            <span className="text-slate-400">{liveResults.length} found</span>
          </div>

          <div className="max-h-80 overflow-y-auto divide-y divide-purple-950/50">
            {liveResults.length === 0 ? (
              <div className="p-4 text-center text-xs text-slate-400">
                {loading ? 'Searching anime registry...' : `No anime found matching "${internalValue}"`}
              </div>
            ) : (
              liveResults.map((item, idx) => (
                <button
                  key={item.mal_id}
                  onClick={() => handleItemClick(item)}
                  role="option"
                  aria-selected={selectedIndex === idx}
                  type="button"
                  className={`w-full p-2.5 flex items-center gap-3 text-left transition-colors group cursor-pointer ${
                    selectedIndex === idx
                      ? 'bg-purple-600/30 text-purple-200 border-l-2 border-purple-400'
                      : 'hover:bg-purple-900/30'
                  }`}
                >
                  {/* Poster Thumbnail */}
                  <div className="w-10 h-14 rounded-lg bg-purple-950/80 overflow-hidden flex-shrink-0 border border-purple-500/20">
                    {item.poster_url ? (
                      <img
                        src={item.poster_url}
                        alt={item.title}
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform"
                      />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center text-purple-400">
                        <Tv className="w-4 h-4" />
                      </div>
                    )}
                  </div>

                  {/* Title & Metadata */}
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-semibold text-white truncate group-hover:text-purple-300 transition-colors">
                      {item.title}
                    </p>
                    {item.title_english && item.title_english !== item.title && (
                      <p className="text-[10px] text-slate-400 truncate">
                        {item.title_english}
                      </p>
                    )}
                    <div className="flex items-center gap-2 mt-1">
                      <span className="inline-flex items-center gap-1 text-[10px] font-mono px-1.5 py-0.5 rounded bg-purple-950/80 border border-purple-500/30 text-purple-300">
                        {getTypeIcon(item.anime_type)}
                        {item.anime_type || 'TV'}
                      </span>
                      {item.score && (
                        <span className="inline-flex items-center gap-0.5 text-[10px] font-mono text-cyan-400">
                          <Star className="w-2.5 h-2.5 fill-cyan-400 text-cyan-400" />
                          {item.score}
                        </span>
                      )}
                      {item.total_episodes && (
                        <span className="text-[10px] font-mono text-slate-400">
                          {item.total_episodes} eps
                        </span>
                      )}
                    </div>
                  </div>
                </button>
              ))
            )}
          </div>

          <div className="p-2.5 bg-purple-950/40 border-t border-purple-500/20 text-center">
            <button
              onClick={() => {
                setIsOpen(false)
                navigate(`/discover?q=${encodeURIComponent(internalValue.trim())}`)
              }}
              type="button"
              className="text-xs font-mono text-purple-400 hover:text-purple-300 font-semibold cursor-pointer"
            >
              See all results in Discover &rarr;
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

export default SearchBar

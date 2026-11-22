import React, { useState, useEffect } from 'react'
import {
  Tv,
  Globe,
  ShieldCheck,
  Search,
  ExternalLink,
  Play,
  CheckCircle,
  AlertCircle,
  Loader2,
  Sparkles,
} from 'lucide-react'
import { searchAnime, getWatchOptions, getAnimeTrailers, getAnimeDetails } from '../api/anime'
import ProviderLogo from '../components/ProviderLogo'
import { isSafeUrl } from '../utils/security'

const QUICK_TITLES = [
  { name: 'Sousou no Frieren', id: 52991 },
  { name: 'Demon Slayer', id: 38000 },
  { name: 'Death Note', id: 1535 },
  { name: 'Naruto', id: 20 },
  { name: 'One Piece', id: 21 },
]

const COUNTRIES = [
  { code: 'IN', label: 'India (Default)' },
  { code: 'US', label: 'United States' },
  { code: 'GB', label: 'United Kingdom' },
  { code: 'JP', label: 'Japan' },
  { code: 'CA', label: 'Canada' },
]

const AUDIO_LANGUAGES = [
  { code: 'all', label: 'All Audio' },
  { code: 'Japanese', label: 'Japanese (Original)' },
  { code: 'English', label: 'English' },
  { code: 'Hindi', label: 'Hindi' },
  { code: 'Tamil', label: 'Tamil' },
  { code: 'Telugu', label: 'Telugu' },
  { code: 'Malayalam', label: 'Malayalam' },
]

const SUBTITLE_LANGUAGES = [
  { code: 'all', label: 'All Subtitles' },
  { code: 'English', label: 'English' },
  { code: 'Japanese', label: 'Japanese' },
  { code: 'Hindi', label: 'Hindi' },
]

export const WatchAnywherePage = () => {
  const [selectedAnime, setSelectedAnime] = useState(QUICK_TITLES[0])
  const [country, setCountry] = useState('IN')
  const [audioLanguage, setAudioLanguage] = useState('all')
  const [subtitleLanguage, setSubtitleLanguage] = useState('all')
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState([])
  const [searching, setSearching] = useState(false)
  const [watchData, setWatchData] = useState(null)
  const [trailersData, setTrailersData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const fetchWatchInfo = async (malId, countryCode, audioLang, subLang) => {
    setLoading(true)
    setError(null)
    try {
      const [watchRes, trailersRes] = await Promise.allSettled([
        getWatchOptions(malId, countryCode, audioLang, subLang),
        getAnimeTrailers(malId),
      ])

      if (watchRes.status === 'fulfilled') {
        setWatchData(watchRes.value)
      } else {
        setWatchData(null)
      }

      if (trailersRes.status === 'fulfilled') {
        setTrailersData(trailersRes.value)
      } else {
        setTrailersData(null)
      }
    } catch (err) {
      setError('Unable to retrieve streaming records for this territory.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (selectedAnime) {
      fetchWatchInfo(selectedAnime.id, country, audioLanguage, subtitleLanguage)
    }
  }, [selectedAnime, country, audioLanguage, subtitleLanguage])

  const handleSearch = async (e) => {
    e.preventDefault()
    if (searchQuery.trim().length < 2) return
    setSearching(true)
    try {
      const res = await searchAnime(searchQuery.trim(), 1)
      setSearchResults(res?.results || [])
    } catch (err) {
      setSearchResults([])
    } finally {
      setSearching(false)
    }
  }

  const handleSelectAnime = (item) => {
    setSelectedAnime({ name: item.title, id: item.mal_id, poster_url: item.poster_url })
    setSearchResults([])
    setSearchQuery('')
  }

  const categories = watchData?.categories || {}
  const totalOptions = watchData?.results_count || 0

  return (
    <div className="space-y-8 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-wide flex items-center gap-2.5">
            <Tv className="w-7 h-7 text-purple-400" />
            Watch Anywhere Hub
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-1 font-mono">
            Verified, legal anime streaming availability across India and global territories
          </p>
        </div>

        {/* Territory & Language Selectors */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Country Selector */}
          <div className="flex items-center gap-1.5 bg-purple-950/40 p-1.5 rounded-2xl border border-purple-500/30">
            <Globe className="w-4 h-4 text-cyan-400 ml-1.5" />
            <select
              value={country}
              onChange={(e) => setCountry(e.target.value)}
              className="bg-transparent text-xs font-mono text-slate-200 focus:outline-none pr-2 cursor-pointer"
            >
              {COUNTRIES.map((c) => (
                <option key={c.code} value={c.code} className="bg-[#0c0e1e] text-slate-200">
                  {c.label}
                </option>
              ))}
            </select>
          </div>

          {/* Audio Language Filter */}
          <div className="flex items-center gap-1.5 bg-purple-950/40 p-1.5 rounded-2xl border border-purple-500/30">
            <span className="text-[10px] font-mono text-purple-400 font-bold ml-1.5">AUDIO:</span>
            <select
              value={audioLanguage}
              onChange={(e) => setAudioLanguage(e.target.value)}
              className="bg-transparent text-xs font-mono text-slate-200 focus:outline-none pr-2 cursor-pointer"
            >
              {AUDIO_LANGUAGES.map((a) => (
                <option key={a.code} value={a.code} className="bg-[#0c0e1e] text-slate-200">
                  {a.label}
                </option>
              ))}
            </select>
          </div>

          {/* Subtitle Language Filter */}
          <div className="flex items-center gap-1.5 bg-purple-950/40 p-1.5 rounded-2xl border border-purple-500/30">
            <span className="text-[10px] font-mono text-cyan-400 font-bold ml-1.5">SUB:</span>
            <select
              value={subtitleLanguage}
              onChange={(e) => setSubtitleLanguage(e.target.value)}
              className="bg-transparent text-xs font-mono text-slate-200 focus:outline-none pr-2 cursor-pointer"
            >
              {SUBTITLE_LANGUAGES.map((s) => (
                <option key={s.code} value={s.code} className="bg-[#0c0e1e] text-slate-200">
                  {s.label}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Search & Quick Selection Row */}
      <div className="space-y-3">
        <form onSubmit={handleSearch} className="relative flex items-center max-w-xl">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search anime to check streaming availability..."
            className="w-full pl-10 pr-24 py-2.5 text-xs sm:text-sm rounded-xl bg-purple-950/30 border border-purple-500/30 text-white placeholder:text-slate-400 focus:outline-none focus:border-purple-400 focus:ring-1 focus:ring-purple-400/50"
          />
          <Search className="w-4 h-4 text-purple-400 absolute left-3.5 pointer-events-none" />
          <button
            type="submit"
            className="absolute right-1.5 px-3 py-1.5 rounded-lg bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold cursor-pointer"
          >
            {searching ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : 'Search'}
          </button>
        </form>

        {/* Search Results Dropdown */}
        {searchResults.length > 0 && (
          <div className="p-2 rounded-2xl bg-[#0c0e1e] border border-purple-500/30 shadow-2xl max-w-xl max-h-60 overflow-y-auto divide-y divide-purple-950/60 z-20">
            {searchResults.map((item) => (
              <button
                key={item.mal_id}
                onClick={() => handleSelectAnime(item)}
                type="button"
                className="w-full p-2 flex items-center gap-3 text-left hover:bg-purple-900/30 rounded-xl transition-colors cursor-pointer"
              >
                <div className="w-8 h-11 rounded bg-purple-950 overflow-hidden flex-shrink-0">
                  {item.poster_url && (
                    <img src={item.poster_url} alt="" className="w-full h-full object-cover" />
                  )}
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-xs font-semibold text-white truncate">{item.title}</p>
                  <p className="text-[10px] text-slate-400 font-mono">
                    {item.anime_type || 'TV'} • {item.score ? `★ ${item.score}` : 'Unrated'}
                  </p>
                </div>
              </button>
            ))}
          </div>
        )}

        {/* Quick Picks Strip */}
        <div className="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-none text-xs font-mono">
          <span className="text-slate-400 flex items-center gap-1">
            <Sparkles className="w-3 h-3 text-purple-400" /> Popular:
          </span>
          {QUICK_TITLES.map((t) => (
            <button
              key={t.id}
              onClick={() => setSelectedAnime(t)}
              type="button"
              className={`px-3 py-1 rounded-xl whitespace-nowrap transition-all cursor-pointer ${
                selectedAnime.id === t.id
                  ? 'bg-purple-600 text-white font-bold border border-purple-400'
                  : 'bg-purple-950/30 text-purple-300 hover:bg-purple-900/40 border border-purple-500/20'
              }`}
            >
              {t.name}
            </button>
          ))}
        </div>
      </div>

      {/* Main Watch Availability Content */}
      <div className="space-y-6">
        {/* Selected Anime Banner Card */}
        <div className="p-5 rounded-2xl bg-[#0c0e1e] border border-purple-500/30 flex items-center justify-between gap-4">
          <div>
            <span className="text-[10px] font-mono uppercase tracking-wider text-cyan-400 block mb-1">
              Active Inspection Title:
            </span>
            <h2 className="text-lg sm:text-xl font-bold text-white">
              {watchData?.anime_title || selectedAnime.name}
            </h2>
            <p className="text-xs font-mono text-slate-400 mt-0.5">
              Target Territory: <span className="text-purple-300 font-semibold">{country}</span> • Verification Mode: <span className="text-cyan-400 font-semibold">Strict Provenance</span>
            </p>
          </div>

          <div className="text-right font-mono text-xs hidden sm:block">
            <span className="px-3 py-1 rounded-xl bg-purple-950/60 border border-purple-500/30 text-purple-200">
              {totalOptions} Verified Sources
            </span>
          </div>
        </div>

        {loading ? (
          <div className="p-12 text-center text-xs font-mono text-purple-300">
            Checking verified streaming registries for {country}...
          </div>
        ) : (
          <div className="space-y-8">
            {/* Categorized Options */}
            {watchData?.is_blocked ? (
              <div className="p-8 rounded-2xl bg-purple-950/20 border border-purple-500/20 text-center space-y-2">
                <p className="text-sm font-semibold text-purple-200">
                  This title is not available in AnimeVerse AI.
                </p>
              </div>
            ) : totalOptions === 0 ? (
              <div className="p-8 rounded-2xl bg-purple-950/20 border border-purple-500/20 text-center space-y-2">
                <p className="text-sm font-semibold text-slate-200">
                  {watchData?.message || `No verified legal streaming options found for ${selectedAnime.name} with selected filters in ${country}.`}
                </p>
                <p className="text-xs text-slate-400 max-w-md mx-auto">
                  AnimeVerse AI strictly shows genuine, verified licensors. We never display unverified audio dubs or fabricated streaming links.
                </p>
              </div>
            ) : (
              <div className="space-y-6">
                {Object.entries(categories).map(([categoryName, items]) => {
                  if (!items || items.length === 0) return null
                  const catLabel = categoryName.replace(/_/g, ' ').toUpperCase()

                  return (
                    <div key={categoryName} className="space-y-3">
                      <h3 className="text-xs font-mono uppercase tracking-wider text-purple-300 flex items-center gap-2">
                        <span className="w-2 h-2 rounded-full bg-cyan-400"></span>
                        {catLabel} Options ({items.length})
                      </h3>

                      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
                        {items.map((opt, i) => (
                          <div
                            key={i}
                            className="p-4 rounded-2xl bg-[#0c0e1e]/90 border border-purple-500/20 hover:border-purple-400/50 transition-all flex flex-col justify-between gap-3 group"
                          >
                            <div className="flex items-center gap-3">
                              <ProviderLogo
                                name={opt.provider_name}
                                logoUrl={opt.provider_logo_url}
                                className="w-10 h-10"
                              />
                              <div className="min-w-0 flex-1">
                                <h4 className="text-sm font-bold text-white truncate group-hover:text-purple-300 transition-colors">
                                  {opt.provider_name}
                                </h4>
                                <p className="text-[10px] font-mono text-cyan-400 capitalize">
                                  {opt.category.replace(/_/g, ' ')} • {opt.presentation_type || 'HD'}
                                </p>
                              </div>
                            </div>

                            {/* Verified Audio & Subtitle Language Metadata */}
                            {opt.has_verified_language_data ? (
                              <div className="space-y-1.5 py-2 border-y border-purple-950/60 text-[11px] font-mono">
                                {opt.verified_audio_languages?.length > 0 && (
                                  <div className="flex items-start gap-1.5">
                                    <span className="text-slate-400 text-[10px] uppercase">Audio:</span>
                                    <div className="flex flex-wrap gap-1">
                                      {opt.verified_audio_languages.map((lang) => (
                                        <span
                                          key={lang}
                                          className="px-1.5 py-0.5 rounded bg-purple-900/40 border border-purple-500/30 text-purple-200 text-[9px]"
                                        >
                                          {lang}
                                        </span>
                                      ))}
                                    </div>
                                  </div>
                                )}
                                {opt.verified_subtitle_languages?.length > 0 && (
                                  <div className="flex items-start gap-1.5">
                                    <span className="text-slate-400 text-[10px] uppercase">Subs:</span>
                                    <div className="flex flex-wrap gap-1">
                                      {opt.verified_subtitle_languages.map((lang) => (
                                        <span
                                          key={lang}
                                          className="px-1.5 py-0.5 rounded bg-cyan-950/40 border border-cyan-500/30 text-cyan-300 text-[9px]"
                                        >
                                          {lang}
                                        </span>
                                      ))}
                                    </div>
                                  </div>
                                )}
                                <div className="flex items-center justify-between text-[9px] text-slate-400 pt-0.5">
                                  <span className="text-emerald-400 flex items-center gap-1 font-semibold">
                                    <ShieldCheck className="w-3 h-3" />
                                    {opt.language_verification_status === 'licensor_confirmed'
                                      ? 'Licensor Confirmed'
                                      : 'Provider Reported'}
                                  </span>
                                  {opt.language_source && (
                                    <span className="truncate max-w-[130px] text-slate-500" title={opt.language_source}>
                                      {opt.language_source}
                                    </span>
                                  )}
                                </div>
                              </div>
                            ) : (
                              <div className="py-2 border-y border-purple-950/60 text-[10px] font-mono text-amber-300/90 flex items-center gap-1.5">
                                <AlertCircle className="w-3.5 h-3.5 flex-shrink-0 text-amber-400" />
                                <span>Platform available — audio language unconfirmed.</span>
                              </div>
                            )}

                            <div className="pt-1 flex items-center justify-between text-xs font-mono">
                              <span className="text-[10px] text-slate-400">
                                {opt.price ? `${opt.price} ${opt.currency || ''}` : 'Official Stream'}
                              </span>
                              <a
                                href={isSafeUrl(opt.url) ? opt.url : '#'}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-purple-600/80 hover:bg-purple-500 text-white font-semibold text-[11px] transition-all cursor-pointer"
                              >
                                <span>Watch</span>
                                <ExternalLink className="w-3 h-3" />
                              </a>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )
                })}
              </div>
            )}

            {/* Official YouTube Trailers */}
            {trailersData && trailersData.trailers && trailersData.trailers.length > 0 && (
              <div className="space-y-4 pt-4 border-t border-purple-500/20">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm sm:text-base font-bold text-white tracking-wide flex items-center gap-2">
                    <Play className="w-4 h-4 text-purple-400" />
                    Verified Official YouTube Trailers
                  </h3>
                  <span className="text-[10px] font-mono text-cyan-400 flex items-center gap-1">
                    <CheckCircle className="w-3 h-3 text-cyan-400" /> Licensor Verified
                  </span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
                  {trailersData.trailers.map((tr, idx) => (
                    <a
                      key={idx}
                      href={isSafeUrl(tr.youtube_url) ? tr.youtube_url : '#'}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="rounded-2xl overflow-hidden bg-[#0c0e1e] border border-purple-500/30 hover:border-purple-400 transition-all group block"
                    >
                      <div className="aspect-video relative bg-purple-950">
                        {tr.thumbnail_url ? (
                          <img src={tr.thumbnail_url} alt="" className="w-full h-full object-cover" />
                        ) : (
                          <div className="w-full h-full flex items-center justify-center text-purple-400">
                            <Play className="w-8 h-8" />
                          </div>
                        )}
                        <div className="absolute inset-0 bg-black/40 group-hover:bg-black/20 flex items-center justify-center transition-colors">
                          <div className="w-10 h-10 rounded-full bg-purple-600/90 flex items-center justify-center text-white shadow-lg group-hover:scale-110 transition-transform">
                            <Play className="w-5 h-5 fill-white ml-0.5" />
                          </div>
                        </div>
                      </div>
                      <div className="p-3">
                        <p className="text-xs font-semibold text-white line-clamp-1 group-hover:text-purple-300">
                          {tr.title}
                        </p>
                        <p className="text-[10px] font-mono text-cyan-400 mt-1 flex items-center gap-1">
                          <ExternalLink className="w-2.5 h-2.5" /> Watch on YouTube
                        </p>
                      </div>
                    </a>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

export default WatchAnywherePage

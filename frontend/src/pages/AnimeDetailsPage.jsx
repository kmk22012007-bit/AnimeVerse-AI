import React, { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import {
  Star,
  Tv,
  ArrowLeft,
  Play,
  ExternalLink,
  Plus,
  Minus,
  FileText,
  Trash2,
  ChevronDown,
  ChevronUp,
  AlertCircle,
  Calendar,
  Users,
  Film,
  Sparkles,
  Layers,
  ShieldAlert,
  ChevronRight,
  MessageSquare,
  ThumbsUp,
  AlertTriangle,
  Eye,
  EyeOff,
  MessageCircle,
} from 'lucide-react'
import {
  getAnimeDetails,
  getAnimeEpisodes,
  getRelatedAnime,
  getWatchOptions,
  getAnimeTrailers,
  getAnimeFranchise,
} from '../api/anime'
import {
  getAnimeReviews,
  createAnimeReview,
  voteReviewHelpful,
  getCommunityPosts,
} from '../api/community'
import { useWatchlist } from '../context/WatchlistContext'
import AddToListButton from '../components/watchlist/AddToListButton'
import { isSafeUrl } from '../utils/security'
import EditRatingNoteModal from '../components/watchlist/EditRatingNoteModal'
import ConfirmDeleteModal from '../components/watchlist/ConfirmDeleteModal'
import ErrorState from '../components/common/ErrorState'
import { HeroSkeleton } from '../components/common/LoadingSkeleton'
import ProviderLogo from '../components/ProviderLogo'

export const AnimeDetailsPage = () => {
  const { id } = useParams()
  const malId = parseInt(id, 10)

  const {
    getEntryByMalId,
    incrementEpisode,
    decrementEpisode,
    saveRatingAndNote,
    removeAnime,
  } = useWatchlist()

  const [details, setDetails] = useState(null)
  const [episodes, setEpisodes] = useState([])
  const [episodesLoading, setEpisodesLoading] = useState(false)
  const [episodePage, setEpisodePage] = useState(1)
  const [episodePagination, setEpisodePagination] = useState({ page: 1, total_pages: 1, total: 0 })
  const [expandedEpisode, setExpandedEpisode] = useState(null)
  const [relatedAnime, setRelatedAnime] = useState([])
  const [watchOptions, setWatchOptions] = useState(null)
  const [trailers, setTrailers] = useState(null)
  const [franchise, setFranchise] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Modals
  const [ratingModalOpen, setRatingModalOpen] = useState(false)
  const [deleteModalOpen, setDeleteModalOpen] = useState(false)
  const [deleting, setDeleting] = useState(false)

  // Reviews & Community Discussions State
  const [reviews, setReviews] = useState([])
  const [reviewsLoading, setReviewsLoading] = useState(false)
  const [reviewsSort, setReviewsSort] = useState('recent')
  const [revealedReviewSpoilers, setRevealedReviewSpoilers] = useState({})
  const [writeReviewModalOpen, setWriteReviewModalOpen] = useState(false)
  const [reviewTitle, setReviewTitle] = useState('')
  const [reviewScore, setReviewScore] = useState(8)
  const [reviewBody, setReviewBody] = useState('')
  const [reviewIsSpoiler, setReviewIsSpoiler] = useState(false)
  const [submittingReview, setSubmittingReview] = useState(false)
  const [reviewError, setReviewError] = useState(null)
  const [animeDiscussions, setAnimeDiscussions] = useState([])
  const [discussionsLoading, setDiscussionsLoading] = useState(false)

  const fetchReviews = async (sort = reviewsSort) => {
    setReviewsLoading(true)
    try {
      const res = await getAnimeReviews(malId, { sort })
      setReviews(res?.results || [])
    } catch (err) {
      setReviews([])
    } finally {
      setReviewsLoading(false)
    }
  }

  const fetchAnimeDiscussions = async () => {
    setDiscussionsLoading(true)
    try {
      const res = await getCommunityPosts({ anime_id: malId, page_size: 4 })
      setAnimeDiscussions(res?.results || [])
    } catch (err) {
      setAnimeDiscussions([])
    } finally {
      setDiscussionsLoading(false)
    }
  }

  const handleToggleHelpful = async (reviewId) => {
    try {
      const res = await voteReviewHelpful(reviewId)
      setReviews((prev) =>
        prev.map((r) =>
          r.id === reviewId
            ? { ...r, helpful_count: res.helpful_count, marked_helpful_by_me: res.is_helpful }
            : r
        )
      )
    } catch (err) {
      console.error('Failed to vote review helpful:', err)
    }
  }

  const handleCreateReview = async (e) => {
    e.preventDefault()
    if (!reviewBody.trim() || reviewBody.trim().length < 20) {
      setReviewError('Review body must be at least 20 characters.')
      return
    }

    setSubmittingReview(true)
    setReviewError(null)
    try {
      const created = await createAnimeReview(malId, {
        title: reviewTitle.trim() || undefined,
        score: parseInt(reviewScore, 10),
        body: reviewBody.trim(),
        is_spoiler: reviewIsSpoiler,
      })
      setReviews((prev) => [created, ...prev])
      setWriteReviewModalOpen(false)
      setReviewTitle('')
      setReviewBody('')
      setReviewScore(8)
      setReviewIsSpoiler(false)
    } catch (err) {
      setReviewError(err.response?.data?.message || err.response?.data?.details?.anime_id || 'Failed to submit review.')
    } finally {
      setSubmittingReview(false)
    }
  }

  const existingEntry = getEntryByMalId(malId)

  // Fetch Core Details, Trailers, Watch Options, Related
  const fetchAnimeData = async () => {
    setLoading(true)
    setError(null)
    try {
      const [detailsRes, watchRes, trailersRes, relatedRes, franchiseRes] = await Promise.allSettled([
        getAnimeDetails(malId),
        getWatchOptions(malId, 'IN'),
        getAnimeTrailers(malId),
        getRelatedAnime(malId),
        getAnimeFranchise(malId),
      ])

      if (detailsRes.status === 'fulfilled') {
        setDetails(detailsRes.value?.data || detailsRes.value)
      } else {
        throw detailsRes.reason
      }

      if (watchRes.status === 'fulfilled') {
        setWatchOptions(watchRes.value)
      }
      if (trailersRes.status === 'fulfilled') {
        setTrailers(trailersRes.value)
      }
      if (relatedRes.status === 'fulfilled') {
        setRelatedAnime(relatedRes.value?.results || [])
      }
      if (franchiseRes.status === 'fulfilled') {
        setFranchise(franchiseRes.value?.franchise || null)
      }
    } catch (err) {
      setError(err.message || 'Failed to retrieve anime details.')
    } finally {
      setLoading(false)
    }
  }

  // Fetch Real Episodes
  const fetchEpisodes = async (page = 1) => {
    setEpisodesLoading(true)
    try {
      const res = await getAnimeEpisodes(malId, page)
      setEpisodes(res?.episodes || [])
      setEpisodePagination(res?.pagination || { page, total_pages: 1, total: res?.episodes?.length || 0 })
    } catch (err) {
      setEpisodes([])
    } finally {
      setEpisodesLoading(false)
    }
  }

  useEffect(() => {
    if (malId) {
      fetchAnimeData()
      fetchEpisodes(1)
      fetchReviews(reviewsSort)
      fetchAnimeDiscussions()
      setEpisodePage(1)
      setExpandedEpisode(null)
    }
  }, [malId])

  const handleEpisodePageChange = (newPage) => {
    setEpisodePage(newPage)
    fetchEpisodes(newPage)
  }

  const toggleEpisodeExpand = (epNum) => {
    setExpandedEpisode((prev) => (prev === epNum ? null : epNum))
  }

  const handleDeleteConfirm = async (entryId) => {
    setDeleting(true)
    await removeAnime(entryId)
    setDeleting(false)
    setDeleteModalOpen(false)
  }

  if (loading) {
    return <HeroSkeleton />
  }

  if (error || !details) {
    const isBlocked = (details && details.is_blocked) || (error && error.includes('not available in AnimeVerse AI'))

    if (isBlocked) {
      return (
        <div className="space-y-6 max-w-xl mx-auto py-12 text-center">
          <Link
            to="/discover"
            className="inline-flex items-center gap-1.5 text-xs text-purple-400 hover:text-purple-300 font-mono mb-4"
          >
            <ArrowLeft className="w-3.5 h-3.5" /> Back to Discover
          </Link>
          <div className="p-8 rounded-2xl bg-purple-950/30 border border-purple-500/20 text-center space-y-4">
            <div className="w-12 h-12 rounded-xl bg-purple-900/40 border border-purple-500/30 mx-auto flex items-center justify-center text-purple-300">
              <ShieldAlert className="w-6 h-6 text-purple-400" />
            </div>
            <h2 className="text-lg font-bold text-white">Title Unavailable</h2>
            <p className="text-sm font-mono text-purple-300/80">
              This title is not available in AnimeVerse AI.
            </p>
          </div>
        </div>
      )
    }

    return (
      <div className="space-y-4">
        <Link
          to="/discover"
          className="inline-flex items-center gap-1.5 text-xs text-purple-400 hover:text-purple-300 font-mono"
        >
          <ArrowLeft className="w-3.5 h-3.5" /> Back to Discover
        </Link>
        <ErrorState
          title="Anime Lookup Failed"
          message={error || 'Unable to locate title in registry.'}
          onRetry={fetchAnimeData}
        />
      </div>
    )
  }

  const title = details.title_english || details.title || `Anime #${malId}`
  const poster = details.poster_url || details.images?.jpg?.large_image_url || details.images?.jpg?.image_url
  const banner = details.banner_url || poster
  const total = details.episodes || existingEntry?.total_episodes || 0
  const watched = existingEntry?.watched_episodes || 0
  const characters = details.characters || []
  const metadataSource = (details.metadata_source || 'TENRAI').toUpperCase()

  return (
    <div className="w-full min-h-full space-y-8 sm:space-y-10 pb-16">
      {/* Back Navigation Bar */}
      <div className="flex items-center justify-between">
        <Link
          to="/discover"
          className="inline-flex items-center gap-1.5 text-xs text-purple-400 hover:text-purple-300 font-mono"
        >
          <ArrowLeft className="w-3.5 h-3.5" /> Back to Discover
        </Link>
        <span className="text-[10px] font-mono px-2.5 py-1 rounded-full bg-purple-950/60 border border-purple-500/30 text-purple-300">
          Source: {metadataSource}
        </span>
      </div>

      {/* Franchise Navigator Strip (if part of an anime franchise) */}
      {franchise && franchise.all_entries && franchise.all_entries.length > 1 && (
        <div className="p-4 rounded-2xl bg-indigo-950/40 border border-indigo-500/30 backdrop-blur-md space-y-3 shadow-[0_0_20px_rgba(99,102,241,0.15)]">
          <div className="flex items-center justify-between flex-wrap gap-2">
            <div className="flex items-center gap-2">
              <Layers className="w-4 h-4 text-indigo-400" />
              <span className="text-xs font-bold uppercase tracking-wider text-indigo-300">
                Part of the {franchise.name} Franchise
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-indigo-900/60 text-indigo-200 border border-indigo-400/30">
                {franchise.entry_count} Verified Entries
              </span>
            </div>
            <Link
              to={`/franchise/${franchise.id}`}
              className="inline-flex items-center gap-1 text-xs text-cyan-300 hover:text-cyan-200 font-mono hover:underline"
            >
              View Franchise Collection <ChevronRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          {/* Quick Entry Selector */}
          <div className="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-thin">
            {franchise.all_entries.map((entry) => {
              const isCurrent = entry.mal_id === malId
              return (
                <Link
                  key={entry.id}
                  to={`/anime/${entry.mal_id}`}
                  className={`flex items-center gap-2 px-3 py-1.5 rounded-xl text-xs font-medium whitespace-nowrap transition-all border ${
                    isCurrent
                      ? 'bg-purple-600 text-white border-purple-400 shadow-[0_0_12px_rgba(168,85,247,0.5)]'
                      : 'bg-black/50 text-slate-300 hover:text-white hover:bg-purple-900/30 border-purple-500/20'
                  }`}
                >
                  <span className="text-[10px] font-mono opacity-80 uppercase">
                    [{entry.relationship_label || entry.relationship_type}]
                  </span>
                  <span className="max-w-[160px] truncate">{entry.title}</span>
                </Link>
              )
            })}
          </div>
        </div>
      )}

      {/* Hero Header & Banner */}
      <div className="relative rounded-3xl bg-[#0e101d]/95 border border-purple-500/25 shadow-[0_0_35px_rgba(168,85,247,0.15)] min-h-[420px] backdrop-blur-md">
        {/* Backdrop Banner Image with Gradient */}
        {banner && (
          <div className="absolute top-0 left-0 right-0 h-64 sm:h-80 overflow-hidden rounded-3xl pointer-events-none opacity-20">
            <img src={banner} alt="" className="w-full h-full object-cover filter blur-sm scale-105" />
            <div className="absolute inset-0 bg-gradient-to-b from-transparent via-[#0e101d]/80 to-[#0e101d]" />
          </div>
        )}

        <div className="relative p-6 sm:p-8 flex flex-col md:flex-row gap-6 lg:gap-8 items-start">
          {/* Poster Column */}
          <div className="w-full sm:w-56 md:w-60 lg:w-64 flex-shrink-0 flex justify-center sm:justify-start">
            {poster && (
              <div className="w-48 sm:w-56 md:w-60 lg:w-64 aspect-[3/4] rounded-2xl overflow-hidden bg-purple-950 shadow-[0_0_25px_rgba(168,85,247,0.3)] border border-purple-500/40 flex-shrink-0">
                <img src={poster} alt={title} className="w-full h-full object-cover" />
              </div>
            )}
          </div>

          {/* Details Body */}
          <div className="flex-1 space-y-5 min-w-0 w-full">
            <div className="flex flex-wrap items-center gap-2">
              {details.score && (
                <span className="inline-flex items-center gap-1 px-3 py-1 rounded-xl bg-black/60 border border-cyan-400/50 text-cyan-300 text-xs font-bold font-mono">
                  <Star className="w-3.5 h-3.5 fill-cyan-400 text-cyan-400" />
                  {details.score} MAL
                </span>
              )}
              {details.type && (
                <span className="px-2.5 py-1 rounded-xl bg-purple-500/20 border border-purple-500/40 text-purple-300 text-xs font-mono font-semibold">
                  {details.type}
                </span>
              )}
              {details.episodes && (
                <span className="px-2.5 py-1 rounded-xl bg-purple-950/60 border border-white/10 text-slate-300 text-xs font-mono">
                  {details.episodes} Episodes
                </span>
              )}
              {details.aired?.from && (
                <span className="px-2.5 py-1 rounded-xl bg-purple-950/40 border border-white/10 text-slate-400 text-xs font-mono flex items-center gap-1">
                  <Calendar className="w-3 h-3 text-purple-400" />
                  {details.aired.from.slice(0, 10)}
                </span>
              )}
              {details.season && details.year && (
                <span className="px-2.5 py-1 rounded-xl bg-purple-950/40 border border-purple-500/20 text-purple-300 text-xs font-mono capitalize">
                  {details.season} {details.year}
                </span>
              )}
              {details.popularity && (
                <span className="px-2.5 py-1 rounded-xl bg-purple-950/40 border border-purple-500/20 text-slate-400 text-xs font-mono">
                  Popularity #{details.popularity}
                </span>
              )}
            </div>

            <h1 className="text-2xl sm:text-4xl font-extrabold text-white tracking-tight leading-tight">
              {title}
            </h1>

            <div className="space-y-0.5">
              {details.title && details.title_english && details.title !== details.title_english && (
                <p className="text-xs sm:text-sm text-purple-300 font-mono">
                  {details.title}
                </p>
              )}
              {details.title_japanese && (
                <p className="text-xs text-slate-400 font-mono">
                  {details.title_japanese}
                </p>
              )}
            </div>

            {/* Genre Tags */}
            {details.genres && details.genres.length > 0 && (
              <div className="flex flex-wrap gap-1.5 pt-1">
                {details.genres.map((g, idx) => (
                  <span
                    key={idx}
                    className="px-2.5 py-0.5 rounded-lg bg-purple-950/80 border border-purple-500/30 text-purple-200 text-[11px] font-mono"
                  >
                    {g}
                  </span>
                ))}
              </div>
            )}

            {/* Watchlist Tracking Controls Bar (PROMINENTLY ABOVE SYNOPSIS) */}
            <div className="p-4 rounded-2xl bg-purple-950/60 border border-purple-500/30 flex flex-wrap items-center justify-between gap-4 shadow-sm backdrop-blur-sm">
              <div className="flex flex-wrap items-center gap-3">
                <AddToListButton malId={malId} />

                {existingEntry && (
                  <div className="flex items-center gap-2 bg-purple-950/80 px-3 py-1.5 rounded-xl border border-purple-500/30 text-xs font-mono">
                    <span className="text-slate-400">Watched:</span>
                    <button
                      onClick={() => decrementEpisode(existingEntry)}
                      disabled={watched <= 0}
                      type="button"
                      className="p-1 rounded bg-purple-900/60 hover:bg-purple-800 text-purple-200 disabled:opacity-30 cursor-pointer"
                      title="-1 Episode"
                    >
                      <Minus className="w-3 h-3" />
                    </button>
                    <span className="font-bold text-white px-1">
                      {watched} / {total > 0 ? total : '??'}
                    </span>
                    <button
                      onClick={() => incrementEpisode(existingEntry)}
                      disabled={total > 0 && watched >= total}
                      type="button"
                      className="p-1 rounded bg-purple-600 hover:bg-purple-500 text-white disabled:opacity-30 cursor-pointer"
                      title="+1 Episode"
                    >
                      <Plus className="w-3 h-3" />
                    </button>
                  </div>
                )}
              </div>

              {existingEntry && (
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setRatingModalOpen(true)}
                    type="button"
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-purple-900/40 hover:bg-purple-800/60 border border-purple-500/30 text-xs text-purple-200 font-mono cursor-pointer"
                  >
                    <Star className={`w-3.5 h-3.5 ${existingEntry.rating ? 'fill-amber-400 text-amber-400' : 'text-slate-400'}`} />
                    <span>{existingEntry.rating ? `${existingEntry.rating}/10` : 'Rate'}</span>
                  </button>

                  <button
                    onClick={() => setRatingModalOpen(true)}
                    type="button"
                    className="p-2 rounded-xl bg-purple-900/40 hover:bg-purple-800/60 border border-purple-500/30 text-purple-300 hover:text-white cursor-pointer"
                    title="Personal Notes"
                  >
                    <FileText className="w-3.5 h-3.5" />
                  </button>

                  <button
                    onClick={() => setDeleteModalOpen(true)}
                    type="button"
                    className="p-2 rounded-xl bg-rose-950/40 hover:bg-rose-900/60 border border-rose-500/30 text-rose-300 hover:text-rose-100 cursor-pointer"
                    title="Remove from Watchlist"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              )}
            </div>

            {/* Synopsis Section */}
            <div className="space-y-2 pt-1">
              <div className="flex items-center gap-2 text-xs font-mono text-purple-300 uppercase tracking-wider font-semibold">
                <FileText className="w-3.5 h-3.5 text-cyan-400" />
                <span>Synopsis</span>
              </div>
              <div className="text-sm text-slate-300 leading-relaxed font-sans space-y-3">
                {details.synopsis ? (
                  details.synopsis.split('\n\n').map((para, pIdx) => (
                    <p key={pIdx} className="leading-relaxed">
                      {para}
                    </p>
                  ))
                ) : (
                  <p className="italic text-slate-500 font-mono">No synopsis registered for this title.</p>
                )}
              </div>
            </div>

            {/* Quick Streaming Summary */}
            {watchOptions && watchOptions.results_count > 0 && (
              <div className="pt-2">
                <span className="text-xs font-mono text-cyan-300 uppercase tracking-wider block mb-2">
                  Legal Streaming Options ({watchOptions.country}):
                </span>
                <div className="flex flex-wrap gap-2">
                  {Object.entries(watchOptions.categories || {}).flatMap(([cat, list]) =>
                    list.map((opt, i) => (
                      <a
                        key={i}
                        href={isSafeUrl(opt.url) ? opt.url : '#'}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-purple-900/40 hover:bg-purple-800/60 border border-purple-500/30 text-xs text-purple-200 transition-all"
                      >
                        <ProviderLogo
                          name={opt.provider_name}
                          logoUrl={opt.provider_logo_url}
                          className="w-4 h-4 rounded-md"
                        />
                        <span>{opt.provider_name}</span>
                        <ExternalLink className="w-3 h-3 text-purple-400" />
                      </a>
                    ))
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* EPISODE GUIDE SECTION */}
      <section className="space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-purple-500/20 pb-3">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-purple-900/30 border border-purple-500/30 text-purple-300">
              <Layers className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-lg sm:text-xl font-bold text-white tracking-wide">
                Episode Guide
              </h2>
              <p className="text-xs text-slate-400 font-mono">
                {episodes.length > 0
                  ? `Showing ${episodes.length} episodes • Source: ${metadataSource}`
                  : 'Episode registry index'}
              </p>
            </div>
          </div>

          {/* Spoiler Notice Pill */}
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-xl bg-amber-950/30 border border-amber-500/30 text-amber-300 text-[11px] font-mono">
            <ShieldAlert className="w-3.5 h-3.5 text-amber-400" />
            <span>Spoiler Warning: Descriptions describe episode plots</span>
          </div>
        </div>

        {/* Episode List */}
        {episodesLoading ? (
          <div className="p-8 text-center text-xs font-mono text-purple-300">
            Loading episode registry from provider...
          </div>
        ) : episodes.length === 0 ? (
          <div className="p-6 rounded-2xl bg-purple-950/20 border border-purple-500/20 text-center text-xs font-mono text-slate-400">
            No episode records returned by provider for this anime.
          </div>
        ) : (
          <div className="space-y-3">
            {episodes.map((ep) => {
              const isExpanded = expandedEpisode === ep.episode_number
              const hasDesc = ep.has_description && ep.synopsis

              return (
                <div
                  key={ep.episode_number}
                  className="rounded-2xl bg-[#0c0e1e]/80 border border-purple-500/20 hover:border-purple-500/40 transition-colors overflow-hidden"
                >
                  <div className="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                    <div className="flex items-center gap-3.5 min-w-0 flex-1">
                      {/* Episode Number Badge */}
                      <span className="w-12 h-10 rounded-xl bg-purple-950/80 border border-purple-500/30 flex items-center justify-center text-xs font-bold font-mono text-purple-300 flex-shrink-0">
                        EP {ep.episode_number < 10 ? `0${ep.episode_number}` : ep.episode_number}
                      </span>

                      {/* Optional Episode Thumbnail */}
                      {ep.thumbnail_url && (
                        <div className="w-16 h-10 rounded-lg overflow-hidden bg-purple-950 flex-shrink-0 border border-purple-500/20 hidden sm:block">
                          <img src={ep.thumbnail_url} alt="" className="w-full h-full object-cover" />
                        </div>
                      )}

                      {/* Title & Metadata */}
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-2 flex-wrap">
                          <h3 className="text-sm font-semibold text-white truncate">
                            {ep.title}
                          </h3>
                          {ep.filler && (
                            <span className="px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/40 text-[10px] font-mono">
                              FILLER
                            </span>
                          )}
                          {ep.recap && (
                            <span className="px-2 py-0.5 rounded bg-blue-500/20 text-blue-300 border border-blue-500/40 text-[10px] font-mono">
                              RECAP
                            </span>
                          )}
                        </div>

                        {ep.aired && (
                          <p className="text-[11px] font-mono text-slate-400 mt-0.5">
                            Aired: {ep.aired.slice(0, 10)}
                          </p>
                        )}
                      </div>
                    </div>

                    {/* Expand Description Trigger */}
                    <button
                      onClick={() => toggleEpisodeExpand(ep.episode_number)}
                      type="button"
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-purple-950/60 hover:bg-purple-900/60 border border-purple-500/30 text-xs font-mono text-purple-300 cursor-pointer self-start sm:self-auto"
                    >
                      <span>{isExpanded ? 'Hide' : 'Description'}</span>
                      {isExpanded ? (
                        <ChevronUp className="w-3.5 h-3.5" />
                      ) : (
                        <ChevronDown className="w-3.5 h-3.5" />
                      )}
                    </button>
                  </div>

                  {/* Expandable Episode Description Area */}
                  {isExpanded && (
                    <div className="px-4 pb-4 pt-1 border-t border-purple-950/80 bg-purple-950/20">
                      {hasDesc ? (
                        <div className="p-3.5 rounded-xl bg-black/40 border border-purple-500/20 text-xs text-slate-200 leading-relaxed font-sans">
                          {ep.synopsis}
                        </div>
                      ) : (
                        <div className="p-3 rounded-xl bg-black/20 border border-purple-500/10 text-xs italic text-slate-500 font-mono">
                          Description unavailable.
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        )}

        {/* Episode Pagination Controls (if > 1 page) */}
        {episodePagination.total_pages > 1 && (
          <div className="flex items-center justify-center gap-3 pt-4 font-mono text-xs">
            <button
              onClick={() => handleEpisodePageChange(episodePage - 1)}
              disabled={episodePage <= 1}
              type="button"
              className="px-3 py-1.5 rounded-xl bg-purple-950/40 border border-purple-500/30 text-purple-300 disabled:opacity-30 cursor-pointer"
            >
              &larr; Prev
            </button>
            <span className="text-slate-400">
              Page {episodePage} of {episodePagination.total_pages}
            </span>
            <button
              onClick={() => handleEpisodePageChange(episodePage + 1)}
              disabled={episodePage >= episodePagination.total_pages}
              type="button"
              className="px-3 py-1.5 rounded-xl bg-purple-950/40 border border-purple-500/30 text-purple-300 disabled:opacity-30 cursor-pointer"
            >
              Next &rarr;
            </button>
          </div>
        )}
      </section>

      {/* CHARACTERS SECTION */}
      {characters.length > 0 && (
        <section className="space-y-4">
          <div className="flex items-center gap-2.5 border-b border-purple-500/20 pb-3">
            <div className="p-2 rounded-xl bg-purple-900/30 border border-purple-500/30 text-purple-300">
              <Users className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-lg sm:text-xl font-bold text-white tracking-wide">
                Key Characters
              </h2>
              <p className="text-xs text-slate-400 font-mono">
                Verified cast from {metadataSource}
              </p>
            </div>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3">
            {characters.slice(0, 12).map((char) => (
              <div
                key={char.id || char.name}
                className="p-2.5 rounded-2xl bg-[#0c0e1e]/60 border border-purple-500/20 flex flex-col items-center text-center group hover:border-purple-500/40 transition-colors"
              >
                <div className="w-20 h-24 rounded-xl overflow-hidden bg-purple-950 mb-2 border border-purple-500/20">
                  {char.image_url ? (
                    <img
                      src={char.image_url}
                      alt={char.name}
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center text-purple-400 text-xs">
                      No Photo
                    </div>
                  )}
                </div>
                <p className="text-xs font-semibold text-white truncate w-full">
                  {char.name}
                </p>
                <p className="text-[10px] font-mono text-purple-300">
                  {char.role || 'Supporting'}
                </p>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* RELATED ANIME SECTION */}
      {relatedAnime.length > 0 && (
        <section className="space-y-4">
          <div className="flex items-center gap-2.5 border-b border-purple-500/20 pb-3">
            <div className="p-2 rounded-xl bg-purple-900/30 border border-purple-500/30 text-purple-300">
              <Film className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-lg sm:text-xl font-bold text-white tracking-wide">
                Related Anime & Franchises
              </h2>
              <p className="text-xs text-slate-400 font-mono">
                Sequels, prequels, and side-stories
              </p>
            </div>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3">
            {relatedAnime.map((rel) => (
              <Link
                key={rel.mal_id}
                to={`/anime/${rel.mal_id}`}
                className="p-2.5 rounded-2xl bg-[#0c0e1e]/60 border border-purple-500/20 hover:border-purple-400/50 flex flex-col transition-all group"
              >
                <div className="aspect-[3/4] rounded-xl overflow-hidden bg-purple-950 mb-2 border border-purple-500/20">
                  {rel.poster_url ? (
                    <img
                      src={rel.poster_url}
                      alt={rel.title}
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center text-purple-400 text-xs">
                      <Tv className="w-6 h-6" />
                    </div>
                  )}
                </div>
                <p className="text-xs font-semibold text-white group-hover:text-purple-300 transition-colors line-clamp-2">
                  {rel.title}
                </p>
              </Link>
            ))}
          </div>
        </section>
      )}

      {/* OFFICIAL TRAILERS SECTION */}
      {trailers && trailers.trailers && trailers.trailers.length > 0 && (
        <section className="space-y-4">
          <div className="flex items-center gap-2.5 border-b border-purple-500/20 pb-3">
            <div className="p-2 rounded-xl bg-purple-900/30 border border-purple-500/30 text-purple-300">
              <Play className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-lg sm:text-xl font-bold text-white tracking-wide">
                Official YouTube Trailers
              </h2>
              <p className="text-xs text-slate-400 font-mono">
                Verified channel uploads
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
            {trailers.trailers.map((tr, idx) => (
              <a
                key={idx}
                href={isSafeUrl(tr.youtube_url) ? tr.youtube_url : '#'}
                target="_blank"
                rel="noopener noreferrer"
                className="rounded-2xl overflow-hidden bg-[#0c0e1e] border border-purple-500/30 hover:border-purple-400 transition-all group block"
              >
                <div className="aspect-video relative bg-purple-950">
                  {tr.thumbnail_url ? (
                    <img src={tr.thumbnail_url} alt={tr.title} className="w-full h-full object-cover" />
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
        </section>
      )}

      {/* REVIEWS & COMMUNITY DISCUSSIONS SECTION */}
      <section className="space-y-6 pt-6 border-t border-purple-500/20">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-purple-900/30 border border-purple-500/30 text-purple-300">
              <MessageSquare className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-lg sm:text-xl font-bold text-white tracking-wide">
                Community Reviews & Discussions
              </h2>
              <p className="text-xs text-slate-400 font-mono">
                {reviews.length} {reviews.length === 1 ? 'Review' : 'Reviews'} • Community ratings
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <Link
              to={`/community?anime_id=${malId}`}
              className="px-3.5 py-1.5 rounded-xl bg-slate-900/80 hover:bg-purple-950/40 border border-purple-800/40 text-xs font-semibold text-purple-300 hover:text-white transition flex items-center gap-1.5"
            >
              <MessageCircle className="w-3.5 h-3.5" />
              <span>All Discussions ({animeDiscussions.length})</span>
            </Link>
            <button
              onClick={() => {
                setReviewError(null)
                setWriteReviewModalOpen(true)
              }}
              className="px-4 py-1.5 rounded-xl bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold shadow-md shadow-purple-600/30 transition flex items-center gap-1.5"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Write a Review</span>
            </button>
          </div>
        </div>

        {/* Sort Reviews Dropdown */}
        {reviews.length > 0 && (
          <div className="flex items-center justify-between gap-3 text-xs">
            <span className="text-slate-400">Sort reviews by:</span>
            <div className="flex items-center gap-1.5">
              {[
                { id: 'recent', label: 'Recent' },
                { id: 'helpful', label: 'Most Helpful' },
                { id: 'highest_rating', label: 'Highest Score' },
                { id: 'lowest_rating', label: 'Lowest Score' },
              ].map((s) => (
                <button
                  key={s.id}
                  onClick={() => {
                    setReviewsSort(s.id)
                    fetchReviews(s.id)
                  }}
                  className={`px-2.5 py-1 rounded-lg text-xs font-medium transition ${
                    reviewsSort === s.id
                      ? 'bg-purple-600 text-white'
                      : 'bg-slate-900/80 text-slate-400 hover:text-slate-200 border border-purple-900/30'
                  }`}
                >
                  {s.label}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Reviews List */}
        {reviewsLoading ? (
          <div className="py-8 flex justify-center text-purple-400 text-xs">
            Loading reviews...
          </div>
        ) : reviews.length === 0 ? (
          <div className="p-6 rounded-2xl bg-purple-950/20 border border-purple-500/20 text-center text-xs font-mono text-slate-400 space-y-2">
            <p>No reviews written for this anime yet.</p>
            <button
              onClick={() => setWriteReviewModalOpen(true)}
              className="text-purple-400 hover:text-purple-300 font-bold underline"
            >
              Be the first to share your review!
            </button>
          </div>
        ) : (
          <div className="space-y-3">
            {reviews.map((rev) => {
              const isSpoilerHidden = rev.is_spoiler && !revealedReviewSpoilers[rev.id]

              return (
                <div
                  key={rev.id}
                  className="p-4 rounded-2xl bg-[#0c0e1e]/80 border border-purple-900/40 space-y-2.5 shadow-md"
                >
                  <div className="flex items-center justify-between text-xs">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-slate-200">
                        {rev.author?.display_name || 'Anonymous User'}
                      </span>
                      <span className="text-slate-500">•</span>
                      <span className="text-slate-500">
                        {new Date(rev.created_at).toLocaleDateString()}
                      </span>
                    </div>

                    <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-lg bg-purple-900/40 border border-purple-500/40 text-purple-300 font-bold text-xs">
                      <Star className="w-3 h-3 fill-purple-400 text-purple-400" />
                      <span>{rev.score}/10</span>
                    </div>
                  </div>

                  {rev.title && (
                    <h4 className="font-bold text-sm text-white">{rev.title}</h4>
                  )}

                  {isSpoilerHidden ? (
                    <div className="flex items-center justify-between p-2.5 rounded-xl bg-amber-950/20 border border-amber-900/40 text-xs">
                      <span className="text-amber-300 font-medium flex items-center gap-1.5">
                        <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
                        This review contains spoilers.
                      </span>
                      <button
                        onClick={() =>
                          setRevealedReviewSpoilers((prev) => ({
                            ...prev,
                            [rev.id]: true,
                          }))
                        }
                        className="text-amber-400 hover:underline font-semibold"
                      >
                        Reveal
                      </button>
                    </div>
                  ) : (
                    <p className="text-xs text-slate-300 leading-relaxed whitespace-pre-line">
                      {rev.body}
                    </p>
                  )}

                  <div className="flex items-center justify-between pt-1 border-t border-purple-950 text-xs text-slate-500">
                    <button
                      onClick={() => handleToggleHelpful(rev.id)}
                      className={`flex items-center gap-1.5 transition ${
                        rev.marked_helpful_by_me ? 'text-purple-400 font-bold' : 'hover:text-purple-300'
                      }`}
                    >
                      <ThumbsUp className={`w-3.5 h-3.5 ${rev.marked_helpful_by_me ? 'fill-current' : ''}`} />
                      <span>Helpful ({rev.helpful_count})</span>
                    </button>
                    {rev.is_spoiler && !isSpoilerHidden && (
                      <span className="text-[10px] text-amber-400/80 font-mono">Contains spoilers</span>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </section>

      {/* WRITE REVIEW MODAL */}
      {writeReviewModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
          <div className="relative w-full max-w-lg rounded-2xl bg-[#0c0c17] border border-purple-700/40 p-6 shadow-2xl shadow-purple-950/60 max-h-[90vh] overflow-y-auto">
            <button
              onClick={() => setWriteReviewModalOpen(false)}
              className="absolute top-5 right-5 text-slate-400 hover:text-white"
            >
              <X className="w-5 h-5" />
            </button>

            <h3 className="text-lg font-bold text-white mb-1 flex items-center gap-2">
              <Star className="w-4 h-4 text-purple-400 fill-purple-400" />
              <span>Review {details.title}</span>
            </h3>
            <p className="text-xs text-slate-400 mb-4 font-mono">
              Your honest assessment helps other fans decide what to watch.
            </p>

            {reviewError && (
              <div className="mb-4 p-3 rounded-xl bg-red-950/40 border border-red-800/40 text-xs text-red-300">
                {reviewError}
              </div>
            )}

            <form onSubmit={handleCreateReview} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                  Rating: <span className="text-purple-400 font-bold text-sm">{reviewScore}/10</span>
                </label>
                <input
                  type="range"
                  min="1"
                  max="10"
                  step="1"
                  value={reviewScore}
                  onChange={(e) => setReviewScore(e.target.value)}
                  className="w-full accent-purple-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                  Review Headline / Title (Optional)
                </label>
                <input
                  type="text"
                  maxLength={150}
                  value={reviewTitle}
                  onChange={(e) => setReviewTitle(e.target.value)}
                  placeholder="e.g. Masterpiece with unforgettable characters"
                  className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-purple-900/40 text-xs text-white placeholder-slate-600 focus:outline-none focus:border-purple-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                  Review Body * (20 - 2000 chars)
                </label>
                <textarea
                  rows={4}
                  minLength={20}
                  maxLength={2000}
                  value={reviewBody}
                  onChange={(e) => setReviewBody(e.target.value)}
                  placeholder="What makes this anime stand out? Story, animation, music, pacing..."
                  className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-purple-900/40 text-xs text-white placeholder-slate-600 focus:outline-none focus:border-purple-500 resize-none"
                />
                <p className="text-[10px] text-slate-500 mt-1">
                  {reviewBody.length}/2000 characters (min. 20)
                </p>
              </div>

              <div className="p-3 rounded-xl bg-slate-950 border border-purple-900/30 flex items-center justify-between">
                <div className="flex items-center gap-2 text-xs text-slate-300">
                  <AlertTriangle className="w-4 h-4 text-amber-400" />
                  <span>Review contains major plot spoilers</span>
                </div>
                <input
                  type="checkbox"
                  checked={reviewIsSpoiler}
                  onChange={(e) => setReviewIsSpoiler(e.target.checked)}
                  className="w-4 h-4 rounded border-purple-900 text-purple-600 focus:ring-0 bg-slate-900"
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setWriteReviewModalOpen(false)}
                  className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-400 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submittingReview}
                  className="px-5 py-2 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-semibold text-xs shadow-md shadow-purple-600/30 transition disabled:opacity-50"
                >
                  {submittingReview ? 'Submitting...' : 'Post Review'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Rating & Note Modal */}
      {existingEntry && (
        <EditRatingNoteModal
          entry={existingEntry}
          isOpen={ratingModalOpen}
          onClose={() => setRatingModalOpen(false)}
          onSave={saveRatingAndNote}
        />
      )}

      {/* Confirm Delete Modal */}
      {existingEntry && (
        <ConfirmDeleteModal
          entry={existingEntry}
          isOpen={deleteModalOpen}
          onClose={() => setDeleteModalOpen(false)}
          onConfirm={handleDeleteConfirm}
          deleting={deleting}
        />
      )}
    </div>
  )
}

export default AnimeDetailsPage

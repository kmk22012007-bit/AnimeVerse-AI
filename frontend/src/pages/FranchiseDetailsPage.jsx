import React, { useEffect, useState } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import {
  Layers,
  ArrowLeft,
  Film,
  Tv,
  Sparkles,
  Calendar,
  ExternalLink,
  ChevronRight,
  ShieldCheck,
  Play,
  Star,
} from 'lucide-react'
import { getFranchise } from '../api/anime'
import { HeroSkeleton } from '../components/common/LoadingSkeleton'
import ErrorState from '../components/common/ErrorState'
import AddToListButton from '../components/watchlist/AddToListButton'

export const FranchiseDetailsPage = () => {
  const { id } = useParams()
  const navigate = useNavigate()
  const [franchise, setFranchise] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    const fetchFranchiseData = async () => {
      setLoading(true)
      setError(null)
      try {
        const res = await getFranchise(id)
        setFranchise(res)
      } catch (err) {
        setError(err.message || 'Unable to retrieve franchise entries.')
      } finally {
        setLoading(false)
      }
    }

    if (id) {
      fetchFranchiseData()
    }
  }, [id])

  if (loading) {
    return <HeroSkeleton />
  }

  if (error || !franchise) {
    return (
      <div className="container mx-auto px-4 py-8">
        <ErrorState
          title="Franchise Not Found"
          message={error || 'Unable to load franchise details.'}
          onRetry={() => navigate(-1)}
        />
      </div>
    )
  }

  const {
    name,
    description,
    cover_image,
    entry_count,
    categories,
    main_entry,
  } = franchise

  const renderEntryCard = (entry) => {
    return (
      <Link
        key={entry.id}
        to={`/anime/${entry.mal_id}`}
        className="group relative flex flex-col rounded-2xl overflow-hidden bg-purple-950/25 border border-purple-500/20 hover:border-purple-400/60 transition-all duration-300 hover:shadow-[0_0_24px_rgba(168,85,247,0.3)] hover:-translate-y-1.5 focus:outline-none focus:ring-2 focus:ring-purple-400/60"
      >
        <div className="relative w-full aspect-[3/4] bg-purple-950/50 overflow-hidden">
          {entry.poster_url ? (
            <img
              src={entry.poster_url}
              alt={entry.title}
              className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center bg-purple-950/40 text-purple-400">
              <Film className="w-8 h-8" />
            </div>
          )}

          {/* Relationship badge */}
          <div className="absolute top-2.5 inset-x-2.5 flex items-center justify-between">
            <span className="px-2 py-0.5 rounded-lg bg-black/80 backdrop-blur-md border border-cyan-400/40 text-cyan-300 text-[10px] font-bold tracking-wider uppercase">
              {entry.relationship_label || entry.relationship_type}
            </span>
            <AddToListButton malId={entry.mal_id} compact className="pointer-events-auto z-20" />
          </div>

          {/* Hover play icon */}
          <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/40 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex items-center justify-center">
            <div className="w-10 h-10 rounded-full bg-purple-600/90 border border-purple-300 text-white flex items-center justify-center shadow-[0_0_20px_rgba(168,85,247,0.7)]">
              <Play className="w-4 h-4 fill-white ml-0.5" />
            </div>
          </div>

          {/* Format and Episode Count */}
          <div className="absolute bottom-2 inset-x-2 flex items-center justify-between text-[11px] text-slate-300">
            <span className="px-1.5 py-0.5 rounded bg-black/75 backdrop-blur-sm text-[10px] font-mono border border-white/10 uppercase">
              {entry.anime_type || 'Anime'}
            </span>
            {entry.total_episodes ? (
              <span className="px-1.5 py-0.5 rounded bg-black/75 backdrop-blur-sm text-[10px] font-mono border border-white/10">
                {entry.total_episodes} eps
              </span>
            ) : null}
          </div>
        </div>

        {/* Card Title & MAL ID */}
        <div className="p-3 flex flex-col flex-grow justify-between bg-black/40">
          <h4 className="text-sm font-semibold text-slate-200 group-hover:text-purple-300 line-clamp-2 transition-colors">
            {entry.title}
          </h4>
          <span className="text-[10px] font-mono text-purple-400/60 mt-1">MAL ID: {entry.mal_id}</span>
        </div>
      </Link>
    )
  }

  const renderSection = (title, items, icon) => {
    if (!items || items.length === 0) return null
    return (
      <div className="mb-10">
        <div className="flex items-center gap-2 mb-4 pb-2 border-b border-purple-500/20">
          {icon}
          <h3 className="text-lg font-bold text-white tracking-wide uppercase">{title}</h3>
          <span className="text-xs font-mono text-purple-400 ml-auto">{items.length} {items.length === 1 ? 'entry' : 'entries'}</span>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
          {items.map(renderEntryCard)}
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-[#0c0e1e] text-slate-100 pb-16">
      {/* Back navigation */}
      <div className="container mx-auto px-4 py-4">
        <button
          onClick={() => navigate(-1)}
          className="inline-flex items-center gap-2 px-3 py-1.5 rounded-xl bg-purple-950/40 border border-purple-500/30 text-purple-300 hover:text-white hover:bg-purple-900/50 transition-colors text-sm font-medium"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back</span>
        </button>
      </div>

      {/* Hero Header */}
      <div className="relative border-b border-purple-500/20 bg-gradient-to-b from-purple-950/40 via-purple-950/20 to-transparent">
        <div className="container mx-auto px-4 py-8">
          <div className="flex flex-col md:flex-row gap-8 items-start">
            {cover_image && (
              <div className="w-40 sm:w-48 aspect-[3/4] rounded-2xl overflow-hidden border border-purple-500/30 shadow-[0_0_30px_rgba(168,85,247,0.25)] flex-shrink-0">
                <img src={cover_image} alt={name} className="w-full h-full object-cover" />
              </div>
            )}

            <div className="flex-1">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-950/80 border border-indigo-400/40 text-indigo-300 text-xs font-bold tracking-wider uppercase mb-3 shadow-[0_0_15px_rgba(99,102,241,0.3)]">
                <Layers className="w-3.5 h-3.5 text-indigo-300" />
                <span>Franchise Grouping System</span>
              </div>

              <h1 className="text-3xl sm:text-4xl font-black text-white tracking-tight mb-3">
                {name}
              </h1>

              {description && (
                <p className="text-slate-300 text-sm sm:text-base leading-relaxed max-w-3xl mb-4">
                  {description}
                </p>
              )}

              <div className="flex flex-wrap items-center gap-4 text-xs font-mono text-purple-300/80">
                <div className="px-3 py-1.5 rounded-lg bg-black/40 border border-purple-500/30">
                  <span className="text-slate-400">Total Entries:</span>{' '}
                  <span className="text-cyan-300 font-bold">{entry_count}</span>
                </div>
                {main_entry && (
                  <div className="px-3 py-1.5 rounded-lg bg-black/40 border border-purple-500/30">
                    <span className="text-slate-400">Main Series:</span>{' '}
                    <span className="text-purple-300 font-bold">{main_entry.title}</span>
                  </div>
                )}
                <div className="px-3 py-1.5 rounded-lg bg-emerald-950/60 border border-emerald-500/40 text-emerald-300 flex items-center gap-1.5">
                  <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                  <span>Verified Provider Relationships</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Categorized Entries Sections */}
      <div className="container mx-auto px-4 py-8">
        {renderSection(
          'Main Series',
          categories?.main_series,
          <Tv className="w-5 h-5 text-purple-400" />
        )}

        {renderSection(
          'Sequels & Prequels',
          categories?.sequels_prequels,
          <Sparkles className="w-5 h-5 text-cyan-400" />
        )}

        {renderSection(
          'Movies & Films',
          categories?.movies,
          <Film className="w-5 h-5 text-amber-400" />
        )}

        {renderSection(
          'OVAs & Specials',
          categories?.ovas_specials,
          <Calendar className="w-5 h-5 text-pink-400" />
        )}

        {renderSection(
          'Spin-offs & Side Stories',
          categories?.spin_offs,
          <Layers className="w-5 h-5 text-indigo-400" />
        )}
      </div>
    </div>
  )
}

export default FranchiseDetailsPage

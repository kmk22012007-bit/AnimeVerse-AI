import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  Play,
  Flame,
  CheckCircle2,
  Tv,
  Star,
  Sparkles,
  ArrowRight,
  History,
  ImageOff,
  Compass,
} from 'lucide-react'
import { getDashboardData } from '../api/dashboard'
import { getAnimeDetails, browseAnime } from '../api/anime'
import StatCard from '../components/common/StatCard'
import AnimeCarousel from '../components/common/AnimeCarousel'
import ProgressCard from '../components/common/ProgressCard'
import ErrorState from '../components/common/ErrorState'
import EmptyState from '../components/common/EmptyState'
import { useWatchlist } from '../context/WatchlistContext'
import {
  HeroSkeleton,
  StatSkeleton,
  CardSkeleton,
  ProgressSkeleton,
} from '../components/common/LoadingSkeleton'

export const DashboardPage = () => {
  const { refreshKey } = useWatchlist()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Hero anime details (synopsis, real banner, genres)
  const [heroDetails, setHeroDetails] = useState(null)
  const [backdropError, setBackdropError] = useState(false)

  // Real recommendations from catalog
  const [recommended, setRecommended] = useState([])

  const fetchDashboard = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await getDashboardData()
      setData(response)

      // Fetch recommended TV anime using real API (type: 'tv')
      try {
        const recRes = await browseAnime({ type: 'tv', page: 1 })
        if (recRes?.results) {
          setRecommended(recRes.results)
        }
      } catch (recErr) {
        console.debug('Recommended fetch non-fatal fallback:', recErr)
      }
    } catch (err) {
      setError(err.message || 'Failed to connect to AnimeVerse dashboard.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchDashboard()
  }, [refreshKey])

  const trending = data?.trending || data?.trending_strip?.items || []
  const heroAnime = trending.length > 0 ? trending[0] : null

  // Fetch full details (synopsis, banner) for the top trending hero anime
  useEffect(() => {
    if (heroAnime?.mal_id) {
      setBackdropError(false)
      getAnimeDetails(heroAnime.mal_id)
        .then((res) => {
          setHeroDetails(res?.data || res)
        })
        .catch((err) => {
          console.debug('Hero details fetch non-fatal:', err)
        })
    }
  }, [heroAnime?.mal_id])

  if (loading) {
    return (
      <div className="space-y-10">
        <HeroSkeleton />
        <StatSkeleton />
        <div className="space-y-4">
          <div className="h-6 w-48 bg-purple-500/20 rounded"></div>
          <ProgressSkeleton />
        </div>
        <div className="space-y-4">
          <div className="h-6 w-48 bg-purple-500/20 rounded"></div>
          <CardSkeleton count={5} />
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <ErrorState
        title="Dashboard Offline"
        message={error}
        onRetry={fetchDashboard}
      />
    )
  }

  const welcome = data?.welcome || {}
  const stats = data?.stats || data?.statistics || {}
  const watching = data?.watching || data?.currently_watching || []
  const recent = data?.recent || data?.recently_updated || []

  // Resolve hero backdrop: prefer banner_url, fallback to poster_url, fallback to null
  const heroBackdrop =
    !backdropError && (heroDetails?.banner_url || heroAnime?.poster_url)
      ? heroDetails?.banner_url || heroAnime?.poster_url
      : null

  const heroPoster = heroDetails?.poster_url || heroAnime?.poster_url
  const heroSynopsis = heroDetails?.synopsis
  const heroGenres = heroDetails?.genres || []

  return (
    <div className="space-y-10">
      {/* 1. Cinematic Dashboard Hero Banner */}
      {heroAnime && (
        <div className="relative rounded-3xl overflow-hidden border border-purple-500/30 bg-[#0c0e1c] shadow-[0_0_35px_rgba(168,85,247,0.22)]">
          {/* Real Anime Backdrop Image with Dark Gradient Overlays */}
          {heroBackdrop ? (
            <div className="absolute inset-0 overflow-hidden">
              <img
                src={heroBackdrop}
                alt={heroAnime.title}
                onError={() => setBackdropError(true)}
                className="w-full h-full object-cover object-center opacity-30 filter blur-[2px] scale-105 transition-opacity duration-700"
              />
              {/* Deep multi-directional gradient overlay for 100% text readability */}
              <div className="absolute inset-0 bg-gradient-to-r from-[#07080f] via-[#07080f]/95 md:via-[#07080f]/85 to-[#07080f]/40"></div>
              <div className="absolute inset-0 bg-gradient-to-t from-[#07080f] via-[#07080f]/60 to-transparent"></div>
              <div className="absolute inset-0 bg-[radial-gradient(circle_at_80%_40%,_var(--tw-gradient-stops))] from-purple-900/20 via-transparent to-transparent"></div>
            </div>
          ) : (
            /* Graceful Cyberpunk Fallback Backdrop */
            <div className="absolute inset-0 bg-gradient-to-br from-purple-950/40 via-[#0a0c18] to-indigo-950/40 cyber-grid">
              <div className="absolute inset-0 bg-gradient-to-t from-[#07080f] via-transparent to-transparent"></div>
            </div>
          )}

          {/* Hero Content Area */}
          <div className="relative p-6 sm:p-10 lg:p-12 flex flex-col md:flex-row items-center justify-between gap-8 min-h-[380px] sm:min-h-[420px]">
            {/* Left Content Column */}
            <div className="max-w-2xl flex flex-col justify-end">
              <div className="flex flex-wrap items-center gap-2 mb-3">
                <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-purple-600/30 border border-purple-400/50 text-purple-200 text-xs font-mono font-bold tracking-wider shadow-[0_0_12px_rgba(168,85,247,0.5)]">
                  <Flame className="w-3.5 h-3.5 text-cyan-400 fill-cyan-400" />
                  <span>#1 TRENDING ANIME</span>
                </div>

                {heroAnime.metadata_source && (
                  <span className="px-2 py-0.5 rounded-full bg-black/60 border border-purple-500/30 text-[10px] font-mono text-purple-300 uppercase">
                    Source: {heroAnime.metadata_source}
                  </span>
                )}
              </div>

              <h1 className="text-2xl sm:text-4xl lg:text-5xl font-extrabold tracking-tight text-white mb-2 leading-tight">
                {heroAnime.title_english || heroAnime.title}
              </h1>

              {heroAnime.title_english && heroAnime.title && heroAnime.title_english !== heroAnime.title && (
                <p className="text-xs sm:text-sm text-purple-300/90 font-mono mb-3">
                  {heroAnime.title}
                </p>
              )}

              {/* Badges: Score, Type, Episodes */}
              <div className="flex flex-wrap items-center gap-3 text-xs font-mono text-slate-300 mb-4">
                {heroAnime.score && (
                  <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-black/75 border border-cyan-400/40 text-cyan-300 font-bold shadow-sm">
                    <Star className="w-3.5 h-3.5 fill-cyan-400 text-cyan-400" />
                    <span>{heroAnime.score} MAL SCORE</span>
                  </div>
                )}
                {heroAnime.anime_type && (
                  <span className="px-2.5 py-1 rounded-lg bg-black/75 border border-purple-400/30 text-purple-300 font-semibold">
                    {heroAnime.anime_type}
                  </span>
                )}
                {heroAnime.total_episodes && (
                  <span className="px-2.5 py-1 rounded-lg bg-black/75 border border-white/10 text-slate-300">
                    {heroAnime.total_episodes} EPISODES
                  </span>
                )}
              </div>

              {/* Real Synopsis when available */}
              {heroSynopsis ? (
                <p className="text-xs sm:text-sm text-slate-300 leading-relaxed line-clamp-3 max-w-xl mb-5 font-normal">
                  {heroSynopsis}
                </p>
              ) : (
                <p className="text-xs text-slate-400 mb-5 font-mono">
                  Verified trending title streaming in global catalogs.
                </p>
              )}

              {/* Genres Pills */}
              {heroGenres.length > 0 && (
                <div className="flex flex-wrap gap-1.5 mb-6">
                  {heroGenres.slice(0, 4).map((g) => (
                    <span
                      key={g}
                      className="px-2.5 py-0.5 rounded-lg bg-purple-900/40 border border-purple-500/30 text-[11px] text-purple-200 font-mono"
                    >
                      {g}
                    </span>
                  ))}
                </div>
              )}

              {/* Action Buttons */}
              <div className="flex flex-wrap items-center gap-3">
                <Link
                  to={`/anime/${heroAnime.mal_id}`}
                  className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-bold text-sm transition-all shadow-[0_0_20px_rgba(168,85,247,0.6)] hover:shadow-[0_0_30px_rgba(168,85,247,0.9)] cursor-pointer"
                >
                  <Play className="w-4 h-4 fill-white" />
                  <span>Explore Title</span>
                </Link>
                <Link
                  to="/discover"
                  className="inline-flex items-center gap-2 px-5 py-3 rounded-xl bg-purple-950/70 hover:bg-purple-900/70 border border-purple-500/40 text-purple-200 font-semibold text-sm transition-all cursor-pointer"
                >
                  <span>View Full Catalog</span>
                  <ArrowRight className="w-4 h-4" />
                </Link>
              </div>
            </div>

            {/* Right Poster Preview Card (Desktop) */}
            {heroPoster && (
              <div className="hidden md:block w-48 lg:w-56 aspect-[3/4] rounded-2xl overflow-hidden border border-purple-400/40 shadow-[0_0_30px_rgba(168,85,247,0.35)] flex-shrink-0 group">
                <img
                  src={heroPoster}
                  alt={heroAnime.title}
                  className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
                />
              </div>
            )}
          </div>
        </div>
      )}

      {/* 2. Live Dashboard Statistics Grid */}
      <section aria-labelledby="stats-heading" className="space-y-3">
        <h2 id="stats-heading" className="sr-only">Dashboard Metrics</h2>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">
          <StatCard
            icon={CheckCircle2}
            label="Completed Anime"
            value={stats.completed_count ?? 0}
            sublabel="Finished series in your records"
            accent="purple"
          />
          <StatCard
            icon={Tv}
            label="Episodes Watched"
            value={stats.total_episodes_watched ?? 0}
            sublabel="Total episodes across all lists"
            accent="cyan"
          />
          <StatCard
            icon={Star}
            label="Average Score"
            value={
              typeof stats.average_rating === 'number'
                ? stats.average_rating.toFixed(1)
                : stats.average_rating || 'No ratings yet'
            }
            sublabel="Calculated user rating score"
            accent="emerald"
          />
        </div>
      </section>

      {/* 3. Currently Watching Section */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 shadow-[0_0_8px_rgba(6,182,212,0.8)]"></span>
            Currently Watching
          </h2>
          {watching.length > 0 && (
            <Link
              to="/list"
              className="text-xs text-purple-400 hover:text-purple-300 font-medium"
            >
              View Full Watchlist →
            </Link>
          )}
        </div>

        {watching.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {watching.map((entry) => (
              <ProgressCard key={entry.id} entry={entry} />
            ))}
          </div>
        ) : (
          <div className="rounded-3xl border border-purple-500/20 bg-gradient-to-b from-purple-950/20 via-[#0d0f1e] to-purple-950/15 p-8 sm:p-10 text-center relative overflow-hidden backdrop-blur-sm">
            <div className="w-14 h-14 rounded-2xl bg-purple-500/10 border border-purple-500/30 text-purple-400 flex items-center justify-center mx-auto mb-4 shadow-[0_0_15px_rgba(168,85,247,0.15)]">
              <Compass className="w-7 h-7" />
            </div>
            <h3 className="text-base sm:text-lg font-bold text-slate-100 mb-2">
              No Anime Currently in Progress
            </h3>
            <p className="text-xs sm:text-sm text-slate-400 max-w-md mx-auto mb-6 leading-relaxed">
              Your watchlist is currently clear. Browse top-ranked trending series below or explore the full catalog to start tracking your episode progress.
            </p>
            <Link
              to="/discover"
              className="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-semibold text-xs sm:text-sm transition-all shadow-[0_0_15px_rgba(168,85,247,0.4)]"
            >
              <span>Explore Trending Anime</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        )}
      </section>

      {/* 4. Real Trending Anime Strip */}
      <section>
        <AnimeCarousel
          items={trending}
          title="Trending Across AnimeVerse"
          subtitle="Top ranked and popular anime verified via upstream provider records"
        />
      </section>

      {/* 5. Recommended TV Classics (from real API browse data) */}
      {recommended.length > 0 && (
        <section>
          <AnimeCarousel
            items={recommended}
            title="Recommended Television Classics"
            subtitle="Top-rated legendary anime series from verified database records"
          />
        </section>
      )}

      {/* 6. Recently Updated Items (if user has watch history) */}
      {recent.length > 0 && (
        <section className="space-y-4">
          <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
            <History className="w-4 h-4 text-purple-400" />
            Recently Updated in Your List
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {recent.map((entry) => (
              <ProgressCard key={entry.id} entry={entry} />
            ))}
          </div>
        </section>
      )}
    </div>
  )
}

export default DashboardPage

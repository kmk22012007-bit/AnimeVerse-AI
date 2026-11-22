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
  Clock,
  Award,
  Zap,
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
  const watching = data?.continue_watching || data?.watching || data?.currently_watching || []
  const recent = data?.recent || data?.recently_updated || []
  const recentlyCompleted = data?.recently_completed || []
  const becauseYouWatched = data?.because_you_watched || null
  const recommendedForYou =
    data?.recommended_for_you && data.recommended_for_you.length > 0
      ? data.recommended_for_you
      : recommended
  const exploreNewGenres = data?.explore_new_genres || []
  const journey = data?.your_anime_journey || null

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

      {/* 2.5 Your Anime Journey (Personalized Stats & Velocity) */}
      {journey && (
        <section aria-labelledby="journey-heading" className="p-5 sm:p-6 rounded-3xl bg-[#0e101d]/90 border border-purple-500/25 shadow-[0_0_25px_rgba(168,85,247,0.12)] backdrop-blur-md">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-4 pb-3 border-b border-purple-500/20">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-xl bg-purple-500/20 border border-purple-500/40 flex items-center justify-center text-purple-300">
                <Sparkles className="w-4 h-4 text-cyan-400" />
              </div>
              <div>
                <h3 id="journey-heading" className="text-sm font-bold text-white flex items-center gap-2">
                  Your Anime Journey
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-purple-500/20 text-purple-300 border border-purple-400/30">
                    Live Signals
                  </span>
                </h3>
                <p className="text-xs text-slate-400">Dynamic viewing velocity and taste indicators</p>
              </div>
            </div>
            <Link
              to="/profile"
              className="text-xs font-mono text-cyan-400 hover:text-cyan-300 flex items-center gap-1"
            >
              <span>Taste Profile & Preferences</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs font-mono">
            <div className="p-3.5 rounded-2xl bg-[#131627]/80 border border-purple-500/20">
              <span className="text-[10px] text-slate-400 block mb-1">Time Invested</span>
              <div className="text-xl font-black text-cyan-300 flex items-baseline gap-1">
                <span>{journey.estimated_hours_watched || 0}</span>
                <span className="text-xs font-normal text-slate-400">hours</span>
              </div>
              <span className="text-[10px] text-slate-500">~24 mins/ep calculation</span>
            </div>

            <div className="p-3.5 rounded-2xl bg-[#131627]/80 border border-purple-500/20">
              <span className="text-[10px] text-slate-400 block mb-1">Completion Rate</span>
              <div className="text-xl font-black text-emerald-400 flex items-baseline gap-1">
                <span>{journey.completion_rate_pct || 0}%</span>
              </div>
              <span className="text-[10px] text-emerald-300/70">Finished vs total tracked</span>
            </div>

            <div className="p-3.5 rounded-2xl bg-[#131627]/80 border border-purple-500/20">
              <span className="text-[10px] text-slate-400 block mb-1">Top Genre Affinity</span>
              <div className="text-base font-bold text-purple-200 truncate mt-0.5">
                {journey.top_genre || 'Eclectic Explorer'}
              </div>
              <span className="text-[10px] text-purple-400">Primary viewing focus</span>
            </div>

            <div className="p-3.5 rounded-2xl bg-[#131627]/80 border border-purple-500/20">
              <span className="text-[10px] text-slate-400 block mb-1">Episodes Tracked</span>
              <div className="text-xl font-black text-amber-400">
                {journey.episodes_watched || 0}
              </div>
              <span className="text-[10px] text-amber-300/70">Across active watchlists</span>
            </div>
          </div>
        </section>
      )}

      {/* 3. Continue Watching Section */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 shadow-[0_0_8px_rgba(6,182,212,0.8)]"></span>
            Continue Watching
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

      {/* 4. Because You Watched Carousel */}
      {becauseYouWatched?.seed_anime && becauseYouWatched?.recommendations?.length > 0 && (
        <section>
          <AnimeCarousel
            items={becauseYouWatched.recommendations}
            title={`Because You Watched: ${becauseYouWatched.seed_anime.title}`}
            subtitle="Personalized recommendations grounded in your highest rated completed anime"
          />
        </section>
      )}

      {/* 5. Recommended For You (Personalized Engine) */}
      {recommendedForYou.length > 0 && (
        <section>
          <AnimeCarousel
            items={recommendedForYou}
            title="Recommended For You"
            subtitle="Personalized recommendations tailored to your taste profile & watch activity"
          />
        </section>
      )}

      {/* 6. Explore New Horizons (Genre Diversity) */}
      {exploreNewGenres.length > 0 && (
        <section>
          <AnimeCarousel
            items={exploreNewGenres}
            title="Explore New Horizons"
            subtitle="Top-rated anime outside your usual genres to diversify your taste"
          />
        </section>
      )}

      {/* 7. Recently Completed Anime */}
      {recentlyCompleted.length > 0 && (
        <section className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
              <CheckCircle2 className="w-5 h-5 text-emerald-400" />
              Recently Completed
            </h2>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-4">
            {recentlyCompleted.map((item) => (
              <Link
                key={item.mal_id}
                to={`/anime/${item.mal_id}`}
                className="group relative flex flex-col rounded-2xl overflow-hidden bg-purple-950/25 border border-purple-500/20 hover:border-purple-400/60 transition-all duration-300 hover:shadow-[0_0_20px_rgba(168,85,247,0.3)] hover:-translate-y-1"
              >
                <div className="relative aspect-[3/4] bg-purple-950/50 overflow-hidden">
                  {item.poster_url ? (
                    <img
                      src={item.poster_url}
                      alt={item.title}
                      className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center text-purple-400 font-mono text-xs">
                      ANIME
                    </div>
                  )}
                  {item.rating && (
                    <div className="absolute top-2 right-2 inline-flex items-center gap-1 px-2 py-0.5 rounded-lg bg-black/80 backdrop-blur-md border border-amber-400/40 text-amber-300 text-xs font-bold">
                      <Star className="w-3 h-3 fill-amber-400 text-amber-400" />
                      <span>{item.rating}/10</span>
                    </div>
                  )}
                </div>
                <div className="p-3 bg-gradient-to-b from-purple-950/30 to-purple-950/60">
                  <h4 className="text-xs font-bold text-white truncate group-hover:text-purple-300">
                    {item.title}
                  </h4>
                  <span className="text-[10px] font-mono text-emerald-400 mt-0.5 block">
                    ✓ Completed
                  </span>
                </div>
              </Link>
            ))}
          </div>
        </section>
      )}

      {/* 8. Trending Across AnimeVerse */}
      <section>
        <AnimeCarousel
          items={trending}
          title="Trending Across AnimeVerse"
          subtitle="Top ranked and popular anime verified via upstream provider records"
        />
      </section>

      {/* 9. Recently Updated in List */}
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

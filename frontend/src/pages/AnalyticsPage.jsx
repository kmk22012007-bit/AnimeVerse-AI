import React, { useState, useEffect, useCallback } from 'react'
import {
  BarChart3,
  PieChart as PieChartIcon,
  TrendingUp,
  Award,
  Sparkles,
  Flame,
  CheckCircle2,
  Calendar,
  Layers,
  Star,
  RefreshCw,
  Clock,
  ShieldCheck,
  ArrowRight,
  Info,
} from 'lucide-react'
import { Link } from 'react-router-dom'
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  PieChart,
  Pie,
  Cell,
  AreaChart,
  Area,
  CartesianGrid,
} from 'recharts'
import { getAnalyticsOverview } from '../api/analytics'
import ErrorState from '../components/common/ErrorState'
import EmptyState from '../components/common/EmptyState'

// Cyberpunk theme colors
const CYBERPUNK_PALETTE = [
  '#a855f7', // Purple
  '#06b6d4', // Cyan
  '#ec4899', // Pink
  '#10b981', // Emerald
  '#f59e0b', // Amber
  '#8b5cf6', // Violet
  '#3b82f6', // Blue
  '#f43f5e', // Rose
  '#14b8a6', // Teal
  '#6366f1', // Indigo
]

export const AnalyticsPage = () => {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [isRefreshing, setIsRefreshing] = useState(false)

  const fetchAnalytics = useCallback(async (refresh = false) => {
    if (refresh) setIsRefreshing(true)
    else setLoading(true)
    setError(null)

    try {
      const res = await getAnalyticsOverview()
      setData(res)
    } catch (err) {
      setError(err?.response?.data?.message || err.message || 'Unable to load personal tracking analytics.')
    } finally {
      setLoading(false)
      setIsRefreshing(false)
    }
  }, [])

  useEffect(() => {
    fetchAnalytics()
  }, [fetchAnalytics])

  // Custom Dark Cyberpunk Tooltip for Recharts
  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="p-3 rounded-2xl bg-[#0c0e1e]/95 border border-purple-500/40 shadow-[0_0_20px_rgba(0,0,0,0.8)] text-xs font-mono space-y-1">
          <p className="font-bold text-white text-sm">{label || payload[0]?.name}</p>
          {payload.map((entry, index) => (
            <p key={index} style={{ color: entry.color || entry.fill || '#06b6d4' }}>
              {entry.name}: <span className="font-bold text-white">{entry.value}</span>
              {entry.payload?.percentage ? ` (${entry.payload.percentage}%)` : ''}
            </p>
          ))}
        </div>
      )
    }
    return null
  }

  return (
    <div className="space-y-8 max-w-7xl mx-auto pb-12">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-purple-500/20 pb-5">
        <div>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-purple-700 via-fuchsia-600 to-cyan-500 p-0.5 shadow-[0_0_20px_rgba(168,85,247,0.4)]">
              <div className="w-full h-full rounded-[14px] bg-[#0c0e1e] flex items-center justify-center">
                <BarChart3 className="w-5 h-5 text-purple-300" />
              </div>
            </div>
            <div>
              <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-wide flex items-center gap-2.5">
                Advanced Analytics Hub
              </h1>
              <p className="text-xs sm:text-sm text-slate-400 font-mono mt-0.5 flex items-center gap-2">
                <span className="inline-block w-2 h-2 rounded-full bg-cyan-400 animate-pulse"></span>
                Authenticated Data • Live Database Records • Zero Fabricated Stats
              </p>
            </div>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-3 self-start sm:self-auto">
          <button
            onClick={() => fetchAnalytics(true)}
            disabled={loading || isRefreshing}
            type="button"
            className="px-4 py-2.5 rounded-xl bg-purple-900/40 hover:bg-purple-800/60 border border-purple-500/40 text-xs font-semibold text-purple-200 transition-all flex items-center gap-2 shadow-sm disabled:opacity-50 cursor-pointer"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin text-cyan-400' : ''}`} />
            <span>{isRefreshing ? 'Recalibrating...' : 'Refresh Data'}</span>
          </button>
        </div>
      </div>

      {/* Loading Skeleton */}
      {loading && !isRefreshing && (
        <div className="space-y-6 animate-pulse">
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="h-28 rounded-2xl bg-purple-950/20 border border-purple-500/10"></div>
            ))}
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="h-80 rounded-3xl bg-purple-950/20 border border-purple-500/10"></div>
            <div className="h-80 rounded-3xl bg-purple-950/20 border border-purple-500/10"></div>
          </div>
        </div>
      )}

      {/* Error View */}
      {error && !loading && (
        <ErrorState
          title="Failed to Load Analytics"
          message={error}
          onRetry={() => fetchAnalytics(true)}
        />
      )}

      {/* Empty State View */}
      {!loading && !error && data && !data.has_data && (
        <EmptyState
          title="No Watch History Recorded"
          message="Your personal analytics dashboard relies on authenticated records in your watchlist. Track your first anime or update your episode progress to generate deep insights."
          actionLabel="Explore Anime Catalog"
          onAction={() => {}}
        />
      )}

      {/* Main Analytics Content */}
      {!loading && !error && data && data.has_data && (
        <div className="space-y-8">
          {/* ======================================================== */}
          {/* SECTION 1: KEY STATS COUNTERS GRID                       */}
          {/* ======================================================== */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
            {/* Total Tracked */}
            <div className="p-4 rounded-2xl bg-[#0c0e1e] border border-purple-500/30 shadow-[0_0_15px_rgba(168,85,247,0.1)] flex flex-col justify-between">
              <span className="text-[11px] font-mono text-slate-400 flex items-center gap-1.5">
                <Layers className="w-3.5 h-3.5 text-purple-400" /> Total Tracked
              </span>
              <div className="mt-2 text-2xl sm:text-3xl font-extrabold text-white">
                {data.stats.total_tracked}
              </div>
              <span className="text-[10px] font-mono text-purple-300 mt-1">
                {data.stats.most_watched_format || 'TV'} primary format
              </span>
            </div>

            {/* Total Episodes Watched */}
            <div className="p-4 rounded-2xl bg-[#0c0e1e] border border-cyan-500/30 shadow-[0_0_15px_rgba(6,182,212,0.1)] flex flex-col justify-between">
              <span className="text-[11px] font-mono text-slate-400 flex items-center gap-1.5">
                <Flame className="w-3.5 h-3.5 text-cyan-400" /> Episodes Watched
              </span>
              <div className="mt-2 text-2xl sm:text-3xl font-extrabold text-cyan-300">
                {data.stats.total_episodes_watched}
              </div>
              <span className="text-[10px] font-mono text-cyan-400/80 mt-1">
                From recorded progress
              </span>
            </div>

            {/* Completed Count & Rate */}
            <div className="p-4 rounded-2xl bg-[#0c0e1e] border border-emerald-500/30 shadow-[0_0_15px_rgba(16,185,129,0.1)] flex flex-col justify-between">
              <span className="text-[11px] font-mono text-slate-400 flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" /> Completed
              </span>
              <div className="mt-2 text-2xl sm:text-3xl font-extrabold text-emerald-300">
                {data.stats.completed_count}
              </div>
              <span className="text-[10px] font-mono text-emerald-400/80 mt-1">
                {data.stats.completion_rate}% finish rate
              </span>
            </div>

            {/* Currently Watching */}
            <div className="p-4 rounded-2xl bg-[#0c0e1e] border border-blue-500/30 shadow-[0_0_15px_rgba(59,130,246,0.1)] flex flex-col justify-between">
              <span className="text-[11px] font-mono text-slate-400 flex items-center gap-1.5">
                <Clock className="w-3.5 h-3.5 text-blue-400" /> In Progress
              </span>
              <div className="mt-2 text-2xl sm:text-3xl font-extrabold text-blue-300">
                {data.stats.watching_count}
              </div>
              <span className="text-[10px] font-mono text-blue-400/80 mt-1">
                Active series
              </span>
            </div>

            {/* Average Rating */}
            <div className="p-4 rounded-2xl bg-[#0c0e1e] border border-amber-500/30 shadow-[0_0_15px_rgba(245,158,11,0.1)] flex flex-col justify-between">
              <span className="text-[11px] font-mono text-slate-400 flex items-center gap-1.5">
                <Star className="w-3.5 h-3.5 text-amber-400 fill-amber-400" /> Mean Score
              </span>
              <div className="mt-2 text-2xl sm:text-3xl font-extrabold text-amber-300">
                {data.stats.average_rating !== null ? `${data.stats.average_rating}` : 'N/A'}
              </div>
              <span className="text-[10px] font-mono text-amber-400/80 mt-1">
                {data.stats.rated_count} of {data.stats.total_tracked} rated
              </span>
            </div>

            {/* Genres Explored */}
            <div className="p-4 rounded-2xl bg-[#0c0e1e] border border-pink-500/30 shadow-[0_0_15px_rgba(236,72,153,0.1)] flex flex-col justify-between">
              <span className="text-[11px] font-mono text-slate-400 flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-pink-400" /> Genres Explored
              </span>
              <div className="mt-2 text-2xl sm:text-3xl font-extrabold text-pink-300">
                {data.stats.total_genres_explored}
              </div>
              <span className="text-[10px] font-mono text-pink-400/80 mt-1">
                Unique categories
              </span>
            </div>
          </div>

          {/* ======================================================== */}
          {/* SECTION 2: CHARTS ROW 1 (GENRES & RATINGS)              */}
          {/* ======================================================== */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Genre Distribution Chart */}
            <div className="p-5 sm:p-6 rounded-3xl bg-[#0c0e1e] border border-purple-500/30 shadow-[0_0_30px_rgba(0,0,0,0.5)] flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between">
                  <h3 className="text-base sm:text-lg font-bold text-white flex items-center gap-2">
                    <PieChartIcon className="w-5 h-5 text-purple-400" />
                    Genre Distribution
                  </h3>
                  <span className="text-[11px] font-mono text-purple-300 px-2 py-0.5 rounded-lg bg-purple-950/60 border border-purple-500/30">
                    {data.genres.total_appearances} Total Tags
                  </span>
                </div>
                <p className="text-xs text-slate-400 font-mono mt-1">
                  {data.genres.explanation}
                </p>
              </div>

              {/* Pie Chart & Ranked Legend */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 items-center mt-4">
                <div className="h-56 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={data.genres.distribution}
                        dataKey="count"
                        nameKey="name"
                        cx="50%"
                        cy="50%"
                        outerRadius={80}
                        innerRadius={45}
                        paddingAngle={3}
                      >
                        {data.genres.distribution.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color || CYBERPUNK_PALETTE[index % CYBERPUNK_PALETTE.length]} />
                        ))}
                      </Pie>
                      <Tooltip content={<CustomTooltip />} />
                    </PieChart>
                  </ResponsiveContainer>
                </div>

                {/* Ranked Genre Legend List */}
                <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
                  {data.genres.distribution.slice(0, 6).map((item, idx) => (
                    <div key={idx} className="flex items-center justify-between text-xs font-mono">
                      <div className="flex items-center gap-2">
                        <span
                          className="w-2.5 h-2.5 rounded-full flex-shrink-0"
                          style={{ backgroundColor: item.color }}
                        />
                        <span className="text-slate-200 truncate max-w-[110px]">{item.name}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-slate-400">{item.count}</span>
                        <span className="text-purple-300 font-semibold">{item.percentage}%</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Personal Rating Distribution Chart */}
            <div className="p-5 sm:p-6 rounded-3xl bg-[#0c0e1e] border border-purple-500/30 shadow-[0_0_30px_rgba(0,0,0,0.5)] flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between">
                  <h3 className="text-base sm:text-lg font-bold text-white flex items-center gap-2">
                    <Star className="w-5 h-5 text-amber-400 fill-amber-400" />
                    Personal Rating Distribution
                  </h3>
                  <span className="text-[11px] font-mono text-amber-300 px-2 py-0.5 rounded-lg bg-amber-950/40 border border-amber-500/30">
                    Mean: {data.ratings.average_rating ? `${data.ratings.average_rating}/10` : 'None'}
                  </span>
                </div>
                <p className="text-xs text-slate-400 font-mono mt-1">
                  Distribution of scores across your {data.ratings.rated_count} rated titles (1 to 10 stars).
                </p>
              </div>

              {/* Bar Chart */}
              <div className="h-56 w-full mt-4">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={data.ratings.distribution} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#2e1065" opacity={0.4} />
                    <XAxis dataKey="label" stroke="#94a3b8" fontSize={11} tickLine={false} />
                    <YAxis stroke="#94a3b8" fontSize={11} allowDecimals={false} tickLine={false} />
                    <Tooltip content={<CustomTooltip />} />
                    <Bar dataKey="count" name="Rated Anime" fill="#a855f7" radius={[6, 6, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          {/* ======================================================== */}
          {/* SECTION 3: CHARTS ROW 2 (ACTIVITY TIMELINE & WATCHLIST)  */}
          {/* ======================================================== */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Watching Activity Timeline */}
            <div className="p-5 sm:p-6 rounded-3xl bg-[#0c0e1e] border border-purple-500/30 shadow-[0_0_30px_rgba(0,0,0,0.5)] flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between">
                  <h3 className="text-base sm:text-lg font-bold text-white flex items-center gap-2">
                    <TrendingUp className="w-5 h-5 text-cyan-400" />
                    Watching Activity Timeline
                  </h3>
                  {data.activity.most_active_month && (
                    <span className="text-[11px] font-mono text-cyan-300 px-2 py-0.5 rounded-lg bg-cyan-950/40 border border-cyan-500/30">
                      Peak: {data.activity.most_active_month.label}
                    </span>
                  )}
                </div>
                <p className="text-xs text-slate-400 font-mono mt-1">
                  {data.activity.scope_disclaimer}
                </p>
              </div>

              <div className="h-56 w-full mt-4">
                {data.activity.timeline.length > 0 ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={data.activity.timeline} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
                      <defs>
                        <linearGradient id="episodesGrad" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.6} />
                          <stop offset="95%" stopColor="#06b6d4" stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="#164e63" opacity={0.3} />
                      <XAxis dataKey="label" stroke="#94a3b8" fontSize={11} tickLine={false} />
                      <YAxis stroke="#94a3b8" fontSize={11} allowDecimals={false} tickLine={false} />
                      <Tooltip content={<CustomTooltip />} />
                      <Area
                        type="monotone"
                        dataKey="episodes"
                        name="Episodes Watched"
                        stroke="#06b6d4"
                        fillOpacity={1}
                        fill="url(#episodesGrad)"
                        strokeWidth={2}
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="h-full flex items-center justify-center text-xs font-mono text-slate-500">
                    No timestamped episode activity recorded yet.
                  </div>
                )}
              </div>
            </div>

            {/* Watchlist Status Distribution */}
            <div className="p-5 sm:p-6 rounded-3xl bg-[#0c0e1e] border border-purple-500/30 shadow-[0_0_30px_rgba(0,0,0,0.5)] flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between">
                  <h3 className="text-base sm:text-lg font-bold text-white flex items-center gap-2">
                    <Layers className="w-5 h-5 text-emerald-400" />
                    Watchlist Breakdown & Backlog
                  </h3>
                  <span className="text-[11px] font-mono text-emerald-300 px-2 py-0.5 rounded-lg bg-emerald-950/40 border border-emerald-500/30">
                    Backlog: {data.watchlist.plan_to_watch_backlog} Series
                  </span>
                </div>
                <p className="text-xs text-slate-400 font-mono mt-1">
                  Distribution of entries across all 5 official tracking states.
                </p>
              </div>

              {/* Status List with Progress Bars */}
              <div className="space-y-3 mt-4">
                {data.watchlist.status_distribution.map((item, idx) => (
                  <div key={idx} className="space-y-1">
                    <div className="flex items-center justify-between text-xs font-mono">
                      <span className="text-slate-200 font-medium">{item.status}</span>
                      <span className="text-slate-400">
                        <strong className="text-white">{item.count}</strong> ({item.percentage}%)
                      </span>
                    </div>
                    <div className="w-full h-2 rounded-full bg-purple-950/60 overflow-hidden">
                      <div
                        className="h-full rounded-full transition-all duration-500"
                        style={{ width: `${item.percentage}%`, backgroundColor: item.color }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* ======================================================== */}
          {/* SECTION 4: CALCULATED PERSONAL INSIGHTS                  */}
          {/* ======================================================== */}
          <div className="space-y-4">
            <h3 className="text-lg font-bold text-white flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-cyan-400" />
              Automated Tracking Insights
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {data.insights.map((insight) => (
                <div
                  key={insight.id}
                  className="p-4 rounded-2xl bg-[#0c0e1e] border border-purple-500/30 shadow-[0_0_20px_rgba(168,85,247,0.1)] flex flex-col justify-between space-y-2"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-cyan-300 px-2 py-0.5 rounded-md bg-cyan-950/50 border border-cyan-400/30">
                      {insight.category}
                    </span>
                    <span className="text-[9px] font-mono text-purple-300 flex items-center gap-1">
                      <CheckCircle2 className="w-3 h-3 text-emerald-400" /> Verified Stat
                    </span>
                  </div>
                  <h4 className="text-sm font-bold text-white leading-tight">{insight.title}</h4>
                  <p className="text-xs text-slate-300 leading-relaxed font-sans">{insight.text}</p>
                </div>
              ))}
            </div>
          </div>

          {/* ======================================================== */}
          {/* SECTION 5: TOP RATED & COMMUNITY COMPARISON SHOWCASE     */}
          {/* ======================================================== */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Top-Rated Personal Favorites */}
            <div className="p-5 sm:p-6 rounded-3xl bg-[#0c0e1e] border border-purple-500/30 shadow-[0_0_30px_rgba(0,0,0,0.5)] space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-base sm:text-lg font-bold text-white flex items-center gap-2">
                  <Award className="w-5 h-5 text-amber-400" />
                  Your Highest-Rated Anime
                </h3>
                <span className="text-xs font-mono text-slate-400">Score 8+ Favorites</span>
              </div>

              {data.ratings.highest_rated.length > 0 ? (
                <div className="space-y-3">
                  {data.ratings.highest_rated.map((item) => (
                    <div
                      key={item.mal_id}
                      className="p-2.5 rounded-2xl bg-purple-950/20 border border-purple-500/20 flex items-center justify-between gap-3 hover:border-purple-400/50 transition-colors"
                    >
                      <div className="flex items-center gap-3">
                        <img
                          src={item.poster_url || '/placeholder-anime.jpg'}
                          alt={item.title}
                          className="w-10 h-14 object-cover rounded-xl"
                        />
                        <div>
                          <Link
                            to={`/anime/${item.mal_id}`}
                            className="text-xs sm:text-sm font-bold text-white hover:text-purple-300 transition-colors line-clamp-1"
                          >
                            {item.title}
                          </Link>
                          <span className="text-[10px] font-mono text-cyan-400">{item.status}</span>
                        </div>
                      </div>

                      <div className="px-3 py-1.5 rounded-xl bg-amber-950/40 border border-amber-400/40 text-amber-300 font-mono text-xs font-bold flex items-center gap-1 flex-shrink-0">
                        <Star className="w-3.5 h-3.5 fill-amber-400 text-amber-400" />
                        {item.rating}/10
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs font-mono text-slate-400">No rated anime recorded yet.</p>
              )}
            </div>

            {/* Community vs Personal Comparison */}
            <div className="p-5 sm:p-6 rounded-3xl bg-[#0c0e1e] border border-purple-500/30 shadow-[0_0_30px_rgba(0,0,0,0.5)] space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-base sm:text-lg font-bold text-white flex items-center gap-2">
                  <Flame className="w-5 h-5 text-cyan-400" />
                  Community vs Personal Score
                </h3>
                <span className="text-xs font-mono text-slate-400">Rating Divergence</span>
              </div>

              {data.ratings.community_comparison && data.ratings.community_comparison.top_divergences.length > 0 ? (
                <div className="space-y-3">
                  {data.ratings.community_comparison.top_divergences.map((item) => (
                    <div
                      key={item.mal_id}
                      className="p-2.5 rounded-2xl bg-purple-950/20 border border-purple-500/20 flex items-center justify-between gap-3"
                    >
                      <Link
                        to={`/anime/${item.mal_id}`}
                        className="text-xs sm:text-sm font-bold text-white hover:text-purple-300 transition-colors line-clamp-1 flex-1"
                      >
                        {item.title}
                      </Link>

                      <div className="flex items-center gap-3 font-mono text-xs flex-shrink-0">
                        <span className="text-amber-300 font-bold">{item.personal_rating}★</span>
                        <span className="text-slate-500">vs</span>
                        <span className="text-slate-300">{item.community_score} MAL</span>
                        <span
                          className={`px-2 py-0.5 rounded-lg text-[10px] font-bold ${
                            item.delta > 0
                              ? 'bg-emerald-950/60 text-emerald-300 border border-emerald-500/30'
                              : item.delta < 0
                              ? 'bg-rose-950/60 text-rose-300 border border-rose-500/30'
                              : 'bg-purple-950/60 text-purple-300'
                          }`}
                        >
                          {item.delta > 0 ? `+${item.delta}` : item.delta}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs font-mono text-slate-400">
                  Rate more anime to see community score comparisons.
                </p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default AnalyticsPage

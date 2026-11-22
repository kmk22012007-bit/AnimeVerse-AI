import React, { useState, useRef, useEffect, useCallback } from 'react'
import {
  Bot,
  Sparkles,
  Send,
  User,
  Loader2,
  RefreshCw,
  Compass,
  Star,
  ArrowRight,
  ShieldCheck,
  CheckCircle2,
  Flame,
  Info,
  SlidersHorizontal,
  Trash2,
  Zap,
  BookOpen,
  Layers,
} from 'lucide-react'
import { Link } from 'react-router-dom'
import {
  sendRyukMessage,
  getRyukRecommendations,
  clearRyukConversations,
} from '../api/ryuk'
import { AddToListButton } from '../components/watchlist/AddToListButton'
import { CardSkeleton } from '../components/common/LoadingSkeleton'
import ErrorState from '../components/common/ErrorState'
import EmptyState from '../components/common/EmptyState'

const PROMPT_CHIPS = [
  { label: 'Summarize my progress', icon: BookOpen, query: 'Summarize my progress' },
  { label: 'What should I watch next?', icon: Sparkles, query: 'Based on my completed anime, what should I watch next?' },
  { label: 'Recommend something different', icon: Compass, query: 'Help me discover something different from my usual preferences' },
  { label: 'Where to watch Demon Slayer?', icon: Zap, query: 'Where can I watch Demon Slayer with verified dubs?' },
  { label: 'Compare Death Note vs Code Geass', icon: Layers, query: 'Compare Death Note and Code Geass using verified metadata' },
]

export const RyukAssistantPage = () => {
  // Navigation tabs: 'recommendations' | 'chat'
  const [activeTab, setActiveTab] = useState('recommendations')

  // === Recommendations State ===
  const [recommendations, setRecommendations] = useState([])
  const [userProfileSummary, setUserProfileSummary] = useState(null)
  const [recLoading, setRecLoading] = useState(true)
  const [recError, setRecError] = useState(null)
  const [selectedGenre, setSelectedGenre] = useState('')
  const [recMode, setRecMode] = useState('personalized') // 'personalized' | 'different'
  const [isRefreshing, setIsRefreshing] = useState(false)

  // === Chat State ===
  const [messages, setMessages] = useState([
    {
      id: 'init',
      role: 'assistant',
      text: 'Greetings, human. I am RYUK, your cybernetic anime companion powered by Gemini AI and verified metadata registries.\n\nI can analyze your watchlist progress, compare verified anime records, look up confirmed dub languages, or craft tailored recommendations. What do you seek?',
      isFallback: false,
    },
  ])
  const [inputText, setInputText] = useState('')
  const [chatLoading, setChatLoading] = useState(false)
  const [conversationId, setConversationId] = useState(null)
  const messagesEndRef = useRef(null)

  // Load recommendations
  const fetchRecommendations = useCallback(async (genre = '', mode = 'personalized', refresh = false) => {
    if (refresh) setIsRefreshing(true)
    else setRecLoading(true)
    setRecError(null)

    try {
      const params = { limit: 8, mode }
      if (genre) params.genre = genre
      if (refresh) params.refresh = true

      const res = await getRyukRecommendations(params)
      setRecommendations(res?.recommendations || [])
      setUserProfileSummary(res?.user_profile_summary || null)
    } catch (err) {
      setRecError(err?.response?.data?.message || err.message || 'Unable to load personalized recommendations.')
    } finally {
      setRecLoading(false)
      setIsRefreshing(false)
    }
  }, [])

  useEffect(() => {
    fetchRecommendations(selectedGenre, recMode)
  }, [fetchRecommendations, selectedGenre, recMode])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    if (activeTab === 'chat') {
      scrollToBottom()
    }
  }, [messages, chatLoading, activeTab])

  // Handle Send Chat Message
  const handleSendMessage = async (textToSend) => {
    const query = (textToSend || inputText).trim()
    if (!query || chatLoading) return

    const userMsg = {
      id: Date.now().toString(),
      role: 'user',
      text: query,
    }

    setMessages((prev) => [...prev, userMsg])
    setInputText('')
    setChatLoading(true)

    try {
      const res = await sendRyukMessage(query, conversationId)
      if (res?.conversation_id) {
        setConversationId(res.conversation_id)
      }

      const botReply = res?.reply || 'I hear you, mortal. What else do you seek from the anime realm?'
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          text: botReply,
          isFallback: false,
        },
      ])
    } catch (err) {
      const errData = err.response?.data
      const fallbackMsg =
        errData?.message ||
        "I'm temporarily conserving power, human. Here are some verified trending anime suggestions instead."

      if (errData?.conversation_id) {
        setConversationId(errData.conversation_id)
      }

      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          text: fallbackMsg,
          isFallback: true,
          suggestions: errData?.suggestions || [],
        },
      ])
    } finally {
      setChatLoading(false)
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const handleClearChat = async () => {
    try {
      await clearRyukConversations()
    } catch {
      // Gracefully clear local state even if network fails
    }
    setMessages([
      {
        id: 'init-cleared',
        role: 'assistant',
        text: 'Neural memory purged. I am ready with a fresh slate. Ask me about your progress, streaming licenses, or recommendations.',
        isFallback: false,
      },
    ])
    setConversationId(null)
  }

  // Format assistant message text (bolding, lists, and linebreaks)
  const formatAssistantText = (text) => {
    if (!text) return ''
    const lines = text.split('\n')
    return lines.map((line, idx) => {
      // Render bullet items
      if (line.startsWith('• ') || line.startsWith('- ')) {
        const itemContent = line.slice(2)
        return (
          <li key={idx} className="ml-4 list-disc text-slate-200">
            {renderBoldText(itemContent)}
          </li>
        )
      }
      return (
        <p key={idx} className={line.trim() === '' ? 'h-2' : 'mb-1 text-slate-200'}>
          {renderBoldText(line)}
        </p>
      )
    })
  }

  const renderBoldText = (str) => {
    const parts = str.split(/(\*\*[^*]+\*\*)/g)
    return parts.map((part, i) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return (
          <strong key={i} className="font-bold text-white">
            {part.slice(2, -2)}
          </strong>
        )
      }
      return part
    })
  }

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Top Banner & Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-purple-500/20 pb-5">
        <div>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-purple-700 to-cyan-500 p-0.5 shadow-[0_0_20px_rgba(168,85,247,0.4)]">
              <div className="w-full h-full rounded-[14px] bg-[#0c0e1e] flex items-center justify-center">
                <Bot className="w-5 h-5 text-purple-300" />
              </div>
            </div>
            <div>
              <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-wide flex items-center gap-2.5">
                RYUK Intelligence Hub
              </h1>
              <p className="text-xs sm:text-sm text-slate-400 font-mono mt-0.5 flex items-center gap-2">
                <span className="inline-block w-2 h-2 rounded-full bg-cyan-400 animate-pulse"></span>
                Context-Aware Companion • Gemini AI • Verified Registry Grounding
              </p>
            </div>
          </div>
        </div>

        {/* Tab Navigation Pill Switcher */}
        <div className="flex items-center gap-1.5 p-1.5 rounded-2xl bg-[#0e1124] border border-purple-500/30 self-start sm:self-auto">
          <button
            onClick={() => setActiveTab('recommendations')}
            type="button"
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs sm:text-sm font-semibold transition-all duration-200 cursor-pointer ${
              activeTab === 'recommendations'
                ? 'bg-purple-600 text-white shadow-[0_0_15px_rgba(168,85,247,0.4)]'
                : 'text-slate-400 hover:text-slate-200 hover:bg-purple-950/40'
            }`}
          >
            <Compass className="w-4 h-4 text-cyan-300" />
            <span>AI Recommendations</span>
          </button>

          <button
            onClick={() => setActiveTab('chat')}
            type="button"
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs sm:text-sm font-semibold transition-all duration-200 cursor-pointer ${
              activeTab === 'chat'
                ? 'bg-purple-600 text-white shadow-[0_0_15px_rgba(168,85,247,0.4)]'
                : 'text-slate-400 hover:text-slate-200 hover:bg-purple-950/40'
            }`}
          >
            <Bot className="w-4 h-4 text-purple-300" />
            <span>Neural Chat</span>
          </button>
        </div>
      </div>

      {/* ======================================================== */}
      {/* VIEW 1: INTELLIGENT RECOMMENDATIONS TAB                 */}
      {/* ======================================================== */}
      {activeTab === 'recommendations' && (
        <div className="space-y-6">
          {/* User Taste Profile Header Card */}
          <div className="p-5 sm:p-6 rounded-3xl bg-gradient-to-r from-purple-950/40 via-[#0e1026] to-cyan-950/20 border border-purple-500/30 shadow-[0_0_30px_rgba(168,85,247,0.12)]">
            <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
              <div className="space-y-2.5">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold bg-cyan-500/20 text-cyan-300 border border-cyan-400/40 flex items-center gap-1">
                    <Sparkles className="w-3 h-3" /> HYBRID RECOMMENDATION ENGINE
                  </span>
                  <span className="px-2.5 py-0.5 rounded-full text-[10px] font-mono text-purple-300 bg-purple-900/40 border border-purple-500/30 flex items-center gap-1">
                    <ShieldCheck className="w-3 h-3 text-emerald-400" /> Verified Metadata
                  </span>
                  <span className="px-2.5 py-0.5 rounded-full text-[10px] font-mono text-amber-300 bg-amber-950/40 border border-amber-500/30">
                    Mode: {recMode === 'different' ? 'Exploratory Discovery' : 'Personalized Affinity'}
                  </span>
                </div>

                <h2 className="text-lg sm:text-xl font-bold text-white tracking-wide">
                  {recMode === 'different'
                    ? 'Serendipitous Discovery — Beyond Your Comfort Zone'
                    : userProfileSummary?.has_watch_history
                    ? 'Curated For Your Anime Journey'
                    : 'Essential Gateway Masterpieces'}
                </h2>

                <p className="text-xs sm:text-sm text-slate-300 max-w-3xl leading-relaxed">
                  {recMode === 'different' ? (
                    <>
                      RYUK selected critically acclaimed gems from genres outside your usual rotation to expand your storytelling horizons.
                    </>
                  ) : userProfileSummary?.has_watch_history ? (
                    <>
                      Calibrated from your{' '}
                      <span className="text-cyan-300 font-semibold">{userProfileSummary.total_tracked} tracked titles</span>{' '}
                      ({userProfileSummary.completed_count} completed, {userProfileSummary.watching_count} watching) and top-rated favorites:{' '}
                      <span className="text-purple-300 font-mono">
                        {userProfileSummary.top_rated_titles?.slice(0, 3).join(', ') || 'Various favorites'}
                      </span>.
                    </>
                  ) : (
                    <>
                      You haven't logged anime in your personal watchlist yet. RYUK has calibrated a selection of celebrated gateway anime to jump-start your taste profile.
                    </>
                  )}
                </p>

                {/* Genre & Studio Affinity Tags */}
                <div className="flex items-center gap-3 pt-1 flex-wrap">
                  {userProfileSummary?.favorite_genres && userProfileSummary.favorite_genres.length > 0 && (
                    <div className="flex items-center gap-1.5 flex-wrap">
                      <span className="text-[11px] font-mono text-slate-400">Top Genres:</span>
                      {userProfileSummary.favorite_genres.slice(0, 4).map((g) => (
                        <span
                          key={g}
                          className="px-2 py-0.5 rounded-lg bg-purple-900/40 border border-purple-500/30 text-xs font-medium text-purple-200"
                        >
                          {g}
                        </span>
                      ))}
                    </div>
                  )}

                  {userProfileSummary?.favorite_studios && userProfileSummary.favorite_studios.length > 0 && (
                    <div className="flex items-center gap-1.5 flex-wrap">
                      <span className="text-[11px] font-mono text-slate-400">Fav Studios:</span>
                      {userProfileSummary.favorite_studios.slice(0, 2).map((s) => (
                        <span
                          key={s}
                          className="px-2 py-0.5 rounded-lg bg-cyan-950/40 border border-cyan-500/30 text-xs font-medium text-cyan-200"
                        >
                          {s}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>

              {/* Mode Toggle & Refresh Actions */}
              <div className="flex flex-col sm:flex-row lg:flex-col items-start lg:items-end gap-2.5">
                <div className="flex items-center gap-1 p-1 rounded-xl bg-purple-950/60 border border-purple-500/30">
                  <button
                    onClick={() => {
                      setRecMode('personalized')
                      setSelectedGenre('')
                    }}
                    type="button"
                    className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                      recMode === 'personalized'
                        ? 'bg-purple-600 text-white shadow-sm'
                        : 'text-slate-400 hover:text-white'
                    }`}
                  >
                    Personalized
                  </button>
                  <button
                    onClick={() => {
                      setRecMode('different')
                      setSelectedGenre('')
                    }}
                    type="button"
                    className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                      recMode === 'different'
                        ? 'bg-cyan-600 text-white shadow-sm'
                        : 'text-slate-400 hover:text-white'
                    }`}
                  >
                    Something Different
                  </button>
                </div>

                <button
                  onClick={() => fetchRecommendations(selectedGenre, recMode, true)}
                  disabled={recLoading || isRefreshing}
                  type="button"
                  className="px-4 py-2 rounded-xl bg-purple-900/40 hover:bg-purple-800/60 border border-purple-500/40 text-xs font-semibold text-purple-200 transition-all flex items-center gap-2 shadow-sm disabled:opacity-50 cursor-pointer"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin text-cyan-400' : ''}`} />
                  <span>{isRefreshing ? 'Recalibrating...' : 'Refresh Suggestions'}</span>
                </button>
              </div>
            </div>
          </div>

          {/* Genre Focus Filter Strip */}
          {userProfileSummary?.favorite_genres && userProfileSummary.favorite_genres.length > 0 && recMode === 'personalized' && (
            <div className="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-none">
              <span className="text-xs font-mono text-slate-400 whitespace-nowrap flex items-center gap-1.5">
                <SlidersHorizontal className="w-3.5 h-3.5 text-purple-400" /> Focus Genre:
              </span>
              <button
                onClick={() => setSelectedGenre('')}
                type="button"
                className={`px-3 py-1 rounded-xl text-xs font-medium transition-colors whitespace-nowrap cursor-pointer ${
                  selectedGenre === ''
                    ? 'bg-purple-600 text-white font-bold'
                    : 'bg-[#0f1226] text-slate-400 hover:text-white border border-purple-500/20'
                }`}
              >
                All Recommendations
              </button>
              {userProfileSummary.favorite_genres.map((g) => (
                <button
                  key={g}
                  onClick={() => setSelectedGenre(g)}
                  type="button"
                  className={`px-3 py-1 rounded-xl text-xs font-medium transition-colors whitespace-nowrap cursor-pointer ${
                    selectedGenre === g
                      ? 'bg-purple-600 text-white font-bold'
                      : 'bg-[#0f1226] text-slate-400 hover:text-white border border-purple-500/20'
                  }`}
                >
                  {g}
                </button>
              ))}
            </div>
          )}

          {/* Error View */}
          {recError && (
            <ErrorState
              title="Recommendation Calibration Error"
              message={recError}
              onRetry={() => fetchRecommendations(selectedGenre, recMode, true)}
            />
          )}

          {/* Loading Skeletons */}
          {recLoading && !isRefreshing && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
              {[...Array(8)].map((_, i) => (
                <CardSkeleton key={i} />
              ))}
            </div>
          )}

          {/* Empty State */}
          {!recLoading && !recError && recommendations.length === 0 && (
            <EmptyState
              title="No Recommendations Found"
              message="RYUK could not find matching titles for this specific filter. Try resetting your genre selection or adding more anime to your watchlist."
              actionLabel="Reset Filter"
              onAction={() => setSelectedGenre('')}
            />
          )}

          {/* Recommendations Cards Grid */}
          {!recLoading && recommendations.length > 0 && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
              {recommendations.map((item) => (
                <div
                  key={item.mal_id}
                  className="rounded-3xl bg-[#0c0e1e] border border-purple-500/25 hover:border-purple-400/60 overflow-hidden flex flex-col shadow-[0_0_20px_rgba(0,0,0,0.5)] hover:shadow-[0_0_30px_rgba(168,85,247,0.22)] transition-all duration-300 group"
                >
                  {/* Poster Thumbnail & Floating Badges */}
                  <div className="relative aspect-[16/10] sm:aspect-[4/3] w-full overflow-hidden bg-purple-950/40">
                    <img
                      src={item.poster_url || '/placeholder-anime.jpg'}
                      alt={item.title}
                      loading="lazy"
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-[#0c0e1e] via-transparent to-black/50" />

                    {/* Top Badges: Confidence Tier & Score */}
                    <div className="absolute top-2.5 left-2.5 flex items-center gap-1.5">
                      <span className="px-2.5 py-1 rounded-xl bg-cyan-950/80 backdrop-blur-md border border-cyan-400/50 text-cyan-300 font-mono text-[11px] font-bold flex items-center gap-1 shadow-[0_0_10px_rgba(6,182,212,0.4)]">
                        <Flame className="w-3 h-3 text-cyan-400" />
                        {item.confidence_tier || `${item.match_percentage}% Match`}
                      </span>
                    </div>

                    <div className="absolute top-2.5 right-2.5">
                      {item.score && (
                        <span className="px-2 py-1 rounded-xl bg-black/70 backdrop-blur-md border border-amber-400/40 text-amber-300 font-mono text-[11px] font-semibold flex items-center gap-1">
                          <Star className="w-3 h-3 fill-amber-400 text-amber-400" />
                          {Number(item.score).toFixed(1)}
                        </span>
                      )}
                    </div>

                    {/* Format / Episodes / Studio Pill */}
                    <div className="absolute bottom-2.5 left-2.5 flex items-center gap-1">
                      <span className="px-2 py-0.5 rounded-lg bg-purple-950/80 backdrop-blur-md border border-purple-500/40 text-purple-200 text-[10px] font-mono">
                        {item.anime_type || 'TV'} {item.total_episodes ? `• ${item.total_episodes} eps` : ''}
                      </span>
                      {item.studios && item.studios.length > 0 && (
                        <span className="px-2 py-0.5 rounded-lg bg-black/60 backdrop-blur-md border border-slate-700 text-slate-300 text-[10px] font-mono">
                          {item.studios[0]}
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Card Content */}
                  <div className="p-4 flex-1 flex flex-col justify-between space-y-3.5">
                    <div>
                      {/* Title */}
                      <Link
                        to={`/anime/${item.mal_id}`}
                        className="text-sm font-bold text-white hover:text-purple-300 line-clamp-1 transition-colors tracking-tight block"
                        title={item.title}
                      >
                        {item.title}
                      </Link>

                      {/* Genre Tags */}
                      {item.genres && item.genres.length > 0 && (
                        <div className="flex flex-wrap gap-1 mt-1.5">
                          {item.genres.slice(0, 3).map((g) => (
                            <span
                              key={g}
                              className="px-1.5 py-0.5 rounded-md bg-purple-950/50 text-purple-300 text-[10px] font-mono"
                            >
                              {g}
                            </span>
                          ))}
                        </div>
                      )}

                      {/* RYUK Rationale Callout Box */}
                      <div className="mt-3 p-3 rounded-2xl bg-purple-950/30 border border-purple-500/30 relative">
                        <div className="flex items-center justify-between mb-1.5">
                          <span className="text-[10px] font-mono font-bold text-purple-300 flex items-center gap-1">
                            <Bot className="w-3 h-3 text-purple-400" /> RYUK's Verdict:
                          </span>
                          <span className="text-[9px] font-mono px-1.5 py-0.2 rounded bg-purple-900/60 text-purple-300">
                            {item.is_ai_rationale ? 'AI Insight' : 'Curated'}
                          </span>
                        </div>
                        <p className="text-[11px] text-slate-300 leading-relaxed italic">
                          "{item.why_recommended}"
                        </p>
                      </div>

                      {/* Matched Reasons Chips */}
                      {item.matched_reasons && item.matched_reasons.length > 0 && (
                        <div className="mt-2 space-y-1">
                          {item.matched_reasons.slice(0, 2).map((reason, idx) => (
                            <div key={idx} className="flex items-center gap-1.5 text-[10px] text-slate-400 font-mono">
                              <CheckCircle2 className="w-3 h-3 text-cyan-400 flex-shrink-0" />
                              <span className="line-clamp-1">{reason}</span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>

                    {/* Card Actions: Watchlist & Details */}
                    <div className="pt-2 border-t border-purple-500/15 flex items-center justify-between gap-2">
                      <Link
                        to={`/anime/${item.mal_id}`}
                        className="inline-flex items-center gap-1 text-xs font-semibold text-purple-300 hover:text-white transition-colors"
                      >
                        <span>Details</span>
                        <ArrowRight className="w-3 h-3" />
                      </Link>

                      <AddToListButton malId={item.mal_id} compact={false} />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ======================================================== */}
      {/* VIEW 2: CONVERSATIONAL NEURAL CHAT TERMINAL              */}
      {/* ======================================================== */}
      {activeTab === 'chat' && (
        <div className="space-y-4">
          {/* Main Terminal Container */}
          <div className="rounded-3xl bg-[#0c0e1e] border border-purple-500/30 overflow-hidden shadow-[0_0_35px_rgba(168,85,247,0.18)] flex flex-col h-[620px]">
            {/* Terminal Header */}
            <div className="p-4 border-b border-purple-500/20 bg-purple-950/40 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-xl bg-purple-600 border border-purple-400 flex items-center justify-center text-white shadow-[0_0_10px_rgba(168,85,247,0.5)]">
                  <Bot className="w-4 h-4" />
                </div>
                <div>
                  <div className="text-sm font-bold text-white flex items-center gap-2">
                    RYUK <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-cyan-500/20 text-cyan-300 border border-cyan-400/40">ONLINE</span>
                  </div>
                  <div className="text-[11px] text-slate-400 font-mono">
                    Context-Aware Companion • Grounded in Database Records
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={() => setActiveTab('recommendations')}
                  type="button"
                  className="inline-flex items-center gap-1.5 px-3 py-1 rounded-xl bg-cyan-950/40 hover:bg-cyan-900/60 border border-cyan-500/30 text-xs font-mono text-cyan-300 transition-colors cursor-pointer"
                >
                  <Compass className="w-3 h-3" />
                  <span className="hidden sm:inline">Recommendation Hub</span>
                </button>

                <button
                  onClick={handleClearChat}
                  type="button"
                  className="inline-flex items-center gap-1.5 px-3 py-1 rounded-xl bg-purple-900/30 hover:bg-rose-950/50 border border-purple-500/20 hover:border-rose-500/40 text-xs font-mono text-purple-300 hover:text-rose-300 transition-colors cursor-pointer"
                  title="Purge dialogue memory"
                >
                  <Trash2 className="w-3 h-3" />
                  <span>Clear History</span>
                </button>
              </div>
            </div>

            {/* Message Thread */}
            <div className="flex-1 p-4 sm:p-6 space-y-4 overflow-y-auto">
              {messages.map((m) => {
                const isUser = m.role === 'user'
                return (
                  <div
                    key={m.id}
                    className={`flex items-start gap-3 max-w-2xl ${
                      isUser ? 'ml-auto flex-row-reverse' : ''
                    }`}
                  >
                    <div
                      className={`w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0 text-white ${
                        isUser
                          ? 'bg-gradient-to-tr from-purple-600 to-indigo-600 border border-purple-400 shadow-[0_0_12px_rgba(168,85,247,0.4)]'
                          : 'bg-[#131627] border border-purple-500/40 text-purple-300 shadow-[0_0_12px_rgba(168,85,247,0.25)]'
                      }`}
                    >
                      {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4 text-cyan-300" />}
                    </div>

                    <div
                      className={`p-4 rounded-2xl text-xs sm:text-sm leading-relaxed ${
                        isUser
                          ? 'bg-gradient-to-r from-purple-600 to-indigo-600 text-white font-medium rounded-tr-sm shadow-[0_4px_16px_rgba(168,85,247,0.35)]'
                          : 'bg-[#0e101d]/95 border border-purple-500/25 text-slate-100 rounded-tl-sm shadow-[0_4px_20px_rgba(0,0,0,0.5)] backdrop-blur-md'
                      }`}
                    >
                      {isUser ? (
                        <p className="whitespace-pre-wrap">{m.text}</p>
                      ) : (
                        <div className="space-y-1">
                          {formatAssistantText(m.text)}
                        </div>
                      )}

                      {/* Fallback suggestion pills */}
                      {m.suggestions && m.suggestions.length > 0 && (
                        <div className="mt-3 pt-2 border-t border-purple-500/20 flex flex-wrap gap-2">
                          {m.suggestions.map((s, idx) => (
                            <span
                              key={idx}
                              className="px-2.5 py-1 rounded-lg bg-purple-950/60 border border-purple-500/30 text-purple-300 text-xs font-mono"
                            >
                              {s.title || s}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                )
              })}

              {chatLoading && (
                <div className="flex items-start gap-3 max-w-lg">
                  <div className="w-9 h-9 rounded-xl bg-[#131627] border border-purple-500/40 flex items-center justify-center flex-shrink-0 text-cyan-300 shadow-[0_0_12px_rgba(6,182,212,0.3)]">
                    <Bot className="w-4 h-4" />
                  </div>
                  <div className="p-3.5 rounded-2xl bg-[#0e101d]/95 border border-purple-500/25 text-xs text-purple-300 flex items-center gap-2 font-mono shadow-sm">
                    <Loader2 className="w-3.5 h-3.5 animate-spin text-purple-400" />
                    <span>RYUK is cross-referencing your profile and verified registries...</span>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>

            {/* Grounded Prompt Chips */}
            <div className="px-4 py-2 border-t border-purple-950/80 bg-purple-950/20 flex items-center gap-2 overflow-x-auto scrollbar-none text-xs">
              <span className="text-slate-400 font-mono text-[11px] whitespace-nowrap flex items-center gap-1">
                <Sparkles className="w-3 h-3 text-cyan-400" /> Grounded Prompts:
              </span>
              {PROMPT_CHIPS.map((chip, idx) => {
                const IconComponent = chip.icon
                return (
                  <button
                    key={idx}
                    onClick={() => handleSendMessage(chip.query)}
                    disabled={chatLoading}
                    type="button"
                    className="px-2.5 py-1 rounded-lg bg-purple-950/40 hover:bg-purple-900/60 border border-purple-500/20 text-purple-300 hover:text-white text-[11px] whitespace-nowrap transition-colors cursor-pointer disabled:opacity-40 flex items-center gap-1.5 active:scale-95"
                  >
                    <IconComponent className="w-3 h-3 text-purple-400" />
                    <span>{chip.label}</span>
                  </button>
                )
              })}
            </div>

            {/* Input Bar */}
            <div className="p-4 border-t border-purple-500/20 bg-purple-950/30">
              <div className="flex gap-3">
                <input
                  type="text"
                  value={inputText}
                  onChange={(e) => setInputText(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Ask RYUK about your progress, streaming availability, or recommendations..."
                  aria-label="RYUK message input"
                  disabled={chatLoading}
                  className="flex-1 px-4 py-2.5 rounded-xl bg-[#080911] border border-purple-500/30 text-xs sm:text-sm text-slate-100 placeholder:text-slate-500 focus:outline-none focus:border-purple-400 transition-colors"
                />
                <button
                  onClick={() => handleSendMessage()}
                  disabled={!inputText.trim() || chatLoading}
                  type="button"
                  aria-label="Send message to RYUK"
                  className="px-5 py-2.5 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-medium text-xs sm:text-sm transition-all shadow-[0_0_15px_rgba(168,85,247,0.4)] flex items-center gap-2 disabled:opacity-40 cursor-pointer active:scale-95"
                >
                  {chatLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                  <span>Send</span>
                </button>
              </div>
              <div className="flex items-center justify-between mt-2 px-1 text-[10px] font-mono text-slate-500">
                <span>Press Enter to send • Shift+Enter for newline</span>
                <span>Powered by Gemini AI</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default RyukAssistantPage

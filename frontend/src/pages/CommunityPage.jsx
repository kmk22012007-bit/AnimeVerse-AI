import React, { useState, useEffect } from 'react'
import { useSearchParams, Link } from 'react-router-dom'
import {
  MessageSquare,
  Heart,
  MessageCircle,
  Plus,
  Send,
  Loader2,
  User,
  Clock,
  Sparkles,
  ChevronDown,
  ChevronUp,
  X,
  AlertTriangle,
  Eye,
  EyeOff,
  Flame,
  TrendingUp,
  Award,
  Vote,
  Flag,
  Shield,
  ShieldAlert,
  CheckCircle,
  Search,
  Filter,
  Tag,
  Film,
  Trash2,
  CornerDownRight,
  UserCheck,
} from 'lucide-react'
import {
  getCommunityPosts,
  createCommunityPost,
  getCommunityPostDetail,
  likeCommunityPost,
  unlikeCommunityPost,
  addCommentToPost,
  deleteCommunityPost,
  deleteComment,
  votePoll,
  submitCommunityReport,
  getModerationReports,
  actionModerationReport,
} from '../api/community'
import { getCurrentProfile } from '../api/profile'

const CATEGORIES = [
  { id: 'all', label: 'All Topics' },
  { id: 'discussion', label: '💬 Discussion' },
  { id: 'theory', label: '🔮 Theory' },
  { id: 'review', label: '⭐ Review' },
  { id: 'question', label: '❓ Question' },
  { id: 'news', label: '📰 News' },
  { id: 'fan_art', label: '🎨 Fan Art' },
  { id: 'recommendation', label: '🎯 Recommendation' },
]

const SORT_OPTIONS = [
  { id: 'latest', label: 'Latest', icon: Clock },
  { id: 'following', label: 'Following', icon: UserCheck },
  { id: 'trending', label: 'Trending', icon: Flame },
  { id: 'popular', label: 'Most Liked', icon: Heart },
  { id: 'discussed', label: 'Most Discussed', icon: MessageCircle },
]

const GENRE_FILTERS = [
  'All',
  'Action',
  'Adventure',
  'Comedy',
  'Drama',
  'Fantasy',
  'Horror',
  'Mystery',
  'Romance',
  'Sci-Fi',
  'Shounen',
  'Slice of Life',
  'Supernatural',
]

const TAG_SUGGESTIONS = [
  'Theory',
  'Discussion',
  'Review',
  'Season 1',
  'Manga',
  'Spoilers',
  'Anime vs Manga',
  'Plot Twist',
]

export const CommunityPage = () => {
  const [searchParams, setSearchParams] = useSearchParams()
  const animeIdParam = searchParams.get('anime_id')

  // User State
  const [currentUser, setCurrentUser] = useState(null)
  const [activeTab, setActiveTab] = useState('feed') // 'feed' | 'moderation'

  // Feed State
  const [posts, setPosts] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [page, setPage] = useState(1)
  const [pagination, setPagination] = useState({ page: 1, total_pages: 1, total: 0 })

  // Filters State
  const [sortMode, setSortMode] = useState('latest')
  const [selectedCategory, setSelectedCategory] = useState('all')
  const [selectedGenre, setSelectedGenre] = useState('All')
  const [selectedFilter, setSelectedFilter] = useState('all') // 'all' | 'has_poll' | 'is_spoiler'
  const [searchQuery, setSearchQuery] = useState('')
  const [revealedSpoilers, setRevealedSpoilers] = useState({}) // { [postId or commentId]: boolean }

  // Create Post Modal State
  const [createModalOpen, setCreateModalOpen] = useState(false)
  const [newTitle, setNewTitle] = useState('')
  const [newBody, setNewBody] = useState('')
  const [newCategory, setNewCategory] = useState('discussion')
  const [newAnimeId, setNewAnimeId] = useState(animeIdParam || '')
  const [newTags, setNewTags] = useState([])
  const [tagInput, setTagInput] = useState('')
  const [newIsSpoiler, setNewIsSpoiler] = useState(false)
  const [hasPoll, setHasPoll] = useState(false)
  const [pollQuestion, setPollQuestion] = useState('')
  const [pollOptions, setPollOptions] = useState(['', ''])
  const [pollExpiresDays, setPollExpiresDays] = useState(7)
  const [creating, setCreating] = useState(false)
  const [createError, setCreateError] = useState(null)

  // Comments & Interaction State
  const [commentsState, setCommentsState] = useState({}) // { [postId]: { comments: [], loading: boolean, open: boolean } }
  const [commentInputs, setCommentInputs] = useState({})
  const [commentSpoilerFlags, setCommentSpoilerFlags] = useState({})
  const [replyInputs, setReplyInputs] = useState({}) // { [commentId]: string }
  const [replySpoilerFlags, setReplySpoilerFlags] = useState({})
  const [activeReplyId, setActiveReplyId] = useState(null)
  const [submittingComment, setSubmittingComment] = useState({})
  const [votingPollId, setVotingPollId] = useState(null)

  // Report Modal State
  const [reportModalOpen, setReportModalOpen] = useState(false)
  const [reportingTarget, setReportingTarget] = useState(null) // { type, id, title }
  const [reportReason, setReportReason] = useState('inappropriate')
  const [reportExplanation, setReportExplanation] = useState('')
  const [submittingReport, setSubmittingReport] = useState(false)
  const [reportFeedback, setReportFeedback] = useState(null)

  // Moderation State
  const [moderationReports, setModerationReports] = useState([])
  const [moderationLoading, setModerationLoading] = useState(false)
  const [moderationStatusFilter, setModerationStatusFilter] = useState('pending')
  const [actioningReportId, setActioningReportId] = useState(null)

  // Fetch Current User Profile
  useEffect(() => {
    const fetchUser = async () => {
      try {
        const res = await getCurrentProfile()
        setCurrentUser(res)
      } catch (err) {
        console.error('Failed to load user profile:', err)
      }
    }
    fetchUser()
  }, [])

  // Fetch Feed Posts
  const fetchPosts = async (targetPage = 1) => {
    setLoading(true)
    setError(null)
    try {
      const params = {
        page: targetPage,
        sort: sortMode,
        category: selectedCategory !== 'all' ? selectedCategory : undefined,
        genre: selectedGenre !== 'All' ? selectedGenre : undefined,
        filter: selectedFilter !== 'all' ? selectedFilter : undefined,
        anime_id: animeIdParam ? parseInt(animeIdParam, 10) : undefined,
        search: searchQuery.trim() || undefined,
      }
      const res = await getCommunityPosts(params)
      setPosts(res?.results || [])
      setPagination(res?.pagination || { page: targetPage, total_pages: 1, total: res?.results?.length || 0 })
    } catch (err) {
      setError('Unable to load community discussions.')
      setPosts([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (activeTab === 'feed') {
      fetchPosts(page)
    }
  }, [page, sortMode, selectedCategory, selectedGenre, selectedFilter, animeIdParam, activeTab])

  // Fetch Moderation Reports
  const fetchModeration = async () => {
    if (!currentUser?.is_moderator) return
    setModerationLoading(true)
    try {
      const res = await getModerationReports({ status: moderationStatusFilter })
      setModerationReports(res?.results || [])
    } catch (err) {
      console.error('Failed to load moderation reports:', err)
    } finally {
      setModerationLoading(false)
    }
  }

  useEffect(() => {
    if (activeTab === 'moderation') {
      fetchModeration()
    }
  }, [activeTab, moderationStatusFilter])

  // Search Handler
  const handleSearchSubmit = (e) => {
    e.preventDefault()
    setPage(1)
    fetchPosts(1)
  }

  // Clear Search
  const handleClearSearch = () => {
    setSearchQuery('')
    setPage(1)
    // Directly fetch with empty search
    getCommunityPosts({
      page: 1,
      sort: sortMode,
      category: selectedCategory !== 'all' ? selectedCategory : undefined,
      genre: selectedGenre !== 'All' ? selectedGenre : undefined,
      filter: selectedFilter !== 'all' ? selectedFilter : undefined,
      anime_id: animeIdParam ? parseInt(animeIdParam, 10) : undefined,
    }).then((res) => {
      setPosts(res?.results || [])
      setPagination(res?.pagination || { page: 1, total_pages: 1, total: 0 })
    })
  }

  // Spoiler Reveal Toggle
  const toggleSpoilerReveal = (id) => {
    setRevealedSpoilers((prev) => ({
      ...prev,
      [id]: !prev[id],
    }))
  }

  // Create Post Handler
  const handleCreatePost = async (e) => {
    e.preventDefault()
    if (!newTitle.trim() || !newBody.trim()) {
      setCreateError('Please provide both a title and post body.')
      return
    }

    let pollPayload = null
    if (hasPoll) {
      const validOptions = pollOptions.map((o) => o.trim()).filter(Boolean)
      if (!pollQuestion.trim() || validOptions.length < 2) {
        setCreateError('Polls require a question and at least 2 valid answer options.')
        return
      }
      pollPayload = {
        question: pollQuestion.trim(),
        options: validOptions,
        expires_days: pollExpiresDays,
      }
    }

    setCreating(true)
    setCreateError(null)

    try {
      const payload = {
        title: newTitle.trim(),
        body: newBody.trim(),
        category: newCategory,
        tags: newTags,
        is_spoiler: newIsSpoiler,
        anime_id: newAnimeId ? parseInt(newAnimeId, 10) : undefined,
        poll: pollPayload,
      }
      const created = await createCommunityPost(payload)
      setPosts((prev) => [created, ...prev])
      // Reset form
      setNewTitle('')
      setNewBody('')
      setNewCategory('discussion')
      setNewTags([])
      setNewIsSpoiler(false)
      setHasPoll(false)
      setPollQuestion('')
      setPollOptions(['', ''])
      setCreateModalOpen(false)
    } catch (err) {
      setCreateError(err.response?.data?.message || 'Failed to publish post.')
    } finally {
      setCreating(false)
    }
  }

  // Like / Unlike Toggle
  const handleToggleLike = async (postId, currentlyLiked) => {
    setPosts((prev) =>
      prev.map((p) => {
        if (p.id === postId) {
          return {
            ...p,
            liked_by_me: !currentlyLiked,
            like_count: currentlyLiked ? Math.max(0, p.like_count - 1) : p.like_count + 1,
          }
        }
        return p
      })
    )

    try {
      if (currentlyLiked) {
        await unlikeCommunityPost(postId)
      } else {
        await likeCommunityPost(postId)
      }
    } catch (err) {
      fetchPosts(page)
    }
  }

  // Poll Vote Handler
  const handlePollVote = async (pollId, optionId, postId) => {
    setVotingPollId(pollId)
    try {
      const res = await votePoll(pollId, optionId)
      // Update post poll state
      setPosts((prev) =>
        prev.map((p) => {
          if (p.id === postId) {
            return {
              ...p,
              poll: res,
            }
          }
          return p
        })
      )
    } catch (err) {
      alert(err.response?.data?.message || 'Failed to submit vote.')
    } finally {
      setVotingPollId(null)
    }
  }

  // Comments Expand/Collapse
  const handleToggleComments = async (postId) => {
    const currentState = commentsState[postId]
    if (currentState?.open) {
      setCommentsState((prev) => ({
        ...prev,
        [postId]: { ...prev[postId], open: false },
      }))
      return
    }

    setCommentsState((prev) => ({
      ...prev,
      [postId]: { comments: prev[postId]?.comments || [], loading: true, open: true },
    }))

    try {
      const detail = await getCommunityPostDetail(postId)
      setCommentsState((prev) => ({
        ...prev,
        [postId]: { comments: detail?.comments || [], loading: false, open: true },
      }))
    } catch (err) {
      setCommentsState((prev) => ({
        ...prev,
        [postId]: { comments: [], loading: false, open: true },
      }))
    }
  }

  // Submit Root Comment
  const handleAddComment = async (postId) => {
    const body = (commentInputs[postId] || '').trim()
    if (!body) return

    const isSpoiler = !!commentSpoilerFlags[postId]
    setSubmittingComment((prev) => ({ ...prev, [postId]: true }))

    try {
      const newComment = await addCommentToPost(postId, {
        body,
        is_spoiler: isSpoiler,
      })

      setCommentsState((prev) => {
        const cur = prev[postId]?.comments || []
        return {
          ...prev,
          [postId]: {
            ...prev[postId],
            comments: [...cur, { ...newComment, replies: [] }],
          },
        }
      })

      setCommentInputs((prev) => ({ ...prev, [postId]: '' }))
      setCommentSpoilerFlags((prev) => ({ ...prev, [postId]: false }))

      setPosts((prev) =>
        prev.map((p) => (p.id === postId ? { ...p, comment_count: p.comment_count + 1 } : p))
      )
    } catch (err) {
      alert(err.response?.data?.message || 'Failed to post comment.')
    } finally {
      setSubmittingComment((prev) => ({ ...prev, [postId]: false }))
    }
  }

  // Submit Nested Reply
  const handleAddReply = async (postId, parentCommentId) => {
    const body = (replyInputs[parentCommentId] || '').trim()
    if (!body) return

    const isSpoiler = !!replySpoilerFlags[parentCommentId]
    setSubmittingComment((prev) => ({ ...prev, [parentCommentId]: true }))

    try {
      const reply = await addCommentToPost(postId, {
        body,
        parent_id: parentCommentId,
        is_spoiler: isSpoiler,
      })

      // Insert reply into nested comments
      setCommentsState((prev) => {
        const cur = prev[postId]?.comments || []
        const updated = cur.map((c) => {
          if (c.id === parentCommentId) {
            return {
              ...c,
              replies: [...(c.replies || []), reply],
            }
          }
          return c
        })
        return {
          ...prev,
          [postId]: {
            ...prev[postId],
            comments: updated,
          },
        }
      })

      setReplyInputs((prev) => ({ ...prev, [parentCommentId]: '' }))
      setReplySpoilerFlags((prev) => ({ ...prev, [parentCommentId]: false }))
      setActiveReplyId(null)

      setPosts((prev) =>
        prev.map((p) => (p.id === postId ? { ...p, comment_count: p.comment_count + 1 } : p))
      )
    } catch (err) {
      alert(err.response?.data?.message || 'Failed to post reply.')
    } finally {
      setSubmittingComment((prev) => ({ ...prev, [parentCommentId]: false }))
    }
  }

  // Delete Post Handler
  const handleDeletePost = async (postId) => {
    if (!window.confirm('Are you sure you want to delete this post?')) return
    try {
      await deleteCommunityPost(postId)
      setPosts((prev) => prev.filter((p) => p.id !== postId))
    } catch (err) {
      alert(err.response?.data?.message || 'Failed to delete post.')
    }
  }

  // Delete Comment Handler
  const handleDeleteComment = async (postId, commentId) => {
    if (!window.confirm('Delete this comment?')) return
    try {
      await deleteComment(commentId)
      setCommentsState((prev) => {
        const cur = prev[postId]?.comments || []
        // Remove from root or replies
        const updated = cur
          .filter((c) => c.id !== commentId)
          .map((c) => ({
            ...c,
            replies: (c.replies || []).filter((r) => r.id !== commentId),
          }))
        return {
          ...prev,
          [postId]: { ...prev[postId], comments: updated },
        }
      })
      setPosts((prev) =>
        prev.map((p) => (p.id === postId ? { ...p, comment_count: Math.max(0, p.comment_count - 1) } : p))
      )
    } catch (err) {
      alert(err.response?.data?.message || 'Failed to delete comment.')
    }
  }

  // Open Report Modal
  const openReportModal = (type, id, title) => {
    setReportingTarget({ type, id, title })
    setReportReason('inappropriate')
    setReportExplanation('')
    setReportFeedback(null)
    setReportModalOpen(true)
  }

  // Submit Report Handler
  const handleSubmitReport = async (e) => {
    e.preventDefault()
    if (!reportingTarget) return

    setSubmittingReport(true)
    setReportFeedback(null)
    try {
      await submitCommunityReport({
        target_type: reportingTarget.type,
        target_id: reportingTarget.id,
        reason: reportReason,
        explanation: reportExplanation.trim(),
      })
      setReportFeedback({
        type: 'success',
        message: 'Thank you. Your report has been submitted for moderation review.',
      })
      setTimeout(() => {
        setReportModalOpen(false)
        setReportingTarget(null)
      }, 1500)
    } catch (err) {
      setReportFeedback({
        type: 'error',
        message: err.response?.data?.message || 'Failed to submit report.',
      })
    } finally {
      setSubmittingReport(false)
    }
  }

  // Action Moderation Report Handler
  const handleActionReport = async (reportId, actionTaken, statusVal = 'resolved') => {
    setActioningReportId(reportId)
    try {
      await actionModerationReport(reportId, {
        status: statusVal,
        action_taken: actionTaken,
        moderator_notes: `Actioned as ${actionTaken}`,
      })
      // Refresh moderation reports
      fetchModeration()
    } catch (err) {
      alert(err.response?.data?.message || 'Failed to action report.')
    } finally {
      setActioningReportId(null)
    }
  }

  return (
    <div className="min-h-screen bg-[#07070d] text-slate-100 pb-20">
      {/* 1. Header Banner */}
      <div className="relative border-b border-purple-900/30 bg-gradient-to-b from-purple-950/20 to-transparent py-10 px-4 sm:px-6 lg:px-8">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
          <div>
            <div className="flex items-center gap-3">
              <span className="p-2.5 rounded-xl bg-purple-500/10 border border-purple-500/30 text-purple-400">
                <MessageSquare className="w-6 h-6" />
              </span>
              <div>
                <h1 className="text-3xl font-extrabold tracking-tight text-white flex items-center gap-2">
                  AnimeVerse <span className="text-purple-400">Community</span>
                </h1>
                <p className="text-sm text-slate-400">
                  Discuss series, share theories, vote in polls, and connect with fellow anime fans.
                </p>
              </div>
            </div>

            {/* Anime Filter Banner */}
            {animeIdParam && (
              <div className="mt-4 inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-purple-900/40 border border-purple-500/40 text-xs text-purple-300">
                <Film className="w-3.5 h-3.5" />
                <span>Showing discussions for Anime #{animeIdParam}</span>
                <button
                  onClick={() => setSearchParams({})}
                  className="ml-2 hover:text-white p-0.5 rounded hover:bg-purple-800/60"
                  title="Clear anime filter"
                >
                  <X className="w-3 h-3" />
                </button>
              </div>
            )}
          </div>

          <div className="flex items-center gap-3">
            {currentUser?.is_moderator && (
              <button
                onClick={() => setActiveTab(activeTab === 'feed' ? 'moderation' : 'feed')}
                className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-semibold transition border ${
                  activeTab === 'moderation'
                    ? 'bg-purple-600 text-white border-purple-500 shadow-lg shadow-purple-600/30'
                    : 'bg-slate-900/80 text-purple-300 border-purple-800/40 hover:bg-purple-900/20'
                }`}
              >
                <Shield className="w-4 h-4" />
                <span>{activeTab === 'moderation' ? 'View Feed' : 'Moderation Center'}</span>
              </button>
            )}

            <button
              onClick={() => setCreateModalOpen(true)}
              className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white font-semibold text-sm shadow-lg shadow-purple-600/25 transition active:scale-95"
            >
              <Plus className="w-4 h-4" />
              <span>Create Post</span>
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 mt-6">
        {/* ========================================================= */}
        {/* MODERATION CENTER TAB (Authorized Staff/Moderators Only) */}
        {/* ========================================================= */}
        {activeTab === 'moderation' && currentUser?.is_moderator && (
          <div className="space-y-6">
            <div className="p-6 rounded-2xl bg-slate-900/70 border border-purple-800/30">
              <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-purple-900/20 pb-4">
                <div className="flex items-center gap-2 text-purple-300 font-bold text-lg">
                  <ShieldAlert className="w-5 h-5 text-purple-400" />
                  <span>Moderation Center & Reports Queue</span>
                </div>
                <div className="flex items-center gap-2">
                  {['pending', 'under_review', 'resolved', 'dismissed'].map((st) => (
                    <button
                      key={st}
                      onClick={() => setModerationStatusFilter(st)}
                      className={`px-3 py-1.5 rounded-lg text-xs font-semibold uppercase tracking-wider transition ${
                        moderationStatusFilter === st
                          ? 'bg-purple-600 text-white'
                          : 'bg-slate-800/70 text-slate-400 hover:text-white'
                      }`}
                    >
                      {st.replace('_', ' ')}
                    </button>
                  ))}
                </div>
              </div>

              {moderationLoading ? (
                <div className="py-12 flex justify-center text-purple-400">
                  <Loader2 className="w-8 h-8 animate-spin" />
                </div>
              ) : moderationReports.length === 0 ? (
                <div className="py-12 text-center text-slate-400">
                  <CheckCircle className="w-10 h-10 mx-auto text-emerald-400 mb-2 opacity-80" />
                  <p className="font-medium">No reports in "{moderationStatusFilter}" status.</p>
                </div>
              ) : (
                <div className="divide-y divide-purple-900/20 mt-4">
                  {moderationReports.map((report) => (
                    <div key={report.id} className="py-4 space-y-3">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className="px-2 py-0.5 rounded text-[11px] font-bold uppercase bg-purple-900/50 text-purple-300 border border-purple-700/50">
                            {report.target_type} #{report.target_id}
                          </span>
                          <span className="px-2 py-0.5 rounded text-[11px] font-medium bg-red-950/40 text-red-300 border border-red-800/30">
                            Reason: {report.reason}
                          </span>
                          <span className="text-xs text-slate-500">
                            Reported by {report.reporter?.display_name || 'Anonymous'}
                          </span>
                        </div>
                        <span className="text-xs text-slate-500">
                          {new Date(report.created_at).toLocaleDateString()}
                        </span>
                      </div>

                      <div className="p-3 rounded-lg bg-black/40 border border-slate-800/80 text-xs text-slate-300">
                        <p className="font-semibold text-slate-200 mb-1">Content Preview:</p>
                        <p className="italic text-slate-400">{report.content_preview || 'No preview available'}</p>
                        {report.explanation && (
                          <p className="mt-2 text-slate-300">
                            <span className="text-purple-400 font-semibold">Reporter explanation:</span>{' '}
                            {report.explanation}
                          </p>
                        )}
                      </div>

                      {report.status === 'pending' && (
                        <div className="flex items-center gap-2 justify-end pt-1">
                          <button
                            disabled={actioningReportId === report.id}
                            onClick={() => handleActionReport(report.id, 'content_hidden')}
                            className="px-3 py-1.5 rounded-lg bg-amber-600/80 hover:bg-amber-600 text-white text-xs font-semibold transition"
                          >
                            Hide Content
                          </button>
                          <button
                            disabled={actioningReportId === report.id}
                            onClick={() => handleActionReport(report.id, 'content_deleted')}
                            className="px-3 py-1.5 rounded-lg bg-red-600/80 hover:bg-red-600 text-white text-xs font-semibold transition"
                          >
                            Delete Content
                          </button>
                          <button
                            disabled={actioningReportId === report.id}
                            onClick={() => handleActionReport(report.id, 'dismissed', 'dismissed')}
                            className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold transition"
                          >
                            Dismiss Report
                          </button>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* ========================================================= */}
        {/* COMMUNITY FEED & DISCUSSIONS TAB                          */}
        {/* ========================================================= */}
        {activeTab === 'feed' && (
          <div className="space-y-6">
            {/* Filter & Search Bar */}
            <div className="p-4 rounded-2xl bg-slate-900/60 border border-purple-900/30 backdrop-blur-md space-y-4">
              <div className="flex flex-col lg:flex-row items-stretch lg:items-center justify-between gap-4">
                {/* Search Input */}
                <form onSubmit={handleSearchSubmit} className="relative flex-1">
                  <Search className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500" />
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search discussions, topics, titles..."
                    className="w-full pl-10 pr-10 py-2.5 rounded-xl bg-slate-950/80 border border-purple-900/40 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-purple-500 focus:ring-1 focus:ring-purple-500/50"
                  />
                  {searchQuery && (
                    <button
                      type="button"
                      onClick={handleClearSearch}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-white"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  )}
                </form>

                {/* Sort Mode Pills */}
                <div className="flex items-center gap-1.5 overflow-x-auto pb-1 lg:pb-0">
                  {SORT_OPTIONS.map((opt) => {
                    const Icon = opt.icon
                    const active = sortMode === opt.id
                    return (
                      <button
                        key={opt.id}
                        onClick={() => {
                          setSortMode(opt.id)
                          setPage(1)
                        }}
                        className={`flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-semibold whitespace-nowrap transition ${
                          active
                            ? 'bg-purple-600 text-white shadow-md shadow-purple-600/30'
                            : 'bg-slate-950/60 text-slate-400 hover:text-slate-200 border border-purple-950/40'
                        }`}
                      >
                        <Icon className="w-3.5 h-3.5" />
                        <span>{opt.label}</span>
                      </button>
                    )
                  })}
                </div>
              </div>

              {/* Category Pills & Quick Filters */}
              <div className="flex flex-wrap items-center justify-between gap-3 pt-2 border-t border-purple-900/20">
                <div className="flex items-center gap-1.5 overflow-x-auto pb-1 max-w-full">
                  {CATEGORIES.map((cat) => (
                    <button
                      key={cat.id}
                      onClick={() => {
                        setSelectedCategory(cat.id)
                        setPage(1)
                      }}
                      className={`px-3 py-1 rounded-lg text-xs font-medium whitespace-nowrap transition ${
                        selectedCategory === cat.id
                          ? 'bg-purple-900/60 text-purple-200 border border-purple-500/50'
                          : 'bg-slate-950/40 text-slate-400 hover:text-slate-200 border border-transparent'
                      }`}
                    >
                      {cat.label}
                    </button>
                  ))}
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => {
                      setSelectedFilter(selectedFilter === 'has_poll' ? 'all' : 'has_poll')
                      setPage(1)
                    }}
                    className={`flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-medium border transition ${
                      selectedFilter === 'has_poll'
                        ? 'bg-indigo-900/60 text-indigo-200 border-indigo-500/50'
                        : 'bg-slate-950/40 text-slate-400 border-purple-900/20'
                    }`}
                  >
                    <Vote className="w-3 h-3" />
                    <span>Polls</span>
                  </button>

                  <button
                    onClick={() => {
                      setSelectedFilter(selectedFilter === 'is_spoiler' ? 'all' : 'is_spoiler')
                      setPage(1)
                    }}
                    className={`flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-medium border transition ${
                      selectedFilter === 'is_spoiler'
                        ? 'bg-amber-900/60 text-amber-200 border-amber-500/50'
                        : 'bg-slate-950/40 text-slate-400 border-purple-900/20'
                    }`}
                  >
                    <AlertTriangle className="w-3 h-3" />
                    <span>Spoilers</span>
                  </button>
                </div>
              </div>

              {/* Genre Pills Strip */}
              <div className="flex items-center gap-1.5 overflow-x-auto pb-1 max-w-full pt-2 border-t border-purple-900/10">
                <span className="text-[11px] font-mono text-purple-400 uppercase flex items-center gap-1 mr-1 flex-shrink-0">
                  <Tag className="w-3 h-3 text-purple-400" /> Genre:
                </span>
                {GENRE_FILTERS.map((g) => (
                  <button
                    key={g}
                    onClick={() => {
                      setSelectedGenre(g)
                      setPage(1)
                    }}
                    className={`px-2.5 py-0.5 rounded-md text-[11px] font-mono whitespace-nowrap transition ${
                      selectedGenre === g
                        ? 'bg-cyan-900/60 text-cyan-200 border border-cyan-500/50'
                        : 'bg-slate-950/40 text-slate-400 hover:text-slate-200 border border-purple-950/20'
                    }`}
                  >
                    {g}
                  </button>
                ))}
              </div>
            </div>

            {/* Feed Content */}
            {loading ? (
              <div className="py-24 flex flex-col items-center justify-center gap-3 text-purple-400">
                <Loader2 className="w-8 h-8 animate-spin" />
                <p className="text-sm text-slate-400">Loading discussions from database...</p>
              </div>
            ) : error ? (
              <div className="p-8 rounded-2xl bg-red-950/20 border border-red-900/40 text-center text-red-300">
                <p>{error}</p>
              </div>
            ) : posts.length === 0 ? (
              <div className="p-16 rounded-2xl bg-slate-900/40 border border-purple-900/20 text-center space-y-4">
                <MessageSquare className="w-12 h-12 mx-auto text-purple-400/40" />
                <h3 className="text-lg font-bold text-slate-200">No discussions found</h3>
                <p className="text-sm text-slate-400 max-w-md mx-auto">
                  Be the first to start a conversation, share a theory, or create a community poll!
                </p>
                <button
                  onClick={() => setCreateModalOpen(true)}
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-semibold text-sm transition"
                >
                  <Plus className="w-4 h-4" />
                  <span>Start a Discussion</span>
                </button>
              </div>
            ) : (
              <div className="space-y-4">
                {posts.map((post) => {
                  const isSpoilerHidden = post.is_spoiler && !revealedSpoilers[post.id]
                  const commentsInfo = commentsState[post.id]

                  return (
                    <div
                      key={post.id}
                      className="rounded-2xl bg-slate-900/70 border border-purple-900/30 overflow-hidden transition hover:border-purple-600/40 shadow-lg shadow-black/40"
                    >
                      {/* Post Header */}
                      <div className="p-5 space-y-3">
                        <div className="flex items-start justify-between gap-4">
                          <div className="flex items-center gap-3">
                            <Link
                              to={`/users/${post.author?.id}`}
                              className="w-9 h-9 rounded-xl bg-gradient-to-tr from-purple-600 to-indigo-600 flex items-center justify-center text-white font-bold text-sm shadow-md shadow-purple-600/30 hover:opacity-90 transition flex-shrink-0"
                            >
                              {post.author?.display_name?.charAt(0)?.toUpperCase() || 'U'}
                            </Link>
                            <div>
                              <div className="flex items-center gap-2">
                                <Link
                                  to={`/users/${post.author?.id}`}
                                  className="font-semibold text-slate-200 text-sm hover:text-purple-300 transition"
                                >
                                  {post.author?.display_name || 'Guest'}
                                </Link>
                                {post.author?.is_staff || post.author?.role === 'moderator' ? (
                                  <span className="px-1.5 py-0.5 rounded text-[10px] font-bold uppercase bg-purple-950 text-purple-300 border border-purple-700/60">
                                    MOD
                                  </span>
                                ) : null}
                              </div>
                              <div className="flex items-center gap-2 text-xs text-slate-500">
                                <span>{new Date(post.created_at).toLocaleDateString()}</span>
                                <span>•</span>
                                <span className="capitalize text-purple-400 font-medium">{post.category}</span>
                              </div>
                            </div>
                          </div>

                          <div className="flex items-center gap-2">
                            {/* Anime Reference Badge */}
                            {post.anime && (
                              <Link
                                to={`/anime/${post.anime.id}`}
                                className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-purple-950/60 border border-purple-800/40 text-xs text-purple-300 hover:text-white transition"
                              >
                                <Film className="w-3 h-3 text-purple-400" />
                                <span className="max-w-[140px] truncate">{post.anime.title}</span>
                              </Link>
                            )}

                            {/* Report Flag Button */}
                            <button
                              onClick={() => openReportModal('post', post.id, post.title)}
                              className="text-slate-500 hover:text-amber-400 p-1.5 rounded-lg hover:bg-slate-800/60 transition"
                              title="Report post"
                            >
                              <Flag className="w-3.5 h-3.5" />
                            </button>

                            {/* Owner or Moderator Delete */}
                            {(currentUser?.id === post.author?.id || currentUser?.is_moderator) && (
                              <button
                                onClick={() => handleDeletePost(post.id)}
                                className="text-slate-500 hover:text-red-400 p-1.5 rounded-lg hover:bg-slate-800/60 transition"
                                title="Delete post"
                              >
                                <Trash2 className="w-3.5 h-3.5" />
                              </button>
                            )}
                          </div>
                        </div>

                        {/* Post Title */}
                        <h2 className="text-lg font-bold text-white tracking-wide">{post.title}</h2>

                        {/* Spoiler Protection Overlay */}
                        {isSpoilerHidden ? (
                          <div className="p-4 rounded-xl bg-amber-950/20 border border-amber-900/40 flex items-center justify-between gap-4">
                            <div className="flex items-center gap-2 text-amber-300 text-xs font-semibold">
                              <AlertTriangle className="w-4 h-4 text-amber-400 flex-shrink-0" />
                              <span>SPOILER ALERT — This post contains spoilers.</span>
                            </div>
                            <button
                              onClick={() => toggleSpoilerReveal(post.id)}
                              className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-amber-900/40 hover:bg-amber-900/60 text-amber-200 text-xs font-medium border border-amber-700/50 transition"
                            >
                              <Eye className="w-3.5 h-3.5" />
                              <span>Reveal</span>
                            </button>
                          </div>
                        ) : (
                          <div className="space-y-2">
                            {post.is_spoiler && (
                              <div className="flex items-center justify-between text-[11px] text-amber-400/80 pb-1">
                                <span className="flex items-center gap-1 font-semibold">
                                  <AlertTriangle className="w-3 h-3" /> Spoiler content revealed
                                </span>
                                <button
                                  onClick={() => toggleSpoilerReveal(post.id)}
                                  className="text-slate-500 hover:text-slate-300"
                                >
                                  Hide
                                </button>
                              </div>
                            )}
                            <p className="text-sm text-slate-300 whitespace-pre-line leading-relaxed">
                              {post.body}
                            </p>
                          </div>
                        )}

                        {/* Tags */}
                        {post.tags && post.tags.length > 0 && (
                          <div className="flex flex-wrap items-center gap-1.5 pt-1">
                            {post.tags.map((t, idx) => (
                              <span
                                key={idx}
                                className="px-2 py-0.5 rounded-md text-[11px] bg-slate-950/60 text-purple-300/80 border border-purple-950"
                              >
                                #{t}
                              </span>
                            ))}
                          </div>
                        )}

                        {/* ========================================= */}
                        {/* Interactive Poll Component                */}
                        {/* ========================================= */}
                        {post.poll && (
                          <div className="mt-4 p-4 rounded-xl bg-slate-950/70 border border-indigo-900/40 space-y-3">
                            <div className="flex items-center justify-between">
                              <div className="flex items-center gap-2 text-sm font-bold text-indigo-300">
                                <Vote className="w-4 h-4 text-indigo-400" />
                                <span>{post.poll.question}</span>
                              </div>
                              <span className="text-[11px] text-slate-500">
                                {post.poll.total_votes} {post.poll.total_votes === 1 ? 'vote' : 'votes'}
                                {post.poll.is_closed && ' • Closed'}
                              </span>
                            </div>

                            <div className="space-y-2">
                              {post.poll.options?.map((opt) => {
                                const hasVoted = post.poll.my_vote_option_id !== null
                                const isMyVote = post.poll.my_vote_option_id === opt.id

                                if (hasVoted || post.poll.is_closed) {
                                  return (
                                    <div
                                      key={opt.id}
                                      className={`relative overflow-hidden rounded-lg p-2.5 border transition ${
                                        isMyVote
                                          ? 'border-indigo-500/80 bg-indigo-950/30'
                                          : 'border-slate-800/70 bg-black/30'
                                      }`}
                                    >
                                      {/* Percentage Fill Bar */}
                                      <div
                                        className="absolute inset-y-0 left-0 bg-indigo-600/25 transition-all duration-500"
                                        style={{ width: `${opt.percentage}%` }}
                                      />
                                      <div className="relative flex items-center justify-between text-xs z-10">
                                        <span className={`font-medium ${isMyVote ? 'text-indigo-200' : 'text-slate-300'}`}>
                                          {opt.text} {isMyVote && '✓ (Your vote)'}
                                        </span>
                                        <span className="font-bold text-slate-400">
                                          {opt.percentage}% ({opt.vote_count})
                                        </span>
                                      </div>
                                    </div>
                                  )
                                }

                                return (
                                  <button
                                    key={opt.id}
                                    disabled={votingPollId === post.poll.id}
                                    onClick={() => handlePollVote(post.poll.id, opt.id, post.id)}
                                    className="w-full text-left p-2.5 rounded-lg bg-slate-900/90 hover:bg-indigo-950/40 border border-slate-800 hover:border-indigo-600/60 text-xs text-slate-200 font-medium transition active:scale-[0.99] flex items-center justify-between"
                                  >
                                    <span>{opt.text}</span>
                                    <span className="text-[10px] text-indigo-400 opacity-80">Click to vote</span>
                                  </button>
                                )
                              })}
                            </div>
                          </div>
                        )}
                      </div>

                      {/* Post Action Toolbar */}
                      <div className="px-5 py-3 border-t border-purple-900/20 bg-slate-950/30 flex items-center justify-between text-xs text-slate-400">
                        <div className="flex items-center gap-4">
                          {/* Like Button */}
                          <button
                            onClick={() => handleToggleLike(post.id, post.liked_by_me)}
                            className={`flex items-center gap-1.5 font-semibold transition ${
                              post.liked_by_me
                                ? 'text-red-400 scale-105'
                                : 'text-slate-400 hover:text-red-400'
                            }`}
                          >
                            <Heart className={`w-4 h-4 ${post.liked_by_me ? 'fill-current' : ''}`} />
                            <span>{post.like_count}</span>
                          </button>

                          {/* Comments Button */}
                          <button
                            onClick={() => handleToggleComments(post.id)}
                            className="flex items-center gap-1.5 text-slate-400 hover:text-purple-300 font-semibold transition"
                          >
                            <MessageCircle className="w-4 h-4" />
                            <span>
                              {post.comment_count} {post.comment_count === 1 ? 'Comment' : 'Comments'}
                            </span>
                          </button>
                        </div>

                        <button
                          onClick={() => handleToggleComments(post.id)}
                          className="text-purple-400 hover:text-purple-300 flex items-center gap-1 font-medium"
                        >
                          <span>{commentsInfo?.open ? 'Hide Discussion' : 'Join Discussion'}</span>
                          {commentsInfo?.open ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                        </button>
                      </div>

                      {/* ========================================= */}
                      {/* Threaded Comments Section                 */}
                      {/* ========================================= */}
                      {commentsInfo?.open && (
                        <div className="p-5 border-t border-purple-900/20 bg-black/40 space-y-4">
                          {/* Comment Input */}
                          <div className="space-y-2">
                            <div className="flex items-center gap-2">
                              <input
                                type="text"
                                value={commentInputs[post.id] || ''}
                                onChange={(e) =>
                                  setCommentInputs((prev) => ({ ...prev, [post.id]: e.target.value }))
                                }
                                onKeyDown={(e) => {
                                  if (e.key === 'Enter') handleAddComment(post.id)
                                }}
                                placeholder="Add to the discussion..."
                                className="flex-1 px-3.5 py-2 rounded-xl bg-slate-900/80 border border-purple-900/30 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-purple-500"
                              />
                              <button
                                disabled={submittingComment[post.id]}
                                onClick={() => handleAddComment(post.id)}
                                className="px-3 py-2 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-medium text-xs flex items-center gap-1.5 transition disabled:opacity-50"
                              >
                                <Send className="w-3.5 h-3.5" />
                                <span>Send</span>
                              </button>
                            </div>
                            <div className="flex items-center justify-between text-[11px] text-slate-400 px-1">
                              <label className="flex items-center gap-1.5 cursor-pointer hover:text-slate-300">
                                <input
                                  type="checkbox"
                                  checked={!!commentSpoilerFlags[post.id]}
                                  onChange={(e) =>
                                    setCommentSpoilerFlags((prev) => ({
                                      ...prev,
                                      [post.id]: e.target.checked,
                                    }))
                                  }
                                  className="rounded border-purple-900/40 text-purple-600 focus:ring-0 bg-slate-900"
                                />
                                <span>Mark comment as spoiler</span>
                              </label>
                            </div>
                          </div>

                          {/* Comments List */}
                          {commentsInfo.loading ? (
                            <div className="py-6 flex justify-center text-purple-400">
                              <Loader2 className="w-5 h-5 animate-spin" />
                            </div>
                          ) : commentsInfo.comments?.length === 0 ? (
                            <p className="text-center text-xs text-slate-500 py-3">
                              No comments yet. Start the conversation!
                            </p>
                          ) : (
                            <div className="space-y-3 pt-2">
                              {commentsInfo.comments.map((comment) => {
                                const commentSpoilerHidden =
                                  comment.is_spoiler && !revealedSpoilers[`comment_${comment.id}`]

                                return (
                                  <div key={comment.id} className="space-y-2">
                                    {/* Root Comment Box */}
                                    <div className="p-3 rounded-xl bg-slate-900/70 border border-slate-800/80 space-y-1.5">
                                      <div className="flex items-center justify-between text-xs">
                                        <div className="flex items-center gap-2">
                                          <Link
                                            to={`/users/${comment.author?.id}`}
                                            className="font-semibold text-slate-200 hover:text-purple-300 transition"
                                          >
                                            {comment.author?.display_name || 'Guest'}
                                          </Link>
                                          {comment.author?.is_staff && (
                                            <span className="px-1 py-0.2 rounded text-[9px] font-bold uppercase bg-purple-950 text-purple-300">
                                              MOD
                                            </span>
                                          )}
                                          <span className="text-slate-500 text-[11px]">
                                            {new Date(comment.created_at).toLocaleTimeString([], {
                                              hour: '2-digit',
                                              minute: '2-digit',
                                            })}
                                          </span>
                                        </div>

                                        <div className="flex items-center gap-1.5">
                                          <button
                                            onClick={() => openReportModal('comment', comment.id, comment.body)}
                                            className="text-slate-500 hover:text-amber-400 p-1"
                                            title="Report comment"
                                          >
                                            <Flag className="w-3 h-3" />
                                          </button>
                                          {(currentUser?.id === comment.author?.id || currentUser?.is_moderator) && (
                                            <button
                                              onClick={() => handleDeleteComment(post.id, comment.id)}
                                              className="text-slate-500 hover:text-red-400 p-1"
                                              title="Delete comment"
                                            >
                                              <Trash2 className="w-3 h-3" />
                                            </button>
                                          )}
                                        </div>
                                      </div>

                                      {/* Comment Body / Spoiler */}
                                      {commentSpoilerHidden ? (
                                        <div className="flex items-center justify-between p-2 rounded bg-amber-950/20 border border-amber-900/40 text-[11px]">
                                          <span className="text-amber-300 font-medium">
                                            ⚠️ Comment contains spoilers
                                          </span>
                                          <button
                                            onClick={() => toggleSpoilerReveal(`comment_${comment.id}`)}
                                            className="text-amber-400 hover:underline"
                                          >
                                            Reveal
                                          </button>
                                        </div>
                                      ) : (
                                        <p className="text-xs text-slate-300 leading-relaxed">{comment.body}</p>
                                      )}

                                      {/* Reply Button */}
                                      <div className="flex justify-end pt-1">
                                        <button
                                          onClick={() =>
                                            setActiveReplyId(activeReplyId === comment.id ? null : comment.id)
                                          }
                                          className="text-[11px] text-purple-400 hover:text-purple-300 font-medium flex items-center gap-1"
                                        >
                                          <CornerDownRight className="w-3 h-3" />
                                          <span>Reply</span>
                                        </button>
                                      </div>
                                    </div>

                                    {/* Inline Reply Input */}
                                    {activeReplyId === comment.id && (
                                      <div className="ml-6 p-2 rounded-xl bg-purple-950/20 border border-purple-900/40 space-y-2">
                                        <div className="flex items-center gap-2">
                                          <input
                                            type="text"
                                            value={replyInputs[comment.id] || ''}
                                            onChange={(e) =>
                                              setReplyInputs((prev) => ({
                                                ...prev,
                                                [comment.id]: e.target.value,
                                              }))
                                            }
                                            onKeyDown={(e) => {
                                              if (e.key === 'Enter') handleAddReply(post.id, comment.id)
                                            }}
                                            placeholder={`Reply to ${comment.author?.display_name}...`}
                                            className="flex-1 px-3 py-1.5 rounded-lg bg-black/60 border border-purple-900/30 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-purple-500"
                                          />
                                          <button
                                            disabled={submittingComment[comment.id]}
                                            onClick={() => handleAddReply(post.id, comment.id)}
                                            className="px-2.5 py-1.5 rounded-lg bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold"
                                          >
                                            Reply
                                          </button>
                                        </div>
                                        <label className="flex items-center gap-1.5 text-[10px] text-slate-400 cursor-pointer">
                                          <input
                                            type="checkbox"
                                            checked={!!replySpoilerFlags[comment.id]}
                                            onChange={(e) =>
                                              setReplySpoilerFlags((prev) => ({
                                                ...prev,
                                                [comment.id]: e.target.checked,
                                              }))
                                            }
                                            className="rounded border-purple-900/40 text-purple-600 focus:ring-0 bg-slate-900"
                                          />
                                          <span>Mark reply as spoiler</span>
                                        </label>
                                      </div>
                                    )}

                                    {/* Nested Replies List */}
                                    {comment.replies && comment.replies.length > 0 && (
                                      <div className="ml-6 space-y-2 border-l-2 border-purple-900/30 pl-3">
                                        {comment.replies.map((reply) => {
                                          const replySpoilerHidden =
                                            reply.is_spoiler && !revealedSpoilers[`comment_${reply.id}`]

                                          return (
                                            <div
                                              key={reply.id}
                                              className="p-2.5 rounded-xl bg-slate-950/70 border border-slate-800/60 space-y-1 text-xs"
                                            >
                                              <div className="flex items-center justify-between">
                                                <Link
                                                  to={`/users/${reply.author?.id}`}
                                                  className="font-semibold text-slate-200 hover:text-purple-300 transition"
                                                >
                                                  {reply.author?.display_name || 'Guest'}
                                                </Link>
                                                <div className="flex items-center gap-1">
                                                  <button
                                                    onClick={() => openReportModal('comment', reply.id, reply.body)}
                                                    className="text-slate-500 hover:text-amber-400 p-0.5"
                                                    title="Report reply"
                                                  >
                                                    <Flag className="w-2.5 h-2.5" />
                                                  </button>
                                                  {(currentUser?.id === reply.author?.id || currentUser?.is_moderator) && (
                                                    <button
                                                      onClick={() => handleDeleteComment(post.id, reply.id)}
                                                      className="text-slate-500 hover:text-red-400 p-0.5"
                                                      title="Delete reply"
                                                    >
                                                      <Trash2 className="w-2.5 h-2.5" />
                                                    </button>
                                                  )}
                                                </div>
                                              </div>

                                              {replySpoilerHidden ? (
                                                <div className="flex items-center justify-between p-1.5 rounded bg-amber-950/20 border border-amber-900/40 text-[10px]">
                                                  <span className="text-amber-300">⚠️ Spoiler reply</span>
                                                  <button
                                                    onClick={() => toggleSpoilerReveal(`comment_${reply.id}`)}
                                                    className="text-amber-400 hover:underline"
                                                  >
                                                    Reveal
                                                  </button>
                                                </div>
                                              ) : (
                                                <p className="text-slate-300">{reply.body}</p>
                                              )}
                                            </div>
                                          )
                                        })}
                                      </div>
                                    )}
                                  </div>
                                )
                              })}
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            )}

            {/* Pagination Controls */}
            {pagination.total_pages > 1 && (
              <div className="flex items-center justify-center gap-3 pt-6 pb-12">
                <button
                  disabled={page <= 1}
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  className="px-4 py-2 rounded-xl bg-slate-900/80 border border-purple-900/30 text-xs font-semibold text-slate-300 disabled:opacity-40 transition"
                >
                  Previous
                </button>
                <span className="text-xs text-slate-400">
                  Page <span className="text-purple-400 font-bold">{page}</span> of {pagination.total_pages}
                </span>
                <button
                  disabled={page >= pagination.total_pages}
                  onClick={() => setPage((p) => Math.min(pagination.total_pages, p + 1))}
                  className="px-4 py-2 rounded-xl bg-slate-900/80 border border-purple-900/30 text-xs font-semibold text-slate-300 disabled:opacity-40 transition"
                >
                  Next
                </button>
              </div>
            )}
          </div>
        )}
      </div>

      {/* ========================================================= */}
      {/* CREATE POST MODAL                                         */}
      {/* ========================================================= */}
      {createModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 overflow-y-auto">
          <div className="relative w-full max-w-xl rounded-2xl bg-[#0c0c17] border border-purple-700/40 p-6 shadow-2xl shadow-purple-950/60 max-h-[90vh] overflow-y-auto">
            <button
              onClick={() => setCreateModalOpen(false)}
              className="absolute top-5 right-5 text-slate-400 hover:text-white"
            >
              <X className="w-5 h-5" />
            </button>

            <h2 className="text-xl font-extrabold text-white mb-4 flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-purple-400" />
              <span>Create New Discussion</span>
            </h2>

            {createError && (
              <div className="mb-4 p-3 rounded-xl bg-red-950/40 border border-red-800/40 text-xs text-red-300">
                {createError}
              </div>
            )}

            <form onSubmit={handleCreatePost} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                  Discussion Title *
                </label>
                <input
                  type="text"
                  maxLength={120}
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  placeholder="e.g. Eren's true motivation in Season 4..."
                  className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-purple-900/40 text-sm text-white placeholder-slate-600 focus:outline-none focus:border-purple-500"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                    Category
                  </label>
                  <select
                    value={newCategory}
                    onChange={(e) => setNewCategory(e.target.value)}
                    className="w-full px-3 py-2.5 rounded-xl bg-slate-950 border border-purple-900/40 text-xs text-slate-200 focus:outline-none focus:border-purple-500"
                  >
                    <option value="discussion">💬 Discussion</option>
                    <option value="theory">🔮 Theory</option>
                    <option value="review">⭐ Review</option>
                    <option value="question">❓ Question</option>
                    <option value="news">📰 News</option>
                    <option value="fan_art">🎨 Fan Art</option>
                    <option value="recommendation">🎯 Recommendation</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                    Link Anime (MAL ID, optional)
                  </label>
                  <input
                    type="number"
                    value={newAnimeId}
                    onChange={(e) => setNewAnimeId(e.target.value)}
                    placeholder="e.g. 16498"
                    className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-purple-900/40 text-xs text-slate-200 placeholder-slate-600 focus:outline-none focus:border-purple-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                  Body Content *
                </label>
                <textarea
                  rows={4}
                  maxLength={2000}
                  value={newBody}
                  onChange={(e) => setNewBody(e.target.value)}
                  placeholder="Share your thoughts, review, or theory in detail..."
                  className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-purple-900/40 text-sm text-white placeholder-slate-600 focus:outline-none focus:border-purple-500 resize-none"
                />
              </div>

              {/* Tags Section */}
              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                  Tags (max 5)
                </label>
                <div className="flex flex-wrap gap-1.5 mb-2">
                  {newTags.map((tag, idx) => (
                    <span
                      key={idx}
                      className="px-2.5 py-1 rounded-lg text-xs bg-purple-950/70 border border-purple-700/50 text-purple-300 flex items-center gap-1.5"
                    >
                      #{tag}
                      <button
                        type="button"
                        onClick={() => setNewTags(newTags.filter((_, i) => i !== idx))}
                        className="hover:text-white"
                      >
                        <X className="w-3 h-3" />
                      </button>
                    </span>
                  ))}
                </div>
                <div className="flex items-center gap-2">
                  <input
                    type="text"
                    value={tagInput}
                    onChange={(e) => setTagInput(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        e.preventDefault()
                        const t = tagInput.trim().replace(/^#/, '')
                        if (t && newTags.length < 5 && !newTags.includes(t)) {
                          setNewTags([...newTags, t])
                          setTagInput('')
                        }
                      }
                    }}
                    placeholder="Type tag and press Enter..."
                    className="flex-1 px-3 py-1.5 rounded-xl bg-slate-950 border border-purple-900/40 text-xs text-slate-200 placeholder-slate-600 focus:outline-none focus:border-purple-500"
                  />
                </div>
                <div className="flex flex-wrap gap-1.5 mt-2">
                  {TAG_SUGGESTIONS.map((sug) => (
                    <button
                      key={sug}
                      type="button"
                      onClick={() => {
                        if (newTags.length < 5 && !newTags.includes(sug)) {
                          setNewTags([...newTags, sug])
                        }
                      }}
                      className="text-[11px] text-slate-400 hover:text-purple-300 bg-slate-900/60 px-2 py-0.5 rounded border border-purple-950"
                    >
                      +{sug}
                    </button>
                  ))}
                </div>
              </div>

              {/* Spoiler Toggle */}
              <div className="p-3 rounded-xl bg-slate-950 border border-purple-900/30 flex items-center justify-between">
                <div className="flex items-center gap-2 text-xs text-slate-300">
                  <AlertTriangle className="w-4 h-4 text-amber-400" />
                  <div>
                    <p className="font-semibold text-slate-200">Contains Spoilers?</p>
                    <p className="text-[11px] text-slate-500">
                      Content will be hidden behind a spoiler warning for readers.
                    </p>
                  </div>
                </div>
                <input
                  type="checkbox"
                  checked={newIsSpoiler}
                  onChange={(e) => setNewIsSpoiler(e.target.checked)}
                  className="w-4 h-4 rounded border-purple-900 text-purple-600 focus:ring-0 bg-slate-900"
                />
              </div>

              {/* Poll Accordion Toggle */}
              <div className="p-3 rounded-xl bg-slate-950 border border-purple-900/30 space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-xs text-slate-300">
                    <Vote className="w-4 h-4 text-indigo-400" />
                    <div>
                      <p className="font-semibold text-slate-200">Attach Community Poll</p>
                      <p className="text-[11px] text-slate-500">Allow users to vote on multiple options.</p>
                    </div>
                  </div>
                  <input
                    type="checkbox"
                    checked={hasPoll}
                    onChange={(e) => setHasPoll(e.target.checked)}
                    className="w-4 h-4 rounded border-purple-900 text-indigo-600 focus:ring-0 bg-slate-900"
                  />
                </div>

                {hasPoll && (
                  <div className="pt-2 border-t border-purple-900/20 space-y-2.5">
                    <input
                      type="text"
                      value={pollQuestion}
                      onChange={(e) => setPollQuestion(e.target.value)}
                      placeholder="Poll Question (e.g. Which ending was best?)"
                      className="w-full px-3 py-2 rounded-lg bg-black/60 border border-indigo-900/40 text-xs text-slate-100 placeholder-slate-600 focus:outline-none focus:border-indigo-500"
                    />

                    {pollOptions.map((opt, idx) => (
                      <div key={idx} className="flex items-center gap-2">
                        <input
                          type="text"
                          value={opt}
                          onChange={(e) => {
                            const updated = [...pollOptions]
                            updated[idx] = e.target.value
                            setPollOptions(updated)
                          }}
                          placeholder={`Option ${idx + 1}`}
                          className="flex-1 px-3 py-1.5 rounded-lg bg-black/60 border border-indigo-900/40 text-xs text-slate-100 placeholder-slate-600 focus:outline-none focus:border-indigo-500"
                        />
                        {pollOptions.length > 2 && (
                          <button
                            type="button"
                            onClick={() => setPollOptions(pollOptions.filter((_, i) => i !== idx))}
                            className="text-slate-500 hover:text-red-400 p-1"
                          >
                            <X className="w-3.5 h-3.5" />
                          </button>
                        )}
                      </div>
                    ))}

                    {pollOptions.length < 8 && (
                      <button
                        type="button"
                        onClick={() => setPollOptions([...pollOptions, ''])}
                        className="text-xs text-indigo-400 hover:text-indigo-300 font-semibold flex items-center gap-1"
                      >
                        <Plus className="w-3.5 h-3.5" />
                        <span>Add Option</span>
                      </button>
                    )}
                  </div>
                )}
              </div>

              <div className="flex items-center justify-end gap-3 pt-3">
                <button
                  type="button"
                  onClick={() => setCreateModalOpen(false)}
                  className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-400 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={creating}
                  className="px-6 py-2.5 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-semibold text-xs shadow-lg shadow-purple-600/30 transition disabled:opacity-50"
                >
                  {creating ? 'Publishing...' : 'Publish Post'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ========================================================= */}
      {/* USER REPORTING MODAL                                      */}
      {/* ========================================================= */}
      {reportModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
          <div className="relative w-full max-w-md rounded-2xl bg-[#0c0c17] border border-purple-700/40 p-6 shadow-2xl shadow-purple-950/60">
            <button
              onClick={() => setReportModalOpen(false)}
              className="absolute top-5 right-5 text-slate-400 hover:text-white"
            >
              <X className="w-5 h-5" />
            </button>

            <h2 className="text-lg font-bold text-white mb-2 flex items-center gap-2">
              <Flag className="w-4 h-4 text-amber-400" />
              <span>Report Community Content</span>
            </h2>
            <p className="text-xs text-slate-400 mb-4">
              Help keep AnimeVerse AI safe. Reports are reviewed privately by moderators.
            </p>

            {reportFeedback && (
              <div
                className={`mb-4 p-3 rounded-xl border text-xs ${
                  reportFeedback.type === 'success'
                    ? 'bg-emerald-950/40 border-emerald-800/40 text-emerald-300'
                    : 'bg-red-950/40 border-red-800/40 text-red-300'
                }`}
              >
                {reportFeedback.message}
              </div>
            )}

            <form onSubmit={handleSubmitReport} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                  Reason for Report *
                </label>
                <select
                  value={reportReason}
                  onChange={(e) => setReportReason(e.target.value)}
                  className="w-full px-3 py-2.5 rounded-xl bg-slate-950 border border-purple-900/40 text-xs text-slate-200 focus:outline-none focus:border-purple-500"
                >
                  <option value="inappropriate">Inappropriate or sexually explicit</option>
                  <option value="spam">Spam, bot activity, or advertising</option>
                  <option value="harassment">Harassment, hate speech, or abuse</option>
                  <option value="unmarked_spoilers">Unmarked spoilers without warning</option>
                  <option value="other">Other policy violation</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                  Additional Details (Optional)
                </label>
                <textarea
                  rows={3}
                  maxLength={500}
                  value={reportExplanation}
                  onChange={(e) => setReportExplanation(e.target.value)}
                  placeholder="Provide context for our moderation team..."
                  className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-purple-900/40 text-xs text-white placeholder-slate-600 focus:outline-none focus:border-purple-500 resize-none"
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setReportModalOpen(false)}
                  className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-400 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submittingReport}
                  className="px-5 py-2 rounded-xl bg-amber-600 hover:bg-amber-500 text-white font-semibold text-xs transition disabled:opacity-50"
                >
                  {submittingReport ? 'Submitting...' : 'Submit Report'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

export default CommunityPage

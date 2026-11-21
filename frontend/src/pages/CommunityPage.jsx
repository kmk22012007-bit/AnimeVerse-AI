import React, { useState, useEffect } from 'react'
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
} from 'lucide-react'
import {
  getCommunityPosts,
  createCommunityPost,
  getCommunityPostDetail,
  likeCommunityPost,
  unlikeCommunityPost,
  addCommentToPost,
} from '../api/community'

export const CommunityPage = () => {
  const [posts, setPosts] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [page, setPage] = useState(1)
  const [pagination, setPagination] = useState({ page: 1, total_pages: 1, total: 0 })

  // Create post modal state
  const [createModalOpen, setCreateModalOpen] = useState(false)
  const [newTitle, setNewTitle] = useState('')
  const [newBody, setNewBody] = useState('')
  const [creating, setCreating] = useState(false)
  const [createError, setCreateError] = useState(null)

  // Expanded post comments state: { [postId]: { comments: [], loading: false, open: boolean } }
  const [commentsState, setCommentsState] = useState({})
  const [commentInputs, setCommentInputs] = useState({})
  const [submittingComment, setSubmittingComment] = useState({})

  const fetchPosts = async (targetPage = 1) => {
    setLoading(true)
    setError(null)
    try {
      const res = await getCommunityPosts(targetPage)
      setPosts(res?.results || [])
      setPagination(res?.pagination || { page: targetPage, total_pages: 1, total: res?.results?.length || 0 })
    } catch (err) {
      setError('Unable to load community feed from database.')
      setPosts([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchPosts(page)
  }, [page])

  // Handle Create Post
  const handleCreatePost = async (e) => {
    e.preventDefault()
    if (!newTitle.trim() || !newBody.trim()) {
      setCreateError('Please provide both a title and post body.')
      return
    }

    setCreating(true)
    setCreateError(null)
    try {
      const created = await createCommunityPost(newTitle.trim(), newBody.trim())
      setPosts((prev) => [created, ...prev])
      setNewTitle('')
      setNewBody('')
      setCreateModalOpen(false)
    } catch (err) {
      setCreateError(err.response?.data?.message || 'Failed to publish post.')
    } finally {
      setCreating(false)
    }
  }

  // Handle Like/Unlike
  const handleToggleLike = async (postId, currentlyLiked) => {
    // Optimistic UI update
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
      // Revert if error
      fetchPosts(page)
    }
  }

  // Handle Toggle Comments View
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

  // Handle Add Comment
  const handleAddComment = async (postId) => {
    const body = (commentInputs[postId] || '').trim()
    if (!body) return

    setSubmittingComment((prev) => ({ ...prev, [postId]: true }))
    try {
      const newComment = await addCommentToPost(postId, body)
      setCommentsState((prev) => ({
        ...prev,
        [postId]: {
          ...prev[postId],
          comments: [...(prev[postId]?.comments || []), newComment],
        },
      }))
      // Increment comment count in post card
      setPosts((prev) =>
        prev.map((p) => (p.id === postId ? { ...p, comment_count: p.comment_count + 1 } : p))
      )
      setCommentInputs((prev) => ({ ...prev, [postId]: '' }))
    } catch (err) {
      // error handling
    } finally {
      setSubmittingComment((prev) => ({ ...prev, [postId]: false }))
    }
  }

  return (
    <div className="space-y-8 max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-wide flex items-center gap-2.5">
            <MessageSquare className="w-7 h-7 text-purple-400" />
            Community Lounge
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-1 font-mono">
            Anime discussions, theories, episode reviews, and live otaku thoughts
          </p>
        </div>

        <button
          onClick={() => setCreateModalOpen(true)}
          type="button"
          className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-purple-600 hover:bg-purple-500 text-white text-xs sm:text-sm font-semibold transition-all shadow-[0_0_15px_rgba(168,85,247,0.4)] cursor-pointer self-start sm:self-auto"
        >
          <Plus className="w-4 h-4" />
          <span>New Discussion</span>
        </button>
      </div>

      {/* Main Feed */}
      {loading ? (
        <div className="p-12 text-center text-xs font-mono text-purple-300">
          Loading community feeds from database...
        </div>
      ) : error ? (
        <div className="p-8 rounded-2xl bg-rose-950/20 border border-rose-500/20 text-center text-rose-300 text-xs font-mono">
          {error}
        </div>
      ) : posts.length === 0 ? (
        <div className="p-12 rounded-3xl bg-[#0c0e1e] border border-purple-500/20 text-center space-y-4 max-w-md mx-auto">
          <div className="w-12 h-12 rounded-2xl bg-purple-950 flex items-center justify-center mx-auto text-purple-400 border border-purple-500/30">
            <MessageSquare className="w-6 h-6" />
          </div>
          <h3 className="text-base font-bold text-white">No Community Discussions Yet</h3>
          <p className="text-xs text-slate-400">
            Be the first otaku in this demo session to spark a debate or share your anime review!
          </p>
          <button
            onClick={() => setCreateModalOpen(true)}
            type="button"
            className="inline-flex items-center gap-2 px-5 py-2 rounded-xl bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold transition-all"
          >
            <Plus className="w-4 h-4" /> Start Discussion
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {posts.map((post) => {
            const commentsInfo = commentsState[post.id] || { open: false, comments: [] }

            return (
              <div
                key={post.id}
                className="rounded-2xl bg-[#0c0e1e]/90 border border-purple-500/25 p-5 sm:p-6 space-y-4 transition-all hover:border-purple-500/40 shadow-sm"
              >
                {/* Author & Timestamp */}
                <div className="flex items-center justify-between text-xs">
                  <div className="flex items-center gap-2.5">
                    <div className="w-7 h-7 rounded-lg bg-gradient-to-tr from-purple-600 to-indigo-600 flex items-center justify-center text-white text-xs font-bold">
                      <User className="w-3.5 h-3.5" />
                    </div>
                    <div>
                      <span className="font-semibold text-white block leading-tight">
                        {post.author?.display_name || 'Anonymous Otaku'}
                      </span>
                      <span className="text-[10px] font-mono text-slate-400 flex items-center gap-1">
                        <Clock className="w-2.5 h-2.5 text-purple-400" />
                        {post.created_at ? new Date(post.created_at).toLocaleDateString() : 'Just now'}
                      </span>
                    </div>
                  </div>

                  <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-purple-950/60 border border-purple-500/20 text-purple-300">
                    Post #{post.id}
                  </span>
                </div>

                {/* Post Content */}
                <div className="space-y-1.5">
                  <h3 className="text-base font-bold text-white tracking-wide">
                    {post.title}
                  </h3>
                  <p className="text-xs sm:text-sm text-slate-300 leading-relaxed whitespace-pre-wrap">
                    {post.body}
                  </p>
                </div>

                {/* Actions: Likes & Comments Toggle */}
                <div className="pt-3 border-t border-purple-950/80 flex items-center gap-4 text-xs font-mono">
                  <button
                    onClick={() => handleToggleLike(post.id, post.liked_by_me)}
                    type="button"
                    className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl border transition-all cursor-pointer ${
                      post.liked_by_me
                        ? 'bg-rose-950/40 border-rose-500/50 text-rose-300'
                        : 'bg-purple-950/30 border-purple-500/20 text-slate-400 hover:text-white'
                    }`}
                  >
                    <Heart className={`w-3.5 h-3.5 ${post.liked_by_me ? 'fill-rose-400 text-rose-400' : ''}`} />
                    <span>{post.like_count || 0}</span>
                  </button>

                  <button
                    onClick={() => handleToggleComments(post.id)}
                    type="button"
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-purple-950/30 hover:bg-purple-900/40 border border-purple-500/20 text-slate-300 transition-colors cursor-pointer"
                  >
                    <MessageCircle className="w-3.5 h-3.5 text-purple-400" />
                    <span>{post.comment_count || 0} Comments</span>
                    {commentsInfo.open ? (
                      <ChevronUp className="w-3 h-3 text-slate-400" />
                    ) : (
                      <ChevronDown className="w-3 h-3 text-slate-400" />
                    )}
                  </button>
                </div>

                {/* Expandable Comments Drawer */}
                {commentsInfo.open && (
                  <div className="pt-4 border-t border-purple-950/60 space-y-3 animate-in fade-in duration-150">
                    {/* Add Comment Input */}
                    <div className="flex gap-2">
                      <input
                        type="text"
                        value={commentInputs[post.id] || ''}
                        onChange={(e) =>
                          setCommentInputs((prev) => ({ ...prev, [post.id]: e.target.value }))
                        }
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') handleAddComment(post.id)
                        }}
                        placeholder="Write a comment..."
                        className="flex-1 px-3.5 py-2 rounded-xl bg-purple-950/40 border border-purple-500/30 text-xs text-white placeholder:text-slate-500 focus:outline-none focus:border-purple-400"
                      />
                      <button
                        onClick={() => handleAddComment(post.id)}
                        disabled={submittingComment[post.id] || !commentInputs[post.id]?.trim()}
                        type="button"
                        className="px-4 py-2 rounded-xl bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold flex items-center gap-1.5 disabled:opacity-40 transition-all cursor-pointer"
                      >
                        {submittingComment[post.id] ? (
                          <Loader2 className="w-3.5 h-3.5 animate-spin" />
                        ) : (
                          <Send className="w-3.5 h-3.5" />
                        )}
                        <span>Reply</span>
                      </button>
                    </div>

                    {/* Comments List */}
                    {commentsInfo.loading ? (
                      <div className="py-2 text-center text-xs font-mono text-purple-300">
                        Loading comments...
                      </div>
                    ) : commentsInfo.comments.length === 0 ? (
                      <div className="py-2 text-center text-xs text-slate-400 font-mono">
                        No comments yet. Start the conversation!
                      </div>
                    ) : (
                      <div className="space-y-2 pt-1 divide-y divide-purple-950/50">
                        {commentsInfo.comments.map((c) => (
                          <div key={c.id} className="pt-2 text-xs space-y-1">
                            <div className="flex items-center justify-between text-[11px] font-mono">
                              <span className="font-semibold text-purple-300">
                                {c.author?.display_name || 'Otaku'}
                              </span>
                              <span className="text-slate-400 text-[10px]">
                                {c.created_at ? new Date(c.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : ''}
                              </span>
                            </div>
                            <p className="text-slate-200 text-xs leading-relaxed">{c.body}</p>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}

      {/* Create Post Modal */}
      {createModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="w-full max-w-lg rounded-3xl bg-[#0c0e1e] border border-purple-500/40 p-6 space-y-5 shadow-[0_0_40px_rgba(168,85,247,0.25)] animate-in fade-in zoom-in-95 duration-150">
            <div className="flex items-center justify-between border-b border-purple-500/20 pb-3">
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-purple-400" />
                Create New Community Discussion
              </h2>
              <button
                onClick={() => setCreateModalOpen(false)}
                type="button"
                className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-purple-900/40"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {createError && (
              <div className="p-3 rounded-xl bg-rose-950/30 border border-rose-500/40 text-xs text-rose-300">
                {createError}
              </div>
            )}

            <form onSubmit={handleCreatePost} className="space-y-4 text-xs">
              <div>
                <label className="block text-slate-300 font-mono mb-1">
                  Discussion Title (up to 120 chars)
                </label>
                <input
                  type="text"
                  maxLength={120}
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  placeholder="e.g. Why Frieren: Beyond Journey's End is a modern masterpiece..."
                  className="w-full px-3.5 py-2.5 rounded-xl bg-purple-950/40 border border-purple-500/30 text-white placeholder:text-slate-500 focus:outline-none focus:border-purple-400 text-xs sm:text-sm"
                />
              </div>

              <div>
                <label className="block text-slate-300 font-mono mb-1">
                  Post Content (up to 2000 chars)
                </label>
                <textarea
                  rows={5}
                  maxLength={2000}
                  value={newBody}
                  onChange={(e) => setNewBody(e.target.value)}
                  placeholder="Share your thoughts, episode analysis, or questions for fellow anime fans..."
                  className="w-full px-3.5 py-2.5 rounded-xl bg-purple-950/40 border border-purple-500/30 text-white placeholder:text-slate-500 focus:outline-none focus:border-purple-400 text-xs sm:text-sm leading-relaxed"
                />
                <div className="text-right text-[10px] font-mono text-slate-400 mt-1">
                  {newBody.length} / 2000 characters
                </div>
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <button
                  onClick={() => setCreateModalOpen(false)}
                  type="button"
                  className="px-4 py-2 rounded-xl bg-purple-950/40 hover:bg-purple-900/60 border border-purple-500/20 text-slate-300 font-medium cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={creating || !newTitle.trim() || !newBody.trim()}
                  className="px-5 py-2 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-semibold flex items-center gap-2 shadow-[0_0_15px_rgba(168,85,247,0.4)] disabled:opacity-40 cursor-pointer"
                >
                  {creating ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Send className="w-3.5 h-3.5" />}
                  <span>Publish Post</span>
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

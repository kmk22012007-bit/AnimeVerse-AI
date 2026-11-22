import React, { useState, useEffect } from 'react'
import { Link, useParams } from 'react-router-dom'
import {
  User,
  Shield,
  Eye,
  EyeOff,
  Edit3,
  Check,
  Star,
  Tv,
  CheckCircle2,
  Clock,
  Sparkles,
  BookOpen,
  Loader2,
  Heart,
  BarChart3,
  ArrowRight,
  SlidersHorizontal,
  X,
  RotateCcw,
  Info,
  Film,
  Users,
  UserPlus,
  UserCheck,
  MessageSquare,
} from 'lucide-react'
import {
  getCurrentProfile,
  updateProfile,
  getUserPreferences,
  updateUserPreferences,
  getUserTasteProfile,
  getPublicUserProfile,
  followUser,
  unfollowUser,
  getUserFollowers,
  getUserFollowing,
} from '../api/profile'

const AVAILABLE_GENRES = [
  'Action', 'Adventure', 'Comedy', 'Drama', 'Fantasy', 'Horror',
  'Mystery', 'Psychological', 'Romance', 'Sci-Fi', 'Shounen',
  'Slice of Life', 'Sports', 'Supernatural', 'Suspense', 'Award Winning'
]

const FORMAT_LIST = [
  { label: 'TV Series', value: 'tv' },
  { label: 'Movie', value: 'movie' },
  { label: 'OVA', value: 'ova' },
  { label: 'ONA', value: 'ona' },
  { label: 'Special', value: 'special' },
]

export const ProfilePage = () => {
  const { id } = useParams()
  const isViewingPublicUser = Boolean(id)

  const [profile, setProfile] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Follow State
  const [followLoading, setFollowLoading] = useState(false)
  const [followModalOpen, setFollowModalOpen] = useState(false)
  const [followModalType, setFollowModalType] = useState('followers') // 'followers' | 'following'
  const [followList, setFollowList] = useState([])
  const [followListLoading, setFollowListLoading] = useState(false)

  // Edit State
  const [editing, setEditing] = useState(false)
  const [displayName, setDisplayName] = useState('')
  const [bio, setBio] = useState('')
  const [isPublic, setIsPublic] = useState(true)
  const [saving, setSaving] = useState(false)
  const [saveSuccess, setSaveSuccess] = useState(false)

  // Taste Profile & Preferences States
  const [tasteProfile, setTasteProfile] = useState(null)
  const [preferences, setPreferences] = useState(null)
  const [editingPreferences, setEditingPreferences] = useState(false)
  const [prefSaving, setPrefSaving] = useState(false)
  const [prefSuccess, setPrefSuccess] = useState(false)
  const [prefError, setPrefError] = useState(null)

  // Draft Preference Controls State
  const [draftPrefs, setDraftPrefs] = useState({
    preferred_genres: [],
    excluded_genres: [],
    preferred_formats: [],
    recommendation_diversity: 'balanced',
    enable_personalized_recommendations: true,
    enable_dashboard_personalization: true,
    enable_discovery_personalization: true,
  })

  const fetchProfile = async () => {
    setLoading(true)
    setError(null)
    try {
      if (isViewingPublicUser) {
        const data = await getPublicUserProfile(id)
        setProfile(data)
        setDisplayName(data?.display_name || '')
        setBio(data?.bio || '')
        setIsPublic(Boolean(data?.is_public))
      } else {
        const data = await getCurrentProfile()
        setProfile(data)
        setDisplayName(data?.display_name || '')
        setBio(data?.bio || '')
        setIsPublic(Boolean(data?.is_public))
      }
    } catch (err) {
      setError(isViewingPublicUser ? 'Unable to load public user profile.' : 'Unable to load user profile data.')
    } finally {
      setLoading(false)
    }
  }

  const fetchTasteAndPreferences = async () => {
    if (isViewingPublicUser) return
    try {
      const [tp, prefs] = await Promise.all([
        getUserTasteProfile(),
        getUserPreferences(),
      ])
      setTasteProfile(tp)
      setPreferences(prefs)
      if (prefs) {
        setDraftPrefs({
          preferred_genres: prefs.preferred_genres || [],
          excluded_genres: prefs.excluded_genres || [],
          preferred_formats: prefs.preferred_formats || [],
          recommendation_diversity: prefs.recommendation_diversity || 'balanced',
          enable_personalized_recommendations: prefs.enable_personalized_recommendations ?? true,
          enable_dashboard_personalization: prefs.enable_dashboard_personalization ?? true,
          enable_discovery_personalization: prefs.enable_discovery_personalization ?? true,
        })
      }
    } catch (err) {
      console.debug('Failed loading taste profile or preferences:', err)
    }
  }

  useEffect(() => {
    fetchProfile()
    if (!isViewingPublicUser) {
      fetchTasteAndPreferences()
    }
  }, [id])

  const handleToggleFollow = async () => {
    if (!profile || profile.is_self) return
    setFollowLoading(true)
    try {
      if (profile.is_following) {
        const res = await unfollowUser(profile.id)
        setProfile((prev) => ({
          ...prev,
          is_following: false,
          follower_count: res.follower_count,
        }))
      } else {
        const res = await followUser(profile.id)
        setProfile((prev) => ({
          ...prev,
          is_following: true,
          follower_count: res.follower_count,
        }))
      }
    } catch (err) {
      console.error('Follow action failed:', err)
    } finally {
      setFollowLoading(false)
    }
  }

  const openFollowModal = async (type) => {
    setFollowModalType(type)
    setFollowModalOpen(true)
    setFollowListLoading(true)
    try {
      const targetId = isViewingPublicUser ? id : profile?.id
      const res =
        type === 'followers'
          ? await getUserFollowers(targetId)
          : await getUserFollowing(targetId)
      setFollowList(res?.results || [])
    } catch (err) {
      console.error('Failed to load followers/following:', err)
      setFollowList([])
    } finally {
      setFollowListLoading(false)
    }
  }

  const handleToggleFollowInModal = async (u) => {
    try {
      if (u.is_following) {
        await unfollowUser(u.id)
        setFollowList((prev) =>
          prev.map((item) => (item.id === u.id ? { ...item, is_following: false } : item))
        )
        if (!isViewingPublicUser) {
          setProfile((prev) => ({
            ...prev,
            following_count: Math.max(0, (prev.following_count || 1) - 1),
          }))
        }
      } else {
        await followUser(u.id)
        setFollowList((prev) =>
          prev.map((item) => (item.id === u.id ? { ...item, is_following: true } : item))
        )
        if (!isViewingPublicUser) {
          setProfile((prev) => ({
            ...prev,
            following_count: (prev.following_count || 0) + 1,
          }))
        }
      }
    } catch (err) {
      console.error('Modal follow toggle failed:', err)
    }
  }

  const handleSavePreferences = async (e) => {
    e?.preventDefault?.()
    setPrefSaving(true)
    setPrefSuccess(false)
    setPrefError(null)
    try {
      const updated = await updateUserPreferences(draftPrefs)
      setPreferences(updated)
      // Refresh taste profile to reflect explicit preferences changes
      const tp = await getUserTasteProfile()
      setTasteProfile(tp)
      setEditingPreferences(false)
      setPrefSuccess(true)
      setTimeout(() => setPrefSuccess(false), 3000)
    } catch (err) {
      setPrefError('Failed to save personalization preferences.')
    } finally {
      setPrefSaving(false)
    }
  }

  const toggleDraftPreferredGenre = (genre) => {
    setDraftPrefs((prev) => {
      const current = prev.preferred_genres || []
      const isIncluded = current.includes(genre)
      const nextPreferred = isIncluded
        ? current.filter((g) => g !== genre)
        : [...current, genre]
      // If adding to preferred, remove from excluded
      const nextExcluded = (prev.excluded_genres || []).filter((g) => g !== genre)
      return { ...prev, preferred_genres: nextPreferred, excluded_genres: nextExcluded }
    })
  }

  const toggleDraftExcludedGenre = (genre) => {
    setDraftPrefs((prev) => {
      const current = prev.excluded_genres || []
      const isExcluded = current.includes(genre)
      const nextExcluded = isExcluded
        ? current.filter((g) => g !== genre)
        : [...current, genre]
      // If adding to excluded, remove from preferred
      const nextPreferred = (prev.preferred_genres || []).filter((g) => g !== genre)
      return { ...prev, excluded_genres: nextExcluded, preferred_genres: nextPreferred }
    })
  }

  const toggleDraftFormat = (fmt) => {
    setDraftPrefs((prev) => {
      const current = prev.preferred_formats || []
      const exists = current.includes(fmt)
      return {
        ...prev,
        preferred_formats: exists
          ? current.filter((f) => f !== fmt)
          : [...current, fmt],
      }
    })
  }

  const handleSaveProfile = async (e) => {
    e.preventDefault()
    setSaving(true)
    setSaveSuccess(false)
    try {
      const updated = await updateProfile({
        display_name: displayName.trim(),
        bio: bio.trim(),
        is_public: isPublic,
      })
      setProfile(updated)
      setEditing(false)
      setSaveSuccess(true)
      setTimeout(() => setSaveSuccess(false), 3000)
    } catch (err) {
      setError('Failed to update profile settings.')
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <div className="p-16 text-center text-xs font-mono text-purple-300">
        Loading user profile and personal statistics...
      </div>
    )
  }

  if (error || !profile) {
    return (
      <div className="p-8 rounded-2xl bg-rose-950/20 border border-rose-500/20 text-center text-rose-300 text-xs font-mono">
        {error || 'Profile not found.'}
      </div>
    )
  }

  const stats = profile.stats || {}
  const statusCounts = profile.status_counts || {}
  const recent = profile.recent_activity || []
  const favorites = profile.favorites || []

  return (
    <div className="space-y-8 max-w-5xl mx-auto">
      {/* Header Banner Card */}
      <div className="relative rounded-3xl bg-[#0c0e1e] border border-purple-500/30 p-6 sm:p-8 shadow-[0_0_35px_rgba(168,85,247,0.15)] overflow-hidden">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6">
          <div className="flex items-center gap-4 sm:gap-5">
            {/* Avatar */}
            <div className="w-16 sm:w-20 aspect-square rounded-2xl bg-gradient-to-tr from-purple-600 via-indigo-600 to-cyan-500 p-0.5 shadow-[0_0_20px_rgba(168,85,247,0.4)] flex-shrink-0">
              <div className="w-full h-full bg-[#0c0e1e] rounded-[14px] flex items-center justify-center text-white text-2xl font-bold">
                {profile.display_name?.charAt(0)?.toUpperCase() || 'U'}
              </div>
            </div>

            {/* Display Name & Info */}
            <div>
              <div className="flex items-center gap-2.5">
                <h1 className="text-xl sm:text-2xl font-extrabold text-white">
                  {profile.display_name}
                </h1>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-cyan-500/20 text-cyan-300 border border-cyan-400/40">
                  {isViewingPublicUser && !profile.is_self ? 'AnimeVerse User' : 'Demo Session'}
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-1 font-mono">
                Member since {new Date(profile.joined_at).toLocaleDateString()}
              </p>
              <div className="flex items-center gap-2 mt-2">
                {profile.is_public ? (
                  <span className="inline-flex items-center gap-1 text-[11px] font-mono text-emerald-400">
                    <Eye className="w-3 h-3" /> Public Profile
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1 text-[11px] font-mono text-amber-400">
                    <EyeOff className="w-3 h-3" /> Private Profile
                  </span>
                )}
              </div>

              {/* Followers & Following Counters */}
              <div className="flex items-center gap-3 mt-3">
                <button
                  type="button"
                  onClick={() => openFollowModal('followers')}
                  className="inline-flex items-center gap-1.5 px-3 py-1 rounded-xl bg-purple-950/40 hover:bg-purple-900/50 border border-purple-500/20 text-xs font-mono text-purple-200 transition cursor-pointer"
                >
                  <Users className="w-3.5 h-3.5 text-purple-400" />
                  <span className="font-bold text-white">{profile.follower_count || 0}</span>
                  <span className="text-slate-400">Followers</span>
                </button>

                <button
                  type="button"
                  onClick={() => openFollowModal('following')}
                  className="inline-flex items-center gap-1.5 px-3 py-1 rounded-xl bg-purple-950/40 hover:bg-purple-900/50 border border-purple-500/20 text-xs font-mono text-purple-200 transition cursor-pointer"
                >
                  <UserCheck className="w-3.5 h-3.5 text-cyan-400" />
                  <span className="font-bold text-white">{profile.following_count || 0}</span>
                  <span className="text-slate-400">Following</span>
                </button>
              </div>
            </div>
          </div>

          {isViewingPublicUser && !profile.is_self ? (
            <button
              onClick={handleToggleFollow}
              disabled={followLoading}
              type="button"
              className={`inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs font-mono font-semibold transition-all shadow-lg cursor-pointer self-start sm:self-auto ${
                profile.is_following
                  ? 'bg-slate-800 hover:bg-rose-950/60 hover:text-rose-300 text-purple-200 border border-purple-500/30'
                  : 'bg-purple-600 hover:bg-purple-500 text-white shadow-purple-600/40'
              }`}
            >
              {followLoading ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
              ) : profile.is_following ? (
                <>
                  <UserCheck className="w-3.5 h-3.5 text-emerald-400" />
                  <span>Following</span>
                </>
              ) : (
                <>
                  <UserPlus className="w-3.5 h-3.5" />
                  <span>Follow User</span>
                </>
              )}
            </button>
          ) : (
            <button
              onClick={() => setEditing((prev) => !prev)}
              type="button"
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-purple-950/60 hover:bg-purple-900/60 border border-purple-500/30 text-xs font-mono text-purple-200 transition-colors cursor-pointer self-start sm:self-auto"
            >
              <Edit3 className="w-3.5 h-3.5" />
              <span>{editing ? 'Cancel' : 'Edit Profile'}</span>
            </button>
          )}
        </div>

        {/* Bio Preview (When not editing) */}
        {!editing && profile.bio && (
          <p className="text-xs sm:text-sm text-slate-300 mt-5 pt-4 border-t border-purple-950/80 leading-relaxed font-sans max-w-2xl">
            {profile.bio}
          </p>
        )}

        {saveSuccess && (
          <div className="mt-4 p-2.5 rounded-xl bg-emerald-950/40 border border-emerald-500/40 text-emerald-300 text-xs font-mono flex items-center gap-2">
            <Check className="w-4 h-4 text-emerald-400" />
            <span>Profile successfully updated!</span>
          </div>
        )}

        {/* Editable Profile Form */}
        {editing && (
          <form onSubmit={handleSaveProfile} className="mt-6 pt-5 border-t border-purple-500/20 space-y-4 text-xs">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-slate-300 font-mono mb-1">Display Name</label>
                <input
                  type="text"
                  maxLength={50}
                  value={displayName}
                  onChange={(e) => setDisplayName(e.target.value)}
                  className="w-full px-3.5 py-2.5 rounded-xl bg-purple-950/40 border border-purple-500/30 text-white placeholder:text-slate-500 focus:outline-none focus:border-purple-400 text-xs sm:text-sm"
                  required
                />
              </div>

              <div>
                <label className="block text-slate-300 font-mono mb-1">Privacy Preference</label>
                <div className="flex items-center gap-3 pt-2">
                  <label className="inline-flex items-center gap-2 text-slate-300 cursor-pointer">
                    <input
                      type="radio"
                      checked={isPublic}
                      onChange={() => setIsPublic(true)}
                      className="accent-purple-500"
                    />
                    <span>Public Profile</span>
                  </label>
                  <label className="inline-flex items-center gap-2 text-slate-300 cursor-pointer">
                    <input
                      type="radio"
                      checked={!isPublic}
                      onChange={() => setIsPublic(false)}
                      className="accent-purple-500"
                    />
                    <span>Private Profile</span>
                  </label>
                </div>
              </div>
            </div>

            <div>
              <label className="block text-slate-300 font-mono mb-1">Bio Description</label>
              <textarea
                rows={3}
                maxLength={500}
                value={bio}
                onChange={(e) => setBio(e.target.value)}
                placeholder="Tell other anime fans about your favorite genres, studios, or anime journey..."
                className="w-full px-3.5 py-2.5 rounded-xl bg-purple-950/40 border border-purple-500/30 text-white placeholder:text-slate-500 focus:outline-none focus:border-purple-400 text-xs sm:text-sm leading-relaxed"
              />
            </div>

            <div className="flex justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={() => setEditing(false)}
                className="px-4 py-2 rounded-xl bg-purple-950/40 border border-purple-500/20 text-slate-300 font-medium cursor-pointer"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={saving || !displayName.trim()}
                className="px-5 py-2 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-semibold flex items-center gap-2 shadow-[0_0_15px_rgba(168,85,247,0.4)] disabled:opacity-40 cursor-pointer"
              >
                {saving ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Check className="w-3.5 h-3.5" />}
                <span>Save Profile Changes</span>
              </button>
            </div>
          </form>
        )}
      </div>

      {/* Conditional: Viewing Public Profile of another user vs Own Profile */}
      {isViewingPublicUser && !profile.is_self ? (
        <div className="space-y-8">
          {/* Public Anime Stats & Favorite Genres */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="p-4 rounded-2xl bg-[#0c0e1e] border border-purple-500/25 space-y-1">
              <span className="text-[10px] font-mono uppercase text-slate-400">Completed Anime</span>
              <div className="text-xl sm:text-2xl font-black text-cyan-400">{stats.completed_count || 0}</div>
              <span className="text-[10px] font-mono text-cyan-300">Finished titles</span>
            </div>

            <div className="p-4 rounded-2xl bg-[#0c0e1e] border border-purple-500/25 space-y-1">
              <span className="text-[10px] font-mono uppercase text-slate-400">Episodes Watched</span>
              <div className="text-xl sm:text-2xl font-black text-purple-300">{stats.total_episodes_watched || 0}</div>
              <span className="text-[10px] font-mono text-purple-400">Total episode milestones</span>
            </div>

            <div className="p-4 rounded-2xl bg-[#0c0e1e] border border-purple-500/25 space-y-1">
              <span className="text-[10px] font-mono uppercase text-slate-400">Mean Score</span>
              <div className="text-xl sm:text-2xl font-black text-amber-400 flex items-center gap-1">
                <Star className="w-4 h-4 fill-amber-400" />
                {stats.average_rating || 'N/A'}
              </div>
              <span className="text-[10px] font-mono text-amber-300/80">User review rating average</span>
            </div>
          </div>

          {/* Favorite Genres Card */}
          {profile.favorite_genres && profile.favorite_genres.length > 0 && (
            <div className="rounded-2xl bg-[#0c0e1e] border border-purple-500/25 p-5 space-y-3">
              <div className="flex items-center gap-2 text-xs font-mono uppercase text-slate-400">
                <Sparkles className="w-4 h-4 text-cyan-400" />
                <span>Favorite Anime Genres</span>
              </div>
              <div className="flex flex-wrap gap-2">
                {profile.favorite_genres.map((genre) => (
                  <span
                    key={genre}
                    className="px-3 py-1 rounded-xl bg-purple-950/60 border border-purple-500/30 text-purple-200 text-xs font-mono"
                  >
                    {genre}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Community Activity Summary */}
          <div className="rounded-3xl bg-[#0c0e1e] border border-purple-500/30 p-6 sm:p-8 shadow-[0_0_35px_rgba(168,85,247,0.15)] space-y-6">
            <div className="flex items-center gap-3 pb-4 border-b border-purple-500/20">
              <div className="p-2.5 rounded-xl bg-purple-500/10 border border-purple-500/20 text-purple-400">
                <MessageSquare className="w-5 h-5 text-purple-400" />
              </div>
              <div>
                <h3 className="text-base font-bold text-white">Community & Social Activity</h3>
                <p className="text-xs text-slate-400">Discussions, comments, and reviews authored by this user</p>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div className="p-3.5 rounded-2xl bg-purple-950/30 border border-purple-500/20 text-center space-y-1">
                <div className="text-lg sm:text-xl font-bold text-white">{profile.community_activity?.posts_count || 0}</div>
                <div className="text-[11px] font-mono text-slate-400">Discussions</div>
              </div>
              <div className="p-3.5 rounded-2xl bg-purple-950/30 border border-purple-500/20 text-center space-y-1">
                <div className="text-lg sm:text-xl font-bold text-cyan-300">{profile.community_activity?.comments_count || 0}</div>
                <div className="text-[11px] font-mono text-slate-400">Comments</div>
              </div>
              <div className="p-3.5 rounded-2xl bg-purple-950/30 border border-purple-500/20 text-center space-y-1">
                <div className="text-lg sm:text-xl font-bold text-amber-300">{profile.community_activity?.reviews_count || 0}</div>
                <div className="text-[11px] font-mono text-slate-400">Reviews</div>
              </div>
            </div>

            {/* Recent Discussions List */}
            {profile.recent_posts && profile.recent_posts.length > 0 && (
              <div className="space-y-3 pt-2">
                <h4 className="text-xs font-mono uppercase text-slate-400">Recent Discussions</h4>
                <div className="space-y-2.5">
                  {profile.recent_posts.map((p) => (
                    <Link
                      key={p.id}
                      to={`/community?post=${p.id}`}
                      className="p-3.5 rounded-2xl bg-slate-900/60 border border-purple-900/30 hover:border-purple-500/50 flex items-center justify-between gap-4 transition group"
                    >
                      <div className="min-w-0">
                        <div className="text-sm font-semibold text-slate-100 group-hover:text-purple-300 transition truncate">
                          {p.title}
                        </div>
                        <div className="flex items-center gap-2 text-[11px] text-slate-500 mt-1 font-mono">
                          <span className="capitalize text-purple-400">{p.category}</span>
                          <span>•</span>
                          <span>{new Date(p.created_at).toLocaleDateString()}</span>
                        </div>
                      </div>
                      <div className="flex items-center gap-3 text-xs text-slate-400 flex-shrink-0 font-mono">
                        <span className="flex items-center gap-1">
                          <Heart className="w-3.5 h-3.5 text-rose-400" />
                          {p.like_count}
                        </span>
                        <span className="flex items-center gap-1">
                          <MessageSquare className="w-3.5 h-3.5 text-cyan-400" />
                          {p.comment_count}
                        </span>
                      </div>
                    </Link>
                  ))}
                </div>
              </div>
            )}

            {/* Recent Reviews List */}
            {profile.reviews && profile.reviews.length > 0 && (
              <div className="space-y-3 pt-2">
                <h4 className="text-xs font-mono uppercase text-slate-400">Recent Reviews</h4>
                <div className="space-y-2.5">
                  {profile.reviews.slice(0, 5).map((r) => (
                    <Link
                      key={r.id}
                      to={`/anime/${r.anime_mal_id}`}
                      className="p-3.5 rounded-2xl bg-slate-900/60 border border-purple-900/30 hover:border-purple-500/50 block transition group"
                    >
                      <div className="flex items-center justify-between text-xs mb-1">
                        <span className="text-amber-400 font-bold flex items-center gap-1 font-mono">
                          <Star className="w-3.5 h-3.5 fill-amber-400" />
                          {r.score}/10
                        </span>
                        <span className="text-slate-500 text-[10px] font-mono">
                          {new Date(r.created_at).toLocaleDateString()}
                        </span>
                      </div>
                      <p className="text-xs text-slate-300 line-clamp-2 leading-relaxed">
                        {r.body}
                      </p>
                    </Link>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      ) : (
        <>
          {/* Numerical Stats Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="p-4 rounded-2xl bg-[#0c0e1e] border border-purple-500/25 space-y-1">
          <span className="text-[10px] font-mono uppercase text-slate-400">Total Tracked</span>
          <div className="text-xl sm:text-2xl font-black text-white">{stats.total_anime || 0}</div>
          <span className="text-[10px] font-mono text-purple-300">Anime titles in list</span>
        </div>

        <div className="p-4 rounded-2xl bg-[#0c0e1e] border border-purple-500/25 space-y-1">
          <span className="text-[10px] font-mono uppercase text-slate-400">Completed</span>
          <div className="text-xl sm:text-2xl font-black text-cyan-400">{stats.completed_count || 0}</div>
          <span className="text-[10px] font-mono text-cyan-300">Series finished</span>
        </div>

        <div className="p-4 rounded-2xl bg-[#0c0e1e] border border-purple-500/25 space-y-1">
          <span className="text-[10px] font-mono uppercase text-slate-400">Episodes Watched</span>
          <div className="text-xl sm:text-2xl font-black text-purple-300">{stats.total_episodes_watched || 0}</div>
          <span className="text-[10px] font-mono text-purple-400">Total ep milestones</span>
        </div>

        <div className="p-4 rounded-2xl bg-[#0c0e1e] border border-purple-500/25 space-y-1">
          <span className="text-[10px] font-mono uppercase text-slate-400">Mean Score</span>
          <div className="text-xl sm:text-2xl font-black text-amber-400 flex items-center gap-1">
            <Star className="w-4 h-4 fill-amber-400" />
            {stats.average_rating}
          </div>
          <span className="text-[10px] font-mono text-amber-300/80">Personal 1-10 average</span>
        </div>
      </div>

      {/* Advanced Analytics Shortcut Banner */}
      <div className="p-5 rounded-2xl bg-gradient-to-r from-purple-950/40 via-indigo-950/40 to-[#0c0e1e] border border-purple-500/30 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 shadow-[0_0_20px_rgba(168,85,247,0.1)]">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-purple-500/10 border border-purple-500/20 text-purple-400">
            <BarChart3 className="w-5 h-5 text-purple-400" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              Advanced Personal Analytics
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-cyan-500/20 text-cyan-300 border border-cyan-400/30">Live</span>
            </h3>
            <p className="text-xs text-slate-400 font-sans mt-0.5">
              Explore your genre distribution, rating analytics, completion rate, and viewing activity timeline.
            </p>
          </div>
        </div>
        <Link
          to="/analytics"
          className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-purple-600 hover:bg-purple-500 text-white text-xs font-mono font-semibold transition-all shadow-[0_0_15px_rgba(168,85,247,0.3)] hover:shadow-[0_0_20px_rgba(168,85,247,0.5)] shrink-0"
        >
          <span>View Analytics</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      </div>

      {/* ======================================================== */}
      {/* PERSONAL ANIME TASTE PROFILE & PREFERENCES CONTROLS      */}
      {/* ======================================================== */}
      <div className="rounded-3xl bg-[#0c0e1e] border border-purple-500/30 p-6 sm:p-8 shadow-[0_0_35px_rgba(168,85,247,0.15)] space-y-6">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-4 border-b border-purple-500/20">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-gradient-to-tr from-purple-600 to-indigo-600 text-white shadow-[0_0_15px_rgba(168,85,247,0.4)]">
              <Sparkles className="w-5 h-5 text-cyan-300" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                Personal Anime Taste Profile
                <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-cyan-500/20 text-cyan-300 border border-cyan-400/30">
                  Algorithmic Intelligence
                </span>
              </h2>
              <p className="text-xs text-slate-400">
                Separating behavioral inferred signals from explicit configured preferences
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={() => setEditingPreferences((prev) => !prev)}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-purple-950/60 hover:bg-purple-900/60 border border-purple-500/30 text-xs font-mono text-purple-200 transition-colors cursor-pointer self-start sm:self-auto"
          >
            <SlidersHorizontal className="w-3.5 h-3.5 text-cyan-400" />
            <span>{editingPreferences ? 'Hide Controls' : 'Edit Preferences'}</span>
          </button>
        </div>

        {prefSuccess && (
          <div className="p-3 rounded-xl bg-emerald-950/40 border border-emerald-500/40 text-emerald-300 text-xs font-mono flex items-center gap-2">
            <Check className="w-4 h-4 text-emerald-400" />
            <span>Personalization preferences updated and active across AnimeVerse!</span>
          </div>
        )}

        {prefError && (
          <div className="p-3 rounded-xl bg-rose-950/40 border border-rose-500/40 text-rose-300 text-xs font-mono flex items-center gap-2">
            <X className="w-4 h-4 text-rose-400" />
            <span>{prefError}</span>
          </div>
        )}

        {/* Taste Summary Banner */}
        {tasteProfile && (
          <div className="p-4 rounded-2xl bg-gradient-to-r from-purple-950/40 via-indigo-950/30 to-[#0c0e1e] border border-purple-500/25 space-y-2">
            <div className="flex items-center gap-2 text-xs font-mono text-purple-300 uppercase tracking-wider">
              <Info className="w-3.5 h-3.5 text-cyan-400" />
              <span>Grounded Taste Summary</span>
            </div>
            <p className="text-xs sm:text-sm text-slate-200 font-sans leading-relaxed">
              {tasteProfile.taste_summary}
            </p>
            {!tasteProfile.has_sufficient_history && (
              <p className="text-[11px] font-mono text-amber-300/90 pt-1">
                ⚡ Profiling note: Rating or tracking at least 3 anime series sharpens algorithmic confidence.
              </p>
            )}
          </div>
        )}

        {/* Inferred Activity Signals vs Explicit Overrides */}
        {tasteProfile && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Left: Inferred Taste Signals */}
            <div className="p-5 rounded-2xl bg-purple-950/20 border border-purple-500/20 space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono uppercase tracking-wider text-cyan-300 font-bold flex items-center gap-1.5">
                  <Sparkles className="w-3.5 h-3.5" /> Inferred Signals (Activity-Based)
                </span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-cyan-950 text-cyan-300 border border-cyan-500/30">
                  Telemetry
                </span>
              </div>

              {/* Rating Tendency & Completion Rate */}
              <div className="grid grid-cols-2 gap-3 text-xs font-mono">
                <div className="p-3 rounded-xl bg-[#0c0e1e] border border-purple-500/15">
                  <span className="text-[10px] text-slate-400 block">Rating Style</span>
                  <span className="text-sm font-bold text-amber-400 block mt-0.5">
                    {tasteProfile.rating_tendency?.label || 'Calibrating'}
                  </span>
                  <span className="text-[10px] text-slate-500">
                    {tasteProfile.rating_tendency?.rated_count > 0
                      ? `avg ${tasteProfile.rating_tendency.average_rating}/10`
                      : 'No rated anime'}
                  </span>
                </div>

                <div className="p-3 rounded-xl bg-[#0c0e1e] border border-purple-500/15">
                  <span className="text-[10px] text-slate-400 block">Completion Rate</span>
                  <span className="text-sm font-bold text-emerald-400 block mt-0.5">
                    {tasteProfile.completion_rate_pct}%
                  </span>
                  <span className="text-[10px] text-slate-500">
                    {tasteProfile.completed_count} completed / {tasteProfile.tracked_count} tracked
                  </span>
                </div>
              </div>

              {/* Inferred Top Genres */}
              <div className="space-y-2">
                <span className="text-[11px] font-mono text-slate-300 block">
                  Top Inferred Genres (with viewing evidence):
                </span>
                {tasteProfile.top_inferred_genres?.length > 0 ? (
                  <div className="flex flex-wrap gap-2">
                    {tasteProfile.top_inferred_genres.map((g) => (
                      <span
                        key={g.name}
                        className="px-2.5 py-1 rounded-lg bg-[#0c0e1e] border border-purple-500/30 text-purple-200 text-xs font-mono flex items-center gap-1.5"
                        title={g.evidence}
                      >
                        <span className="font-semibold text-white">{g.name}</span>
                        <span className="text-[10px] text-cyan-300 font-bold">
                          {g.count} titles
                        </span>
                        {g.avg_rating && (
                          <span className="text-[10px] text-amber-300">
                            ★{g.avg_rating}
                          </span>
                        )}
                      </span>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-slate-400 font-mono italic">
                    No genres inferred yet. Start tracking anime to populate affinity signals.
                  </p>
                )}
              </div>

              {/* Inferred Top Studios */}
              <div className="space-y-2">
                <span className="text-[11px] font-mono text-slate-300 block">
                  Top Inferred Studios:
                </span>
                {tasteProfile.top_inferred_studios?.length > 0 ? (
                  <div className="flex flex-wrap gap-2">
                    {tasteProfile.top_inferred_studios.map((s) => (
                      <span
                        key={s.name}
                        className="px-2.5 py-1 rounded-lg bg-[#0c0e1e] border border-purple-500/30 text-slate-300 text-xs font-mono flex items-center gap-1.5"
                        title={s.evidence}
                      >
                        <Film className="w-3 h-3 text-purple-400" />
                        <span>{s.name}</span>
                        <span className="text-[10px] text-cyan-300">({s.count})</span>
                      </span>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-slate-400 font-mono italic">
                    Studio preferences will appear as you complete anime series.
                  </p>
                )}
              </div>
            </div>

            {/* Right: Explicit Overrides & Current Configuration */}
            <div className="p-5 rounded-2xl bg-purple-950/20 border border-purple-500/20 space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono uppercase tracking-wider text-purple-300 font-bold flex items-center gap-1.5">
                  <SlidersHorizontal className="w-3.5 h-3.5" /> Explicit Preferences (User Defined)
                </span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-purple-950 text-purple-300 border border-purple-500/30">
                  Custom
                </span>
              </div>

              {/* Preferred Genres */}
              <div className="space-y-1.5">
                <span className="text-[11px] font-mono text-slate-300 block">
                  Explicitly Preferred Genres:
                </span>
                {preferences?.preferred_genres?.length > 0 ? (
                  <div className="flex flex-wrap gap-1.5">
                    {preferences.preferred_genres.map((g) => (
                      <span
                        key={g}
                        className="px-2.5 py-1 rounded-lg bg-emerald-950/50 border border-emerald-500/40 text-emerald-300 text-xs font-mono"
                      >
                        +{g}
                      </span>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-slate-400 font-mono italic">
                    No preferred genres pinned. Algorithmic discovery uses your inferred tastes.
                  </p>
                )}
              </div>

              {/* Excluded Genres */}
              <div className="space-y-1.5">
                <span className="text-[11px] font-mono text-slate-300 block">
                  Excluded Genres (Strict Filter):
                </span>
                {preferences?.excluded_genres?.length > 0 ? (
                  <div className="flex flex-wrap gap-1.5">
                    {preferences.excluded_genres.map((eg) => (
                      <span
                        key={eg}
                        className="px-2.5 py-1 rounded-lg bg-rose-950/50 border border-rose-500/40 text-rose-300 text-xs font-mono line-through"
                      >
                        -{eg}
                      </span>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-slate-400 font-mono italic">
                    No genres excluded.
                  </p>
                )}
              </div>

              {/* Formats & Diversity */}
              <div className="grid grid-cols-2 gap-3 text-xs font-mono pt-2 border-t border-purple-500/15">
                <div>
                  <span className="text-[10px] text-slate-400 block">Diversity Level</span>
                  <span className="text-xs font-bold text-cyan-300 capitalize">
                    {preferences?.recommendation_diversity || 'Balanced'}
                  </span>
                </div>
                <div>
                  <span className="text-[10px] text-slate-400 block">Recommendation Engine</span>
                  <span className={`text-xs font-bold ${preferences?.enable_personalized_recommendations ? 'text-emerald-400' : 'text-amber-400'}`}>
                    {preferences?.enable_personalized_recommendations ? 'Active (Smart)' : 'Standard (Popular)'}
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Interactive Preferences Editor */}
        {editingPreferences && (
          <form
            onSubmit={handleSavePreferences}
            className="p-5 rounded-2xl bg-purple-950/30 border border-purple-500/35 space-y-6 text-xs transition-all"
          >
            <div className="flex items-center justify-between border-b border-purple-500/20 pb-3">
              <span className="font-bold text-white text-sm flex items-center gap-2">
                <SlidersHorizontal className="w-4 h-4 text-purple-400" /> Personalization Configuration Panel
              </span>
              <button
                type="button"
                onClick={() => setEditingPreferences(false)}
                className="text-slate-400 hover:text-white cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Feature Toggles */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <label className="p-3 rounded-xl bg-[#0c0e1e] border border-purple-500/20 flex items-start gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={draftPrefs.enable_personalized_recommendations}
                  onChange={(e) =>
                    setDraftPrefs((prev) => ({
                      ...prev,
                      enable_personalized_recommendations: e.target.checked,
                    }))
                  }
                  className="mt-0.5 accent-purple-500 cursor-pointer"
                />
                <div>
                  <span className="font-bold text-white block">Smart Recommendations</span>
                  <span className="text-[11px] text-slate-400 font-mono">
                    Tailors RYUK and carousel suggestions to your taste profile
                  </span>
                </div>
              </label>

              <label className="p-3 rounded-xl bg-[#0c0e1e] border border-purple-500/20 flex items-start gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={draftPrefs.enable_dashboard_personalization}
                  onChange={(e) =>
                    setDraftPrefs((prev) => ({
                      ...prev,
                      enable_dashboard_personalization: e.target.checked,
                    }))
                  }
                  className="mt-0.5 accent-purple-500 cursor-pointer"
                />
                <div>
                  <span className="font-bold text-white block">Dashboard Personalization</span>
                  <span className="text-[11px] text-slate-400 font-mono">
                    Surfaces "Because You Watched" and journey metrics
                  </span>
                </div>
              </label>

              <label className="p-3 rounded-xl bg-[#0c0e1e] border border-purple-500/20 flex items-start gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={draftPrefs.enable_discovery_personalization}
                  onChange={(e) =>
                    setDraftPrefs((prev) => ({
                      ...prev,
                      enable_discovery_personalization: e.target.checked,
                    }))
                  }
                  className="mt-0.5 accent-purple-500 cursor-pointer"
                />
                <div>
                  <span className="font-bold text-white block">Discovery Personalization</span>
                  <span className="text-[11px] text-slate-400 font-mono">
                    Prioritizes your preferred genres in catalog browse
                  </span>
                </div>
              </label>
            </div>

            {/* Recommendation Diversity */}
            <div className="space-y-2">
              <label className="block text-slate-300 font-mono text-[11px] font-semibold uppercase tracking-wider">
                Recommendation Diversity Level
              </label>
              <div className="grid grid-cols-3 gap-3">
                {[
                  { key: 'focused', title: 'Focused (Strict)', desc: 'Strictly match your established taste profile' },
                  { key: 'balanced', title: 'Balanced (Recommended)', desc: 'Healthy balance of comfort zone & fresh discoveries' },
                  { key: 'exploratory', title: 'Exploratory (Diverse)', desc: 'Explore diverse genres, niche studios & hidden gems' },
                ].map((d) => (
                  <button
                    key={d.key}
                    type="button"
                    onClick={() => setDraftPrefs((prev) => ({ ...prev, recommendation_diversity: d.key }))}
                    className={`p-3 rounded-xl text-left transition-all cursor-pointer ${
                      draftPrefs.recommendation_diversity === d.key
                        ? 'bg-purple-600/30 border-purple-400 border text-white shadow-[0_0_15px_rgba(168,85,247,0.3)]'
                        : 'bg-[#0c0e1e] border border-purple-500/15 text-slate-400 hover:text-white'
                    }`}
                  >
                    <span className="font-bold block text-xs">{d.title}</span>
                    <span className="text-[10px] text-slate-400 font-mono mt-0.5 block">{d.desc}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Preferred Genres Selection */}
            <div className="space-y-2">
              <label className="block text-slate-300 font-mono text-[11px] font-semibold uppercase tracking-wider">
                Preferred Genres (Boosted in Catalog & AI Recommendations)
              </label>
              <div className="flex flex-wrap gap-1.5">
                {AVAILABLE_GENRES.map((genre) => {
                  const isSelected = (draftPrefs.preferred_genres || []).includes(genre)
                  return (
                    <button
                      key={`pref-${genre}`}
                      type="button"
                      onClick={() => toggleDraftPreferredGenre(genre)}
                      className={`px-2.5 py-1 rounded-lg text-xs font-mono transition-all cursor-pointer flex items-center gap-1 ${
                        isSelected
                          ? 'bg-emerald-600 text-white font-semibold border border-emerald-400 shadow-[0_0_10px_rgba(16,185,129,0.3)]'
                          : 'bg-[#0c0e1e] text-slate-400 border border-purple-500/20 hover:text-white'
                      }`}
                    >
                      <span>{genre}</span>
                      {isSelected && <Check className="w-3 h-3 text-white" />}
                    </button>
                  )
                })}
              </div>
            </div>

            {/* Excluded Genres Selection */}
            <div className="space-y-2">
              <label className="block text-slate-300 font-mono text-[11px] font-semibold uppercase tracking-wider">
                Excluded Genres (Strictly Filtered Out from Recommendations & Discovery)
              </label>
              <div className="flex flex-wrap gap-1.5">
                {AVAILABLE_GENRES.map((genre) => {
                  const isExcluded = (draftPrefs.excluded_genres || []).includes(genre)
                  return (
                    <button
                      key={`exc-${genre}`}
                      type="button"
                      onClick={() => toggleDraftExcludedGenre(genre)}
                      className={`px-2.5 py-1 rounded-lg text-xs font-mono transition-all cursor-pointer flex items-center gap-1 ${
                        isExcluded
                          ? 'bg-rose-600 text-white font-semibold border border-rose-400 shadow-[0_0_10px_rgba(244,63,94,0.3)] line-through'
                          : 'bg-[#0c0e1e] text-slate-400 border border-purple-500/20 hover:text-white'
                      }`}
                    >
                      <span>{genre}</span>
                      {isExcluded && <X className="w-3 h-3 text-white" />}
                    </button>
                  )
                })}
              </div>
            </div>

            {/* Preferred Formats */}
            <div className="space-y-2">
              <label className="block text-slate-300 font-mono text-[11px] font-semibold uppercase tracking-wider">
                Preferred Formats
              </label>
              <div className="flex flex-wrap gap-1.5">
                {FORMAT_LIST.map((fmt) => {
                  const isSelected = (draftPrefs.preferred_formats || []).includes(fmt.value)
                  return (
                    <button
                      key={`fmt-${fmt.value}`}
                      type="button"
                      onClick={() => toggleDraftFormat(fmt.value)}
                      className={`px-2.5 py-1 rounded-lg text-xs font-mono transition-all cursor-pointer flex items-center gap-1 ${
                        isSelected
                          ? 'bg-purple-600 text-white font-semibold border border-purple-400 shadow-[0_0_10px_rgba(168,85,247,0.3)]'
                          : 'bg-[#0c0e1e] text-slate-400 border border-purple-500/20 hover:text-white'
                      }`}
                    >
                      <span>{fmt.label}</span>
                      {isSelected && <Check className="w-3 h-3 text-white" />}
                    </button>
                  )
                })}
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex justify-end gap-3 pt-3 border-t border-purple-500/20">
              <button
                type="button"
                onClick={() => setEditingPreferences(false)}
                className="px-4 py-2 rounded-xl bg-purple-950/40 border border-purple-500/20 text-slate-300 font-medium cursor-pointer"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={prefSaving}
                className="px-5 py-2 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-semibold flex items-center gap-2 shadow-[0_0_15px_rgba(168,85,247,0.4)] disabled:opacity-40 cursor-pointer"
              >
                {prefSaving ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Check className="w-3.5 h-3.5" />}
                <span>Save Personalization Preferences</span>
              </button>
            </div>
          </form>
        )}
      </div>

      {/* Watchlist Status Distribution */}
      <div className="p-5 rounded-2xl bg-[#0c0e1e] border border-purple-500/25 space-y-3">
        <h3 className="text-xs font-mono uppercase text-purple-300 tracking-wider">
          Watchlist Status Breakdown
        </h3>
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 text-xs font-mono">
          <div className="p-2.5 rounded-xl bg-purple-950/40 border border-cyan-500/30 text-center">
            <span className="text-[10px] text-cyan-400 block font-semibold">Watching</span>
            <span className="text-base font-bold text-white">{statusCounts.watching || 0}</span>
          </div>
          <div className="p-2.5 rounded-xl bg-purple-950/40 border border-emerald-500/30 text-center">
            <span className="text-[10px] text-emerald-400 block font-semibold">Completed</span>
            <span className="text-base font-bold text-white">{statusCounts.completed || 0}</span>
          </div>
          <div className="p-2.5 rounded-xl bg-purple-950/40 border border-purple-500/30 text-center">
            <span className="text-[10px] text-purple-400 block font-semibold">Plan to Watch</span>
            <span className="text-base font-bold text-white">{statusCounts.plan_to_watch || 0}</span>
          </div>
          <div className="p-2.5 rounded-xl bg-purple-950/40 border border-amber-500/30 text-center">
            <span className="text-[10px] text-amber-400 block font-semibold">On Hold</span>
            <span className="text-base font-bold text-white">{statusCounts.on_hold || 0}</span>
          </div>
          <div className="p-2.5 rounded-xl bg-purple-950/40 border border-rose-500/30 text-center">
            <span className="text-[10px] text-rose-400 block font-semibold">Dropped</span>
            <span className="text-base font-bold text-white">{statusCounts.dropped || 0}</span>
          </div>
        </div>
      </div>

      {/* Favorite High-Rated Anime (>= 8/10) */}
      {favorites.length > 0 && (
        <section className="space-y-4">
          <h2 className="text-sm sm:text-base font-bold text-white tracking-wide flex items-center gap-2">
            <Heart className="w-4 h-4 text-rose-400 fill-rose-400" />
            Top Rated Favorites (Score 8+)
          </h2>

          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-3">
            {favorites.map((fav) => (
              <Link
                key={fav.id}
                to={`/anime/${fav.anime_id}`}
                className="p-2.5 rounded-2xl bg-[#0c0e1e] border border-purple-500/20 hover:border-purple-400 transition-all group flex flex-col justify-between"
              >
                <div className="aspect-[3/4] rounded-xl overflow-hidden bg-purple-950 mb-2 border border-purple-500/20">
                  {fav.poster_url ? (
                    <img
                      src={fav.poster_url}
                      alt={fav.title}
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center text-purple-400">
                      <Tv className="w-6 h-6" />
                    </div>
                  )}
                </div>
                <p className="text-xs font-semibold text-white truncate group-hover:text-purple-300">
                  {fav.title}
                </p>
                <div className="mt-1 flex items-center justify-between text-[10px] font-mono">
                  <span className="text-amber-400 font-bold flex items-center gap-0.5">
                    <Star className="w-2.5 h-2.5 fill-amber-400" /> {fav.rating}/10
                  </span>
                  <span className="text-purple-300">{fav.status}</span>
                </div>
              </Link>
            ))}
          </div>
        </section>
      )}

      {/* Recently Updated Watchlist Activity */}
      {recent.length > 0 && (
        <section className="space-y-4">
          <h2 className="text-sm sm:text-base font-bold text-white tracking-wide flex items-center gap-2">
            <Clock className="w-4 h-4 text-purple-400" />
            Recent Watchlist Activity
          </h2>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
            {recent.map((rec) => (
              <Link
                key={rec.id}
                to={`/anime/${rec.anime_id}`}
                className="p-3 rounded-2xl bg-[#0c0e1e] border border-purple-500/20 hover:border-purple-400/50 transition-all flex items-center gap-3 group"
              >
                <div className="w-12 h-16 rounded-xl overflow-hidden bg-purple-950 flex-shrink-0 border border-purple-500/20">
                  {rec.poster_url ? (
                    <img src={rec.poster_url} alt="" className="w-full h-full object-cover" />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center text-purple-400">
                      <Tv className="w-4 h-4" />
                    </div>
                  )}
                </div>

                <div className="min-w-0 flex-1">
                  <h4 className="text-xs font-bold text-white truncate group-hover:text-purple-300">
                    {rec.title}
                  </h4>
                  <p className="text-[10px] font-mono text-cyan-400 mt-0.5">
                    Progress: {rec.watched_episodes} / {rec.total_episodes || '??'} eps
                  </p>
                  <div className="flex items-center gap-2 mt-1 text-[10px] font-mono text-slate-400">
                    <span className="px-1.5 py-0.5 rounded bg-purple-950/80 border border-purple-500/20 text-purple-300">
                      {rec.status}
                    </span>
                    {rec.rating && <span className="text-amber-400">★ {rec.rating}/10</span>}
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </section>
      )}
        </>
      )}

      {/* Followers / Following Modal */}
      {followModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="w-full max-w-md rounded-3xl bg-[#0c0e1e] border border-purple-500/30 p-6 shadow-[0_0_50px_rgba(168,85,247,0.25)] space-y-4 max-h-[80vh] flex flex-col">
            <div className="flex items-center justify-between pb-3 border-b border-purple-900/30">
              <div className="flex items-center gap-2">
                {followModalType === 'followers' ? (
                  <Users className="w-5 h-5 text-purple-400" />
                ) : (
                  <UserCheck className="w-5 h-5 text-cyan-400" />
                )}
                <h3 className="text-sm font-bold text-white capitalize">
                  {followModalType} ({followList.length})
                </h3>
              </div>
              <button
                onClick={() => setFollowModalOpen(false)}
                className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-purple-950/40 transition cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="overflow-y-auto space-y-2.5 flex-1 pr-1">
              {followListLoading ? (
                <div className="py-12 flex justify-center text-purple-400">
                  <Loader2 className="w-6 h-6 animate-spin" />
                </div>
              ) : followList.length === 0 ? (
                <p className="text-center text-xs text-slate-400 py-8 font-mono">
                  No {followModalType} found.
                </p>
              ) : (
                followList.map((u) => (
                  <div
                    key={u.id}
                    className="p-3 rounded-2xl bg-purple-950/20 border border-purple-500/15 flex items-center justify-between gap-3 hover:border-purple-500/30 transition"
                  >
                    <Link
                      to={`/users/${u.id}`}
                      onClick={() => setFollowModalOpen(false)}
                      className="flex items-center gap-3 min-w-0"
                    >
                      <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-purple-600 to-indigo-600 flex items-center justify-center text-white font-bold text-sm flex-shrink-0">
                        {u.display_name?.charAt(0)?.toUpperCase() || 'U'}
                      </div>
                      <div className="min-w-0">
                        <div className="text-xs font-bold text-white truncate hover:text-purple-300">
                          {u.display_name}
                        </div>
                        {u.bio && (
                          <p className="text-[10px] text-slate-400 truncate max-w-[200px] font-sans">
                            {u.bio}
                          </p>
                        )}
                      </div>
                    </Link>

                    {!u.is_self && (
                      <button
                        onClick={() => handleToggleFollowInModal(u)}
                        className={`px-3 py-1 rounded-xl text-[11px] font-mono transition flex-shrink-0 cursor-pointer ${
                          u.is_following
                            ? 'bg-slate-800 text-purple-300 border border-purple-500/30 hover:bg-rose-950/50 hover:text-rose-300'
                            : 'bg-purple-600 text-white hover:bg-purple-500'
                        }`}
                      >
                        {u.is_following ? 'Following' : 'Follow'}
                      </button>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default ProfilePage

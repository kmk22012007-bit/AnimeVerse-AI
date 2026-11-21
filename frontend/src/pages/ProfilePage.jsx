import React, { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
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
} from 'lucide-react'
import { getCurrentProfile, updateProfile } from '../api/profile'

export const ProfilePage = () => {
  const [profile, setProfile] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Edit State
  const [editing, setEditing] = useState(false)
  const [displayName, setDisplayName] = useState('')
  const [bio, setBio] = useState('')
  const [isPublic, setIsPublic] = useState(true)
  const [saving, setSaving] = useState(false)
  const [saveSuccess, setSaveSuccess] = useState(false)

  const fetchProfile = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await getCurrentProfile()
      setProfile(data)
      setDisplayName(data?.display_name || '')
      setBio(data?.bio || '')
      setIsPublic(Boolean(data?.is_public))
    } catch (err) {
      setError('Unable to load user profile data.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchProfile()
  }, [])

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
                  Demo Session
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
            </div>
          </div>

          <button
            onClick={() => setEditing((prev) => !prev)}
            type="button"
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-purple-950/60 hover:bg-purple-900/60 border border-purple-500/30 text-xs font-mono text-purple-200 transition-colors cursor-pointer self-start sm:self-auto"
          >
            <Edit3 className="w-3.5 h-3.5" />
            <span>{editing ? 'Cancel' : 'Edit Profile'}</span>
          </button>
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
    </div>
  )
}

export default ProfilePage

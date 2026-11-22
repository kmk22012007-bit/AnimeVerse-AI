import React, { useState, useEffect, useRef, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Bell,
  Check,
  CheckCheck,
  Trash2,
  Settings,
  X,
  Sparkles,
  Tv,
  Heart,
  MessageSquare,
  Clock,
  Info,
  ExternalLink,
  Loader2,
  Sliders,
} from 'lucide-react'
import {
  getNotifications,
  getUnreadCount,
  markNotificationRead,
  markAllNotificationsRead,
  deleteNotification,
  clearReadNotifications,
  getNotificationPreferences,
  updateNotificationPreferences,
} from '../../api/notifications'

// Relative time formatting helper
function formatRelativeTime(dateString) {
  if (!dateString) return ''
  const date = new Date(dateString)
  const now = new Date()
  const diffInSeconds = Math.floor((now - date) / 1000)

  if (diffInSeconds < 30) return 'Just now'
  if (diffInSeconds < 60) return `${diffInSeconds}s ago`
  const minutes = Math.floor(diffInSeconds / 60)
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  if (days < 7) return `${days}d ago`
  return date.toLocaleDateString()
}

// Icon and badge styling per notification category
function getNotificationMeta(type) {
  switch (type) {
    case 'anime_release':
      return {
        icon: Sparkles,
        label: 'Release',
        bg: 'bg-pink-500/15',
        border: 'border-pink-500/30',
        text: 'text-pink-400',
      }
    case 'episode_release':
      return {
        icon: Tv,
        label: 'Episode',
        bg: 'bg-cyan-500/15',
        border: 'border-cyan-500/30',
        text: 'text-cyan-400',
      }
    case 'community_like':
      return {
        icon: Heart,
        label: 'Like',
        bg: 'bg-rose-500/15',
        border: 'border-rose-500/30',
        text: 'text-rose-400',
      }
    case 'community_comment':
      return {
        icon: MessageSquare,
        label: 'Comment',
        bg: 'bg-purple-500/15',
        border: 'border-purple-500/30',
        text: 'text-purple-400',
      }
    case 'watchlist_reminder':
      return {
        icon: Clock,
        label: 'Reminder',
        bg: 'bg-amber-500/15',
        border: 'border-amber-500/30',
        text: 'text-amber-400',
      }
    case 'system':
    default:
      return {
        icon: Info,
        label: 'System',
        bg: 'bg-indigo-500/15',
        border: 'border-indigo-500/30',
        text: 'text-indigo-400',
      }
  }
}

export const NotificationBell = () => {
  const navigate = useNavigate()
  const [isOpen, setIsOpen] = useState(false)
  const [unreadCount, setUnreadCount] = useState(0)
  const [notifications, setNotifications] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [activeTab, setActiveTab] = useState('all') // 'all' or 'unread'
  const [showPreferences, setShowPreferences] = useState(false)
  const [preferences, setPreferences] = useState(null)
  const [prefLoading, setPrefLoading] = useState(false)
  const [prefSaving, setPrefSaving] = useState(false)

  const dropdownRef = useRef(null)

  // Poll for unread count
  const fetchUnreadCount = useCallback(async () => {
    try {
      const data = await getUnreadCount()
      setUnreadCount(data?.unread_count || 0)
    } catch (err) {
      // Quiet fail on background poll
    }
  }, [])

  useEffect(() => {
    fetchUnreadCount()
    const interval = setInterval(fetchUnreadCount, 45000)
    const handleFocus = () => fetchUnreadCount()
    window.addEventListener('focus', handleFocus)
    return () => {
      clearInterval(interval)
      window.removeEventListener('focus', handleFocus)
    }
  }, [fetchUnreadCount])

  // Fetch notifications when opened or tab changed
  const fetchNotificationList = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const isReadFilter = activeTab === 'unread' ? false : null
      const data = await getNotifications({ page: 1, is_read: isReadFilter })
      setNotifications(data?.results || [])
    } catch (err) {
      setError('Unable to load notifications.')
    } finally {
      setLoading(false)
    }
  }, [activeTab])

  useEffect(() => {
    if (isOpen) {
      fetchNotificationList()
      fetchUnreadCount()
    }
  }, [isOpen, activeTab, fetchNotificationList, fetchUnreadCount])

  // Close dropdown on click outside
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setIsOpen(false)
        setShowPreferences(false)
      }
    }
    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside)
    }
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [isOpen])

  // Actions: Mark Single Read
  const handleMarkRead = async (e, id) => {
    e.stopPropagation()
    try {
      await markNotificationRead(id)
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, is_read: true } : n))
      )
      setUnreadCount((prev) => Math.max(0, prev - 1))
    } catch (err) {
      // Fail silently
    }
  }

  // Actions: Click notification to navigate
  const handleItemClick = async (notif) => {
    if (!notif.is_read) {
      try {
        await markNotificationRead(notif.id)
        setUnreadCount((prev) => Math.max(0, prev - 1))
      } catch (err) {}
    }
    setIsOpen(false)
    if (notif.action_url) {
      navigate(notif.action_url)
    }
  }

  // Actions: Mark All Read
  const handleMarkAllRead = async () => {
    try {
      await markAllNotificationsRead()
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })))
      setUnreadCount(0)
    } catch (err) {
      // Failed to mark all
    }
  }

  // Actions: Delete Single
  const handleDelete = async (e, id) => {
    e.stopPropagation()
    try {
      await deleteNotification(id)
      const target = notifications.find((n) => n.id === id)
      if (target && !target.is_read) {
        setUnreadCount((prev) => Math.max(0, prev - 1))
      }
      setNotifications((prev) => prev.filter((n) => n.id !== id))
    } catch (err) {}
  }

  // Actions: Clear Read
  const handleClearRead = async () => {
    try {
      await clearReadNotifications()
      setNotifications((prev) => prev.filter((n) => !n.is_read))
    } catch (err) {}
  }

  // Load Preferences
  const handleOpenPreferences = async () => {
    setShowPreferences(true)
    setPrefLoading(true)
    try {
      const data = await getNotificationPreferences()
      setPreferences(data)
    } catch (err) {
      // Handle error
    } finally {
      setPrefLoading(false)
    }
  }

  // Toggle Preference
  const handleTogglePref = async (key) => {
    if (!preferences) return
    const updated = { ...preferences, [key]: !preferences[key] }
    setPreferences(updated)
    setPrefSaving(true)
    try {
      await updateNotificationPreferences({ [key]: updated[key] })
    } catch (err) {
      // Rollback
      setPreferences(preferences)
    } finally {
      setPrefSaving(false)
    }
  }

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Bell Trigger Button */}
      <button
        onClick={() => setIsOpen((prev) => !prev)}
        type="button"
        aria-label="Open notifications"
        className="relative p-2 rounded-xl text-slate-300 hover:text-white hover:bg-purple-900/30 border border-purple-500/20 transition-all cursor-pointer flex items-center justify-center focus:outline-none focus:border-purple-400"
      >
        <Bell className="w-5 h-5 text-slate-300 transition-transform group-hover:scale-105" />
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 flex h-4 min-w-[16px] px-1 items-center justify-center rounded-full bg-gradient-to-r from-purple-600 to-pink-500 text-[9px] font-mono font-bold text-white shadow-[0_0_10px_rgba(168,85,247,0.7)] animate-pulse">
            {unreadCount > 99 ? '99+' : unreadCount}
          </span>
        )}
      </button>

      {/* Notification Dropdown Panel */}
      {isOpen && (
        <div className="fixed left-3 right-3 top-16 sm:absolute sm:left-auto sm:right-0 sm:top-full sm:mt-2 sm:w-96 max-h-[85vh] rounded-2xl bg-[#0c0e1e]/98 backdrop-blur-xl border border-purple-500/30 shadow-[0_15px_50px_rgba(0,0,0,0.8),0_0_25px_rgba(168,85,247,0.2)] z-50 overflow-hidden text-xs">
          {/* Header */}
          <div className="p-3.5 border-b border-purple-500/20 flex items-center justify-between bg-purple-950/20">
            <div className="flex items-center gap-2">
              <span className="font-bold text-white text-sm tracking-wide">
                Notifications
              </span>
              {unreadCount > 0 && (
                <span className="px-1.5 py-0.5 rounded-full bg-purple-500/20 border border-purple-400/40 text-purple-300 text-[10px] font-mono">
                  {unreadCount} unread
                </span>
              )}
            </div>

            <div className="flex items-center gap-1.5">
              <button
                onClick={handleMarkAllRead}
                type="button"
                title="Mark all as read"
                className="p-1 rounded-lg text-slate-400 hover:text-purple-300 hover:bg-purple-900/40 transition-colors cursor-pointer"
              >
                <CheckCheck className="w-4 h-4" />
              </button>
              <button
                onClick={handleClearRead}
                type="button"
                title="Clear read notifications"
                className="p-1 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-rose-900/30 transition-colors cursor-pointer"
              >
                <Trash2 className="w-4 h-4" />
              </button>
              <button
                onClick={handleOpenPreferences}
                type="button"
                title="Notification settings"
                className="p-1 rounded-lg text-slate-400 hover:text-cyan-300 hover:bg-cyan-900/30 transition-colors cursor-pointer"
              >
                <Settings className="w-4 h-4" />
              </button>
              <button
                onClick={() => setIsOpen(false)}
                type="button"
                className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-purple-900/40 transition-colors cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Preferences View (Conditional Slide-over) */}
          {showPreferences ? (
            <div className="p-4 space-y-4 max-h-[420px] overflow-y-auto">
              <div className="flex items-center justify-between border-b border-purple-500/20 pb-2">
                <span className="font-bold text-white flex items-center gap-1.5">
                  <Sliders className="w-3.5 h-3.5 text-cyan-400" /> Notification Preferences
                </span>
                <button
                  onClick={() => setShowPreferences(false)}
                  className="text-xs text-purple-300 hover:text-purple-100 font-mono"
                >
                  Back
                </button>
              </div>

              {prefLoading ? (
                <div className="py-8 text-center text-slate-400 font-mono">
                  <Loader2 className="w-5 h-5 animate-spin mx-auto mb-2 text-purple-400" />
                  Loading preferences...
                </div>
              ) : preferences ? (
                <div className="space-y-3 font-sans">
                  {[
                    { key: 'anime_releases', label: 'Anime Premieres', desc: 'Alerts when scheduled series begin' },
                    { key: 'episode_releases', label: 'Episode Releases', desc: 'Alerts when new episodes of followed anime drop' },
                    { key: 'community_likes', label: 'Community Likes', desc: 'When others like your discussion posts' },
                    { key: 'community_comments', label: 'Community Comments', desc: 'When someone replies to your threads' },
                    { key: 'watchlist_reminders', label: 'Watchlist Reminders', desc: 'Friendly nudges for active watchlist titles' },
                    { key: 'system_notices', label: 'System Announcements', desc: 'Platform updates and feature news' },
                  ].map(({ key, label, desc }) => (
                    <div
                      key={key}
                      onClick={() => handleTogglePref(key)}
                      className="p-2.5 rounded-xl bg-purple-950/30 hover:bg-purple-900/30 border border-purple-500/20 flex items-center justify-between cursor-pointer transition-colors"
                    >
                      <div className="pr-3">
                        <div className="text-white font-medium text-xs">{label}</div>
                        <div className="text-[10px] text-slate-400 leading-tight">{desc}</div>
                      </div>
                      <div
                        className={`w-9 h-5 rounded-full p-0.5 transition-colors shrink-0 flex items-center ${
                          preferences[key] ? 'bg-purple-600 justify-end' : 'bg-slate-700 justify-start'
                        }`}
                      >
                        <div className="w-4 h-4 rounded-full bg-white shadow-sm" />
                      </div>
                    </div>
                  ))}
                  {prefSaving && (
                    <div className="text-[10px] font-mono text-cyan-400 text-right">
                      Saving changes...
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-center text-rose-400 text-xs py-4">
                  Failed to load preferences.
                </div>
              )}
            </div>
          ) : (
            <>
              {/* Filter Tabs */}
              <div className="flex border-b border-purple-500/20 bg-purple-950/10">
                <button
                  type="button"
                  onClick={() => setActiveTab('all')}
                  className={`flex-1 py-2 text-center font-mono font-medium border-b-2 transition-colors cursor-pointer ${
                    activeTab === 'all'
                      ? 'border-purple-400 text-purple-200 bg-purple-500/10'
                      : 'border-transparent text-slate-400 hover:text-slate-200'
                  }`}
                >
                  All
                </button>
                <button
                  type="button"
                  onClick={() => setActiveTab('unread')}
                  className={`flex-1 py-2 text-center font-mono font-medium border-b-2 transition-colors cursor-pointer ${
                    activeTab === 'unread'
                      ? 'border-purple-400 text-purple-200 bg-purple-500/10'
                      : 'border-transparent text-slate-400 hover:text-slate-200'
                  }`}
                >
                  Unread ({unreadCount})
                </button>
              </div>

              {/* Notification Items List */}
              <div className="max-h-[380px] overflow-y-auto divide-y divide-purple-500/10">
                {loading && (
                  <div className="p-8 text-center text-slate-400 font-mono">
                    <Loader2 className="w-5 h-5 animate-spin mx-auto mb-2 text-purple-400" />
                    Fetching notifications...
                  </div>
                )}

                {error && (
                  <div className="p-6 text-center text-rose-400 font-mono">
                    {error}
                  </div>
                )}

                {!loading && !error && notifications.length === 0 && (
                  <div className="p-8 text-center text-slate-400 space-y-2">
                    <div className="w-10 h-10 rounded-2xl bg-purple-950/40 border border-purple-500/20 flex items-center justify-center mx-auto text-purple-400">
                      <Bell className="w-5 h-5 opacity-40" />
                    </div>
                    <p className="font-sans font-medium text-slate-300">
                      {activeTab === 'unread' ? 'No unread notifications' : 'All caught up!'}
                    </p>
                    <p className="text-[11px] text-slate-500 font-mono">
                      {activeTab === 'unread'
                        ? 'Check the "All" tab for your notification history.'
                        : 'New release alerts, community interactions, and updates will appear here.'}
                    </p>
                  </div>
                )}

                {!loading &&
                  notifications.map((notif) => {
                    const meta = getNotificationMeta(notif.notification_type)
                    const IconComponent = meta.icon
                    const isUnread = !notif.is_read

                    return (
                      <div
                        key={notif.id}
                        onClick={() => handleItemClick(notif)}
                        className={`p-3 transition-colors cursor-pointer relative group flex items-start gap-3 ${
                          isUnread
                            ? 'bg-purple-950/35 hover:bg-purple-900/40'
                            : 'bg-transparent hover:bg-purple-950/20 opacity-80 hover:opacity-100'
                        }`}
                      >
                        {/* Type Icon Badge or Anime Poster Thumbnail */}
                        {notif.related_anime?.poster_url ? (
                          <div className="w-9 h-12 rounded-lg overflow-hidden border border-purple-500/30 bg-purple-950/50 shrink-0">
                            <img
                              src={notif.related_anime.poster_url}
                              alt={notif.related_anime.title}
                              className="w-full h-full object-cover"
                            />
                          </div>
                        ) : (
                          <div
                            className={`w-9 h-9 rounded-xl border ${meta.border} ${meta.bg} flex items-center justify-center shrink-0`}
                          >
                            <IconComponent className={`w-4 h-4 ${meta.text}`} />
                          </div>
                        )}

                        {/* Text Content */}
                        <div className="flex-1 min-w-0 pr-1">
                          <div className="flex items-center justify-between gap-1">
                            <span className="font-semibold text-white truncate text-xs flex items-center gap-1.5">
                              {notif.title}
                              {isUnread && (
                                <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse" />
                              )}
                            </span>
                            <span className="text-[10px] text-slate-400 font-mono shrink-0">
                              {formatRelativeTime(notif.created_at)}
                            </span>
                          </div>
                          <p className="text-[11px] text-slate-300 mt-0.5 line-clamp-2 leading-relaxed">
                            {notif.message}
                          </p>
                        </div>

                        {/* Hover Quick Actions */}
                        <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity shrink-0 self-center">
                          {isUnread && (
                            <button
                              onClick={(e) => handleMarkRead(e, notif.id)}
                              type="button"
                              title="Mark read"
                              className="p-1 rounded-md text-slate-400 hover:text-emerald-400 hover:bg-emerald-950/40 transition-colors"
                            >
                              <Check className="w-3.5 h-3.5" />
                            </button>
                          )}
                          <button
                            onClick={(e) => handleDelete(e, notif.id)}
                            type="button"
                            title="Delete"
                            className="p-1 rounded-md text-slate-400 hover:text-rose-400 hover:bg-rose-950/40 transition-colors"
                          >
                            <X className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </div>
                    )
                  })}
              </div>
            </>
          )}

          {/* Footer Link if Actionable */}
          <div className="p-2 border-t border-purple-500/20 bg-purple-950/20 text-center">
            <span className="text-[10px] font-mono text-slate-400">
              AnimeVerse Real-Time Notification Engine
            </span>
          </div>
        </div>
      )}
    </div>
  )
}

export default NotificationBell

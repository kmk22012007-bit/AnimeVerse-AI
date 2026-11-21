import React, { createContext, useContext, useState, useEffect, useCallback, useMemo } from 'react'
import {
  getWatchlist,
  addToWatchlist,
  updateWatchlistEntry,
  deleteWatchlistEntry,
  updateEpisodeProgress,
  completeWatchlistEntry,
} from '../api/watchlist'

const WatchlistContext = createContext()

export const WatchlistProvider = ({ children }) => {
  const [entries, setEntries] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [refreshKey, setRefreshKey] = useState(0)

  // Map mal_id -> entry for instant O(1) lookup across all cards
  const watchlistMap = useMemo(() => {
    const map = new Map()
    for (const e of entries) {
      if (e?.mal_id) {
        map.set(e.mal_id, e)
      }
    }
    return map
  }, [entries])

  // Load all user watchlist entries
  const fetchAllEntries = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await getWatchlist({ page: 1 })
      // AnimeversePagination returns results array
      const items = res?.results || (Array.isArray(res) ? res : [])
      setEntries(items)
    } catch (err) {
      setError(err.message || 'Failed to load watchlist.')
      console.debug('Watchlist load error:', err)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchAllEntries()
  }, [fetchAllEntries])

  // Add anime to watchlist
  const addAnime = async (malId, status = 'Plan to Watch') => {
    try {
      const newEntry = await addToWatchlist(malId, status)
      setEntries((prev) => [newEntry, ...prev.filter((e) => e.mal_id !== malId)])
      setRefreshKey((k) => k + 1)
      return { success: true, entry: newEntry }
    } catch (err) {
      return {
        success: false,
        error: err.message || 'Unable to add anime to watchlist.',
        isDuplicate: err.status === 409 || err.code === 'DUPLICATE_ENTRY',
      }
    }
  }

  // Update status (watching, completed, etc.)
  const changeStatus = async (id, newStatus) => {
    try {
      const updated = await updateWatchlistEntry(id, { status: newStatus })
      setEntries((prev) => prev.map((e) => (e.id === id ? updated : e)))
      setRefreshKey((k) => k + 1)
      return { success: true, entry: updated }
    } catch (err) {
      return { success: false, error: err.message }
    }
  }

  // Update progress directly
  const setProgress = async (id, count) => {
    try {
      const updated = await updateEpisodeProgress(id, count)
      setEntries((prev) => prev.map((e) => (e.id === id ? updated : e)))
      setRefreshKey((k) => k + 1)
      return { success: true, entry: updated }
    } catch (err) {
      return { success: false, error: err.message }
    }
  }

  // +1 Episode increment
  const incrementEpisode = async (entry) => {
    if (!entry) return
    const current = entry.watched_episodes || 0
    const total = entry.total_episodes
    if (total !== null && total !== undefined && current >= total) {
      return { success: false, error: 'All episodes already watched.' }
    }
    return await setProgress(entry.id, current + 1)
  }

  // -1 Episode decrement
  const decrementEpisode = async (entry) => {
    if (!entry) return
    const current = entry.watched_episodes || 0
    if (current <= 0) {
      return { success: false, error: 'Episode count cannot be negative.' }
    }
    return await setProgress(entry.id, current - 1)
  }

  // Save rating and personal note
  const saveRatingAndNote = async (id, { rating, note }) => {
    try {
      const payload = {}
      if (rating !== undefined) payload.rating = rating
      if (note !== undefined) payload.note = note
      const updated = await updateWatchlistEntry(id, payload)
      setEntries((prev) => prev.map((e) => (e.id === id ? updated : e)))
      setRefreshKey((k) => k + 1)
      return { success: true, entry: updated }
    } catch (err) {
      return { success: false, error: err.message }
    }
  }

  // Mark completed
  const markAsCompleted = async (id) => {
    try {
      const updated = await completeWatchlistEntry(id)
      setEntries((prev) => prev.map((e) => (e.id === id ? updated : e)))
      setRefreshKey((k) => k + 1)
      return { success: true, entry: updated }
    } catch (err) {
      return { success: false, error: err.message }
    }
  }

  // Remove from watchlist
  const removeAnime = async (id) => {
    try {
      await deleteWatchlistEntry(id)
      setEntries((prev) => prev.filter((e) => e.id !== id))
      setRefreshKey((k) => k + 1)
      return { success: true }
    } catch (err) {
      return { success: false, error: err.message }
    }
  }

  // Check if anime is in list
  const getEntryByMalId = (malId) => {
    return watchlistMap.get(malId) || null
  }

  return (
    <WatchlistContext.Provider
      value={{
        entries,
        loading,
        error,
        refreshKey,
        refreshWatchlist: fetchAllEntries,
        addAnime,
        changeStatus,
        setProgress,
        incrementEpisode,
        decrementEpisode,
        saveRatingAndNote,
        markAsCompleted,
        removeAnime,
        getEntryByMalId,
      }}
    >
      {children}
    </WatchlistContext.Provider>
  )
}

export const useWatchlist = () => {
  const context = useContext(WatchlistContext)
  if (!context) {
    throw new Error('useWatchlist must be used within a WatchlistProvider')
  }
  return context
}

export default WatchlistContext

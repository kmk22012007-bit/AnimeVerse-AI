import apiClient from './client'

/**
 * SRS GET /api/list/?status={status}&sort={sort}&page={page}
 * Retrieves the user's personal watchlist.
 */
export const getWatchlist = async (params = {}) => {
  return await apiClient.get('/list/', { params })
}

/**
 * SRS POST /api/list/
 * Adds an anime to the user's watchlist with initial status.
 * Body: { mal_id: int, status: string }
 */
export const addToWatchlist = async (malId, status = 'Plan to Watch') => {
  return await apiClient.post('/list/', {
    mal_id: malId,
    status,
  })
}

/**
 * SRS PATCH /api/list/{id}/
 * Updates status, rating (1-10 or null), and note (up to 2000 chars).
 */
export const updateWatchlistEntry = async (id, data = {}) => {
  return await apiClient.patch(`/list/${id}/`, data)
}

/**
 * SRS DELETE /api/list/{id}/
 * Removes entry from watchlist and cascades to episode progress.
 */
export const deleteWatchlistEntry = async (id) => {
  return await apiClient.delete(`/list/${id}/`)
}

/**
 * SRS PUT /api/list/{id}/progress/
 * Updates watched episodes count atomically.
 * Body: { watched_episodes: int }
 */
export const updateEpisodeProgress = async (id, watchedEpisodes) => {
  return await apiClient.put(`/list/${id}/progress/`, {
    watched_episodes: watchedEpisodes,
  })
}

/**
 * SRS POST /api/list/{id}/complete/
 * Marks an anime as completed and sets watched_episodes to total episodes.
 */
export const completeWatchlistEntry = async (id) => {
  return await apiClient.post(`/list/${id}/complete/`)
}

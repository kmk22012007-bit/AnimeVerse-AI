import apiClient from './client'

/**
 * GET /api/analytics/overview/
 * Retrieves unified personal anime tracking statistics, genre analytics,
 * rating distribution, activity timeline, and insights.
 */
export const getAnalyticsOverview = async () => {
  return await apiClient.get('/analytics/overview/')
}

/**
 * GET /api/analytics/genres/
 */
export const getGenreAnalytics = async () => {
  return await apiClient.get('/analytics/genres/')
}

/**
 * GET /api/analytics/ratings/
 */
export const getRatingAnalytics = async () => {
  return await apiClient.get('/analytics/ratings/')
}

/**
 * GET /api/analytics/activity/
 */
export const getActivityAnalytics = async () => {
  return await apiClient.get('/analytics/activity/')
}

/**
 * GET /api/analytics/watchlist/
 */
export const getWatchlistInsights = async () => {
  return await apiClient.get('/analytics/watchlist/')
}

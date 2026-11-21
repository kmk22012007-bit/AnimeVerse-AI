import apiClient from './client'

/**
 * SRS GET /api/dashboard/
 * Retrieves live welcome info, currently watching items, calculated user stats,
 * recent updates, and trending strip.
 */
export const getDashboardData = async () => {
  return await apiClient.get('/dashboard/')
}

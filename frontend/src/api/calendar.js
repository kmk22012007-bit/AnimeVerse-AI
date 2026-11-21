import apiClient from './client'

/**
 * SRS GET /api/calendar/season/?year={year}&season={season}&page={page}
 */
export const getSeasonAnime = async (year = null, season = null, page = 1) => {
  const params = { page }
  if (year) params.year = year
  if (season) params.season = season
  return await apiClient.get('/calendar/season/', { params })
}

/**
 * SRS GET /api/calendar/upcoming/?page={page}
 */
export const getUpcomingAnime = async (page = 1) => {
  return await apiClient.get('/calendar/upcoming/', {
    params: { page },
  })
}

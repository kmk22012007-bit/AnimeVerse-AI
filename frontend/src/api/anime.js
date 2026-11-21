import apiClient from './client'

/**
 * SRS GET /api/anime/search/?q={q}&page={page}
 * Search anime by title (2 to 100 characters).
 */
export const searchAnime = async (q, page = 1) => {
  return await apiClient.get('/anime/search/', {
    params: { q, page },
  })
}

/**
 * SRS GET /api/anime/trending/?page={page}
 * Trending anime strip and discover stream.
 */
export const getTrendingAnime = async (page = 1) => {
  return await apiClient.get('/anime/trending/', {
    params: { page },
  })
}

/**
 * SRS GET /api/anime/browse/
 * Filter by genre, min_score, type, status, page.
 */
export const browseAnime = async (filters = {}) => {
  return await apiClient.get('/anime/browse/', {
    params: filters,
  })
}

/**
 * SRS GET /api/anime/{mal_id}/
 * Full anime details with characters, synopsis, genres, and metadata source.
 */
export const getAnimeDetails = async (malId) => {
  return await apiClient.get(`/anime/${malId}/`)
}

/**
 * SRS GET /api/anime/{mal_id}/watch-options/?country={country}&audio={audio}&sub={sub}
 * Legal streaming availability with 5 categories (subscription, free, free_with_ads, rent, buy)
 * and verified audio & subtitle language filtering.
 */
export const getWatchOptions = async (malId, country = 'IN', audio = '', sub = '') => {
  const params = { country }
  if (audio && audio !== 'all') params.audio = audio
  if (sub && sub !== 'all') params.sub = sub
  return await apiClient.get(`/anime/${malId}/watch-options/`, { params })
}

/**
 * GET /api/anime/franchises/{idOrSlug}/
 * Retrieves categorized entries for an entire anime franchise.
 */
export const getFranchise = async (idOrSlug) => {
  return await apiClient.get(`/anime/franchises/${idOrSlug}/`)
}

/**
 * GET /api/anime/{mal_id}/franchise/
 * Retrieves franchise group for a specific anime if one exists.
 */
export const getAnimeFranchise = async (malId) => {
  return await apiClient.get(`/anime/${malId}/franchise/`)
}

/**
 * SRS GET /api/anime/{mal_id}/episodes/?page={page}
 * Episode guide with episode numbers, titles, synopses, filler flag, air dates.
 */
export const getAnimeEpisodes = async (malId, page = 1) => {
  return await apiClient.get(`/anime/${malId}/episodes/`, {
    params: { page },
  })
}

/**
 * SRS GET /api/anime/{mal_id}/related/
 * Related anime, prequels, sequels, and side-stories.
 */
export const getRelatedAnime = async (malId) => {
  return await apiClient.get(`/anime/${malId}/related/`)
}

/**
 * SRS GET /api/anime/{mal_id}/trailers/
 * Verified official YouTube trailers.
 */
export const getAnimeTrailers = async (malId) => {
  return await apiClient.get(`/anime/${malId}/trailers/`)
}

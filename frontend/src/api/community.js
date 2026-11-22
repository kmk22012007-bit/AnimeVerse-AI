import apiClient from './client'

/**
 * GET /api/community/posts/
 * Supports: page, sort, anime_id, category, tag, filter, search
 */
export const getCommunityPosts = async (params = {}) => {
  const queryParams = typeof params === 'number' ? { page: params } : params
  return await apiClient.get('/community/posts/', { params: queryParams })
}

/**
 * POST /api/community/posts/
 * Supports: title, body, anime_id, category, tags, is_spoiler, poll
 */
export const createCommunityPost = async (payload) => {
  // If legacy call (title, body) as two arguments
  if (typeof payload === 'string') {
    const title = arguments[0]
    const body = arguments[1]
    return await apiClient.post('/community/posts/', { title, body })
  }
  return await apiClient.post('/community/posts/', payload)
}

/**
 * GET /api/community/posts/{id}/
 */
export const getCommunityPostDetail = async (id) => {
  return await apiClient.get(`/community/posts/${id}/`)
}

/**
 * PATCH /api/community/posts/{id}/
 */
export const updateCommunityPost = async (id, data) => {
  return await apiClient.patch(`/community/posts/${id}/`, data)
}

/**
 * DELETE /api/community/posts/{id}/
 */
export const deleteCommunityPost = async (id) => {
  return await apiClient.delete(`/community/posts/${id}/`)
}

/**
 * POST /api/community/posts/{id}/like/
 */
export const likeCommunityPost = async (id) => {
  return await apiClient.post(`/community/posts/${id}/like/`)
}

/**
 * DELETE /api/community/posts/{id}/like/
 */
export const unlikeCommunityPost = async (id) => {
  return await apiClient.delete(`/community/posts/${id}/like/`)
}

/**
 * POST /api/community/posts/{id}/comments/
 * Supports: body, parent_id, is_spoiler
 */
export const addCommentToPost = async (id, payload) => {
  const data = typeof payload === 'string' ? { body: payload } : payload
  return await apiClient.post(`/community/posts/${id}/comments/`, data)
}

/**
 * PATCH /api/community/comments/{id}/
 */
export const updateComment = async (id, data) => {
  return await apiClient.patch(`/community/comments/${id}/`, data)
}

/**
 * DELETE /api/community/comments/{id}/
 */
export const deleteComment = async (id) => {
  return await apiClient.delete(`/community/comments/${id}/`)
}

/**
 * POST /api/community/polls/{id}/vote/
 */
export const votePoll = async (id, optionId) => {
  return await apiClient.post(`/community/polls/${id}/vote/`, { option_id: optionId })
}

/**
 * POST /api/community/reports/
 */
export const submitCommunityReport = async (data) => {
  return await apiClient.post('/community/reports/', data)
}

/**
 * GET /api/community/moderation/reports/
 */
export const getModerationReports = async (params = {}) => {
  return await apiClient.get('/community/moderation/reports/', { params })
}

/**
 * PATCH /api/community/moderation/reports/{id}/
 */
export const actionModerationReport = async (id, data) => {
  return await apiClient.patch(`/community/moderation/reports/${id}/`, data)
}

/**
 * GET /api/anime/{mal_id}/reviews/
 */
export const getAnimeReviews = async (malId, params = {}) => {
  return await apiClient.get(`/anime/${malId}/reviews/`, { params })
}

/**
 * POST /api/anime/{mal_id}/reviews/
 */
export const createAnimeReview = async (malId, data) => {
  return await apiClient.post(`/anime/${malId}/reviews/`, data)
}

/**
 * POST /api/reviews/{id}/helpful/
 */
export const voteReviewHelpful = async (id) => {
  return await apiClient.post(`/reviews/${id}/helpful/`)
}

import apiClient from './client'

/**
 * SRS GET /api/profile/
 */
export const getCurrentProfile = async () => {
  return await apiClient.get('/profile/')
}

/**
 * SRS PATCH /api/profile/
 */
export const updateProfile = async (data) => {
  return await apiClient.patch('/profile/', data)
}

/**
 * GET /api/profile/preferences/
 * Get user personalization and diversity preferences
 */
export const getUserPreferences = async () => {
  return await apiClient.get('/profile/preferences/')
}

/**
 * PUT /api/profile/preferences/
 * Update user personalization and diversity preferences
 */
export const updateUserPreferences = async (preferences) => {
  return await apiClient.put('/profile/preferences/', preferences)
}

/**
 * GET /api/profile/taste-profile/
 * Get grounded anime taste profile (inferred + explicit)
 */
export const getUserTasteProfile = async () => {
  return await apiClient.get('/profile/taste-profile/')
}

/**
 * GET /api/users/{id}/
 * Get public profile, anime stats, community activity, and follow status
 */
export const getPublicUserProfile = async (id) => {
  return await apiClient.get(`/users/${id}/`)
}

/**
 * POST /api/users/{id}/follow/
 * Follow a user
 */
export const followUser = async (id) => {
  return await apiClient.post(`/users/${id}/follow/`)
}

/**
 * DELETE /api/users/{id}/follow/
 * Unfollow a user
 */
export const unfollowUser = async (id) => {
  return await apiClient.delete(`/users/${id}/follow/`)
}

/**
 * GET /api/users/{id}/followers/
 * Paginated list of followers
 */
export const getUserFollowers = async (id, page = 1) => {
  return await apiClient.get(`/users/${id}/followers/`, { params: { page } })
}

/**
 * GET /api/users/{id}/following/
 * Paginated list of followed users
 */
export const getUserFollowing = async (id, page = 1) => {
  return await apiClient.get(`/users/${id}/following/`, { params: { page } })
}



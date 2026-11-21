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

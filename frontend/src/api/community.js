import apiClient from './client'

/**
 * SRS GET /api/community/posts/?page={page}
 */
export const getCommunityPosts = async (page = 1) => {
  return await apiClient.get('/community/posts/', {
    params: { page },
  })
}

/**
 * SRS POST /api/community/posts/
 */
export const createCommunityPost = async (title, body) => {
  return await apiClient.post('/community/posts/', { title, body })
}

/**
 * SRS GET /api/community/posts/{id}/
 */
export const getCommunityPostDetail = async (id) => {
  return await apiClient.get(`/community/posts/${id}/`)
}

/**
 * SRS POST /api/community/posts/{id}/like/
 */
export const likeCommunityPost = async (id) => {
  return await apiClient.post(`/community/posts/${id}/like/`)
}

/**
 * SRS DELETE /api/community/posts/{id}/like/
 */
export const unlikeCommunityPost = async (id) => {
  return await apiClient.delete(`/community/posts/${id}/like/`)
}

/**
 * SRS POST /api/community/posts/{id}/comments/
 */
export const addCommentToPost = async (id, body) => {
  return await apiClient.post(`/community/posts/${id}/comments/`, { body })
}

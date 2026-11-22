import apiClient from './client'

/**
 * POST /api/ryuk/messages/
 * Sends message to RYUK AI assistant.
 */
export const sendRyukMessage = async (message, conversationId = null, animeMalId = null) => {
  const payload = { message }
  if (conversationId) payload.conversation_id = conversationId
  if (animeMalId) payload.anime_mal_id = animeMalId

  return await apiClient.post('/ryuk/messages/', payload)
}

/**
 * GET /api/ryuk/conversations/
 * Retrieves conversation list for current session.
 */
export const getRyukConversations = async () => {
  return await apiClient.get('/ryuk/conversations/')
}

/**
 * DELETE /api/ryuk/conversations/{id}/
 * Deletes a specific conversation owned by current user.
 */
export const deleteRyukConversation = async (conversationId) => {
  return await apiClient.delete(`/ryuk/conversations/${conversationId}/`)
}

/**
 * POST /api/ryuk/conversations/clear/
 * Clears all conversations for current user.
 */
export const clearRyukConversations = async () => {
  return await apiClient.post('/ryuk/conversations/clear/')
}

/**
 * GET /api/ryuk/conversations/{id}/messages/
 * Retrieves message history for a conversation.
 */
export const getRyukConversationMessages = async (conversationId) => {
  return await apiClient.get(`/ryuk/conversations/${conversationId}/messages/`)
}

/**
 * GET /api/ryuk/recommendations/
 * Retrieves personalized anime recommendations with RYUK AI rationales.
 * Supports mode='personalized' | 'different'.
 */
export const getRyukRecommendations = async (params = {}) => {
  return await apiClient.get('/ryuk/recommendations/', { params })
}

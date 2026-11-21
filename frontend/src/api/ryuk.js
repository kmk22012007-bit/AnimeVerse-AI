import apiClient from './client'

/**
 * SRS POST /api/ryuk/messages/
 * Sends message to RYUK AI assistant.
 */
export const sendRyukMessage = async (message, conversationId = null, animeMalId = null) => {
  const payload = { message }
  if (conversationId) payload.conversation_id = conversationId
  if (animeMalId) payload.anime_mal_id = animeMalId

  return await apiClient.post('/ryuk/messages/', payload)
}

/**
 * SRS GET /api/ryuk/conversations/
 * Retrieves conversation list for current demo session.
 */
export const getRyukConversations = async () => {
  return await apiClient.get('/ryuk/conversations/')
}

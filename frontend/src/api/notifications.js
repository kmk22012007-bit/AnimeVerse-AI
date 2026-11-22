import { apiClient } from './client'

/**
 * Fetches paginated notifications for the current user.
 * Optional query params: page, is_read, type.
 */
export const getNotifications = async ({ page = 1, is_read = null, type = null } = {}) => {
  const params = { page }
  if (is_read !== null && is_read !== undefined) {
    params.is_read = is_read
  }
  if (type) {
    params.type = type
  }
  return apiClient.get('/notifications/', { params })
}

/**
 * Fetches the count of unread notifications for badge rendering.
 */
export const getUnreadCount = async () => {
  return apiClient.get('/notifications/unread-count/')
}

/**
 * Marks a specific notification as read.
 */
export const markNotificationRead = async (id) => {
  return apiClient.patch(`/notifications/${id}/read/`)
}

/**
 * Marks all notifications for the current user as read.
 */
export const markAllNotificationsRead = async () => {
  return apiClient.post('/notifications/mark-all-read/')
}

/**
 * Deletes a single notification.
 */
export const deleteNotification = async (id) => {
  return apiClient.delete(`/notifications/${id}/`)
}

/**
 * Clears/purges all read notifications for the current user.
 */
export const clearReadNotifications = async () => {
  return apiClient.delete('/notifications/clear-read/')
}

/**
 * Retrieves the current user's notification preferences.
 */
export const getNotificationPreferences = async () => {
  return apiClient.get('/notifications/preferences/')
}

/**
 * Updates the current user's notification preferences.
 */
export const updateNotificationPreferences = async (preferences) => {
  return apiClient.patch('/notifications/preferences/', preferences)
}

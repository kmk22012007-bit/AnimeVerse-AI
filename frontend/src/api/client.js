import axios from 'axios'

// Centralized Axios client configured for AnimeVerse AI Django Backend.
// withCredentials: true ensures the animeverse_session cookie is preserved across calls.
const baseURL = import.meta.env.VITE_API_BASE_URL || '/api'

export const apiClient = axios.create({
  baseURL,
  withCredentials: true,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
})

// Response interceptor for standardized error extraction per SRS
apiClient.interceptors.response.use(
  (response) => response.data,
  (error) => {
    let standardizedError = {
      message: 'An unexpected error occurred while communicating with AnimeVerse services.',
      code: 'UNKNOWN_ERROR',
      status: error.response ? error.response.status : 500,
      details: null,
    }

    if (error.response && error.response.data) {
      const data = error.response.data
      if (typeof data.error === 'string') {
        standardizedError.message = data.error
      } else if (data.error && typeof data.error === 'object') {
        standardizedError.message = data.error.message || standardizedError.message
        standardizedError.code = data.error.code || standardizedError.code
        standardizedError.details = data.error.details || null
      } else if (data.message) {
        standardizedError.message = data.message
      } else if (data.detail) {
        standardizedError.message = data.detail
      }
    } else if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
      standardizedError.message = 'The upstream anime service timed out. Please try again in a few moments.'
      standardizedError.code = 'REQUEST_TIMEOUT'
      standardizedError.status = 504
    } else if (!error.response) {
      standardizedError.message = 'Unable to reach the AnimeVerse backend server. Please verify Django is running on port 8000.'
      standardizedError.code = 'BACKEND_OFFLINE'
      standardizedError.status = 503
    }

    return Promise.reject(standardizedError)
  }
)

export default apiClient

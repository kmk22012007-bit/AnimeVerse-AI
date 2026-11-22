import React, { Suspense, lazy } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { ThemeProvider } from './context/ThemeContext'
import { WatchlistProvider } from './context/WatchlistContext'
import AppLayout from './components/layout/AppLayout'

// Eager load primary landing page for instantaneous first paint
import DashboardPage from './pages/DashboardPage'

// Route-based code splitting: lazy load secondary feature pages
const DiscoverPage = lazy(() => import('./pages/DiscoverPage'))
const MyListPage = lazy(() => import('./pages/MyListPage'))
const AnimeDetailsPage = lazy(() => import('./pages/AnimeDetailsPage'))
const FranchiseDetailsPage = lazy(() => import('./pages/FranchiseDetailsPage'))
const WatchAnywherePage = lazy(() => import('./pages/WatchAnywherePage'))
const RyukAssistantPage = lazy(() => import('./pages/RyukAssistantPage'))
const CommunityPage = lazy(() => import('./pages/CommunityPage'))
const CalendarPage = lazy(() => import('./pages/CalendarPage'))
const ProfilePage = lazy(() => import('./pages/ProfilePage'))
const AnalyticsPage = lazy(() => import('./pages/AnalyticsPage'))

const PageLoader = () => (
  <div className="w-full min-h-[50vh] flex flex-col items-center justify-center gap-3">
    <div className="w-9 h-9 rounded-2xl bg-purple-600/30 border border-purple-400/40 flex items-center justify-center">
      <div className="w-3.5 h-3.5 rounded-full bg-purple-400 animate-ping" />
    </div>
    <span className="text-xs font-mono text-purple-300">Loading module...</span>
  </div>
)

export function App() {
  return (
    <ThemeProvider>
      <WatchlistProvider>
        <BrowserRouter>
          <Routes>
            <Route element={<AppLayout />}>
              <Route index element={<DashboardPage />} />
              <Route
                path="discover"
                element={
                  <Suspense fallback={<PageLoader />}>
                    <DiscoverPage />
                  </Suspense>
                }
              />
              <Route
                path="list"
                element={
                  <Suspense fallback={<PageLoader />}>
                    <MyListPage />
                  </Suspense>
                }
              />
              <Route
                path="analytics"
                element={
                  <Suspense fallback={<PageLoader />}>
                    <AnalyticsPage />
                  </Suspense>
                }
              />
              <Route
                path="anime/:id"
                element={
                  <Suspense fallback={<PageLoader />}>
                    <AnimeDetailsPage />
                  </Suspense>
                }
              />
              <Route
                path="franchise/:id"
                element={
                  <Suspense fallback={<PageLoader />}>
                    <FranchiseDetailsPage />
                  </Suspense>
                }
              />
              <Route
                path="watch"
                element={
                  <Suspense fallback={<PageLoader />}>
                    <WatchAnywherePage />
                  </Suspense>
                }
              />
              <Route
                path="ryuk"
                element={
                  <Suspense fallback={<PageLoader />}>
                    <RyukAssistantPage />
                  </Suspense>
                }
              />
              <Route
                path="community"
                element={
                  <Suspense fallback={<PageLoader />}>
                    <CommunityPage />
                  </Suspense>
                }
              />
              <Route
                path="calendar"
                element={
                  <Suspense fallback={<PageLoader />}>
                    <CalendarPage />
                  </Suspense>
                }
              />
              <Route
                path="profile"
                element={
                  <Suspense fallback={<PageLoader />}>
                    <ProfilePage />
                  </Suspense>
                }
              />
              <Route
                path="users/:id"
                element={
                  <Suspense fallback={<PageLoader />}>
                    <ProfilePage />
                  </Suspense>
                }
              />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </WatchlistProvider>
    </ThemeProvider>
  )
}

export default App

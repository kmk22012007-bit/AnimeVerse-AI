import React from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { ThemeProvider } from './context/ThemeContext'
import { WatchlistProvider } from './context/WatchlistContext'
import AppLayout from './components/layout/AppLayout'

// Pages
import DashboardPage from './pages/DashboardPage'
import DiscoverPage from './pages/DiscoverPage'
import MyListPage from './pages/MyListPage'
import AnimeDetailsPage from './pages/AnimeDetailsPage'
import FranchiseDetailsPage from './pages/FranchiseDetailsPage'
import WatchAnywherePage from './pages/WatchAnywherePage'
import RyukAssistantPage from './pages/RyukAssistantPage'
import CommunityPage from './pages/CommunityPage'
import CalendarPage from './pages/CalendarPage'
import ProfilePage from './pages/ProfilePage'

export function App() {
  return (
    <ThemeProvider>
      <WatchlistProvider>
        <BrowserRouter>
          <Routes>
            <Route element={<AppLayout />}>
              <Route index element={<DashboardPage />} />
              <Route path="discover" element={<DiscoverPage />} />
              <Route path="list" element={<MyListPage />} />
              <Route path="anime/:id" element={<AnimeDetailsPage />} />
              <Route path="franchise/:id" element={<FranchiseDetailsPage />} />
              <Route path="watch" element={<WatchAnywherePage />} />
              <Route path="ryuk" element={<RyukAssistantPage />} />
              <Route path="community" element={<CommunityPage />} />
              <Route path="calendar" element={<CalendarPage />} />
              <Route path="profile" element={<ProfilePage />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </WatchlistProvider>
    </ThemeProvider>
  )
}

export default App

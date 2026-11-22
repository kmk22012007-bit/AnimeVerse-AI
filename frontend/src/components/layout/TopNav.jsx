import React, { useState } from 'react'
import { Menu, User, ShieldCheck, Search, X } from 'lucide-react'
import { useNavigate, Link } from 'react-router-dom'
import SearchBar from '../common/SearchBar'
import ThemeSwitcher from '../common/ThemeSwitcher'
import NotificationBell from '../notifications/NotificationBell'

export const TopNav = ({ onToggleSidebar, displayName = 'Guest' }) => {
  const navigate = useNavigate()
  const [mobileSearchOpen, setMobileSearchOpen] = useState(false)

  const handleGlobalSearch = (query) => {
    if (query && query.trim().length >= 2) {
      setMobileSearchOpen(false)
      navigate(`/discover?q=${encodeURIComponent(query.trim())}`)
    }
  }

  return (
    <header
      role="banner"
      className="sticky top-0 z-30 bg-[#080911]/90 backdrop-blur-md border-b border-purple-500/20 px-4 sm:px-6 transition-colors"
    >
      <div className="h-16 flex items-center justify-between gap-4">
        <div className="flex items-center gap-3 flex-1 max-w-xl">
          {/* Mobile menu toggle */}
          <button
            onClick={onToggleSidebar}
            type="button"
            aria-label="Open navigation menu"
            className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-purple-900/30 border border-purple-500/20 md:hidden transition cursor-pointer min-h-[40px] min-w-[40px] flex items-center justify-center"
          >
            <Menu className="w-5 h-5" />
          </button>

          {/* Global Live Search Bar (Desktop/Tablet) */}
          <SearchBar
            placeholder="Search anime across database (min 2 chars)..."
            onSearch={handleGlobalSearch}
            liveSearch={true}
            className="max-w-md hidden sm:flex"
          />

          {/* Mobile Search Toggle Button */}
          <button
            onClick={() => setMobileSearchOpen((prev) => !prev)}
            type="button"
            aria-label={mobileSearchOpen ? 'Close search' : 'Open mobile search'}
            className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-purple-900/30 border border-purple-500/20 sm:hidden transition cursor-pointer min-h-[40px] min-w-[40px] flex items-center justify-center"
          >
            {mobileSearchOpen ? <X className="w-5 h-5 text-purple-300" /> : <Search className="w-5 h-5" />}
          </button>
        </div>

        {/* Right Controls: Notification Bell, Theme Switcher & User Profile */}
        <div className="flex items-center gap-2.5 sm:gap-3">
          <NotificationBell />
          <ThemeSwitcher />

          {/* User Session Link Pill */}
          <Link
            to="/profile"
            title="View and edit your personal anime profile"
            aria-label={`Profile for ${displayName}`}
            className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-purple-950/40 hover:bg-purple-900/60 border border-purple-500/30 hover:border-purple-400/60 transition shadow-[0_0_10px_rgba(168,85,247,0.15)] group cursor-pointer"
          >
            <div className="w-6 h-6 rounded-lg bg-gradient-to-tr from-purple-600 via-indigo-600 to-cyan-500 flex items-center justify-center text-white text-xs font-bold flex-shrink-0 group-hover:scale-105 transition-transform">
              <User className="w-3.5 h-3.5" />
            </div>
            <div className="flex flex-col text-left">
              <span className="text-xs font-semibold text-slate-200 group-hover:text-purple-200 transition-colors leading-none truncate max-w-[100px] sm:max-w-[140px]">
                {displayName}
              </span>
              <span className="text-[9px] font-mono text-cyan-400 flex items-center gap-0.5 leading-tight">
                <ShieldCheck className="w-2.5 h-2.5" /> Demo Session
              </span>
            </div>
          </Link>
        </div>
      </div>

      {/* Expandable Mobile Search Bar Drawer */}
      {mobileSearchOpen && (
        <div className="sm:hidden pb-3 pt-1 border-t border-purple-500/15 animate-in fade-in slide-in-from-top-1 duration-150">
          <SearchBar
            placeholder="Search anime across database..."
            onSearch={handleGlobalSearch}
            liveSearch={true}
            autoFocus={true}
          />
        </div>
      )}
    </header>
  )
}

export default TopNav

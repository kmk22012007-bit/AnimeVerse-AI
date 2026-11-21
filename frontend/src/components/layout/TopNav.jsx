import React from 'react'
import { Menu, User, ShieldCheck } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import SearchBar from '../common/SearchBar'
import ThemeSwitcher from '../common/ThemeSwitcher'

export const TopNav = ({ onToggleSidebar, displayName = 'Guest' }) => {
  const navigate = useNavigate()

  const handleGlobalSearch = (query) => {
    if (query && query.trim().length >= 2) {
      navigate(`/discover?q=${encodeURIComponent(query.trim())}`)
    }
  }

  return (
    <header className="sticky top-0 z-30 h-16 bg-[#07080f]/90 backdrop-blur-md border-b border-purple-500/20 px-4 sm:px-6 flex items-center justify-between gap-4">
      <div className="flex items-center gap-3 flex-1 max-w-xl">
        {/* Mobile menu toggle */}
        <button
          onClick={onToggleSidebar}
          type="button"
          aria-label="Open navigation menu"
          className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-purple-900/30 border border-purple-500/20 md:hidden"
        >
          <Menu className="w-5 h-5" />
        </button>

        {/* Global Live Search Bar */}
        <SearchBar
          placeholder="Search anime across database (min 2 chars)..."
          onSearch={handleGlobalSearch}
          liveSearch={true}
          className="max-w-md hidden sm:flex"
        />
      </div>

      {/* Right Controls: Theme Switcher & User Profile status */}
      <div className="flex items-center gap-3">
        <ThemeSwitcher />

        {/* User Session Pill */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-purple-950/40 border border-purple-500/30 shadow-[0_0_10px_rgba(168,85,247,0.15)]">
          <div className="w-6 h-6 rounded-lg bg-gradient-to-tr from-purple-600 to-cyan-500 flex items-center justify-center text-white text-xs font-bold">
            <User className="w-3.5 h-3.5" />
          </div>
          <div className="flex flex-col text-left">
            <span className="text-xs font-semibold text-slate-200 leading-none">
              {displayName}
            </span>
            <span className="text-[9px] font-mono text-cyan-400 flex items-center gap-0.5 leading-tight">
              <ShieldCheck className="w-2.5 h-2.5" /> Demo Session
            </span>
          </div>
        </div>
      </div>
    </header>
  )
}

export default TopNav

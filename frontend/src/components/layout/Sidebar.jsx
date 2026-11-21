import React from 'react'
import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard,
  Compass,
  BookmarkCheck,
  Tv,
  Bot,
  MessageSquare,
  CalendarDays,
  User,
  X,
  Radio,
  Zap,
} from 'lucide-react'

const navItems = [
  { name: 'Dashboard', path: '/', icon: LayoutDashboard },
  { name: 'Discover', path: '/discover', icon: Compass },
  { name: 'My List', path: '/list', icon: BookmarkCheck },
  { name: 'Watch Anywhere', path: '/watch', icon: Tv, badge: 'NEW' },
  { name: 'RYUK AI Assistant', path: '/ryuk', icon: Bot, badge: 'AI' },
  { name: 'Community', path: '/community', icon: MessageSquare },
  { name: 'Calendar', path: '/calendar', icon: CalendarDays },
  { name: 'Profile', path: '/profile', icon: User },
]

export const Sidebar = ({ isOpen, onClose }) => {
  return (
    <>
      {/* Mobile Backdrop overlay */}
      {isOpen && (
        <div
          onClick={onClose}
          className="fixed inset-0 z-40 bg-black/70 backdrop-blur-sm md:hidden"
        />
      )}

      {/* Sidebar Container */}
      <aside
        className={`fixed top-0 bottom-0 left-0 z-50 w-64 bg-[#0a0c18] border-r border-purple-500/20 flex flex-col justify-between transition-transform duration-300 md:translate-x-0 ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {/* Brand Header */}
        <div>
          <div className="h-16 flex items-center justify-between px-5 border-b border-purple-500/20">
            <NavLink to="/" onClick={onClose} className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-purple-600 via-fuchsia-600 to-indigo-700 flex items-center justify-center shadow-[0_0_15px_rgba(168,85,247,0.6)]">
                <Zap className="w-4 h-4 text-white fill-white" />
              </div>
              <div className="flex items-center gap-1.5">
                <span className="font-extrabold text-base tracking-wider bg-gradient-to-r from-purple-200 via-fuchsia-200 to-purple-400 bg-clip-text text-transparent">
                  AnimeVerse
                </span>
                <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-purple-900/60 text-purple-300 border border-purple-500/40 font-bold">
                  AI
                </span>
              </div>
            </NavLink>

            {/* Mobile close button */}
            <button
              onClick={onClose}
              type="button"
              className="p-1 rounded-lg text-slate-400 hover:text-white md:hidden"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Navigation Links */}
          <nav className="p-3 space-y-1.5 mt-2">
            {navItems.map((item) => {
              const Icon = item.icon
              return (
                <NavLink
                  key={item.path}
                  to={item.path}
                  onClick={onClose}
                  className={({ isActive }) =>
                    `flex items-center justify-between px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 ${
                      isActive
                        ? 'bg-purple-600/20 text-purple-200 border border-purple-500/40 shadow-[0_0_15px_rgba(168,85,247,0.2)] font-semibold'
                        : 'text-slate-400 hover:text-slate-200 hover:bg-purple-950/30 hover:border hover:border-purple-500/20'
                    }`
                  }
                >
                  <div className="flex items-center gap-3">
                    <Icon className="w-4 h-4" />
                    <span>{item.name}</span>
                  </div>

                  {item.badge && (
                    <span
                      className={`text-[9px] font-mono font-bold px-1.5 py-0.5 rounded ${
                        item.badge === 'AI'
                          ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40'
                          : 'bg-purple-500/20 text-purple-300 border border-purple-500/40'
                      }`}
                    >
                      {item.badge}
                    </span>
                  )}
                </NavLink>
              )
            })}
          </nav>
        </div>

        {/* Cyberpunk Footer / System Status */}
        <div className="p-4 border-t border-purple-500/20 bg-purple-950/20">
          <div className="flex items-center gap-2 mb-1.5">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
            <span className="text-[11px] font-mono font-semibold text-slate-300 tracking-wide">
              SYSTEM ONLINE
            </span>
          </div>
          <div className="flex items-center justify-between text-[10px] text-slate-500 font-mono">
            <span>Uplink: Live Upstream</span>
            <span className="text-purple-400">Tenrai / AniList</span>
          </div>
        </div>
      </aside>
    </>
  )
}

export default Sidebar

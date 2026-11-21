import React from 'react'
import { Sparkles, Bot } from 'lucide-react'
import { Link } from 'react-router-dom'

export const FloatingRyuk = () => {
  return (
    <aside aria-label="RYUK AI Assistant" className="fixed bottom-6 right-6 z-50 group">
      {/* Pulsing neon halo aura */}
      <div className="absolute inset-0 rounded-full bg-purple-600/30 blur-md animate-pulse"></div>

      <Link
        to="/ryuk"
        className="relative flex items-center gap-2.5 px-4 py-3 rounded-full bg-gradient-to-r from-purple-950 via-purple-900 to-indigo-950 border border-purple-400/50 text-white shadow-[0_0_25px_rgba(168,85,247,0.45)] hover:shadow-[0_0_35px_rgba(168,85,247,0.8)] transition-all duration-300 hover:scale-105"
      >
        <div className="relative w-7 h-7 rounded-full bg-purple-600/60 border border-purple-300 flex items-center justify-center shadow-[0_0_10px_rgba(168,85,247,0.8)]">
          <Bot className="w-4 h-4 text-purple-100" />
          <span className="absolute -top-1 -right-1 w-2.5 h-2.5 rounded-full bg-cyan-400 border border-purple-950 shadow-[0_0_6px_rgba(6,182,212,1)]"></span>
        </div>

        <div className="flex flex-col text-left">
          <span className="text-xs font-bold tracking-wider text-purple-200 flex items-center gap-1">
            RYUK AI <Sparkles className="w-3 h-3 text-cyan-400 animate-spin" />
          </span>
          <span className="text-[10px] text-slate-300 font-mono">Cybernetic Intel</span>
        </div>
      </Link>
    </aside>
  )
}

export default FloatingRyuk

import React from 'react'
import { Sun, Moon } from 'lucide-react'
import { useTheme } from '../../context/ThemeContext'

export const ThemeSwitcher = ({ className = '' }) => {
  const { isDark, toggleTheme } = useTheme()

  return (
    <button
      onClick={toggleTheme}
      type="button"
      aria-label="Toggle theme"
      className={`relative inline-flex items-center justify-center p-2 rounded-xl transition-all duration-300 border border-purple-500/20 bg-purple-950/20 hover:bg-purple-900/40 text-purple-300 hover:text-purple-100 hover:border-purple-400/50 shadow-[0_0_10px_rgba(168,85,247,0.15)] ${className}`}
      title={isDark ? 'Switch to Light Theme' : 'Switch to Cyberpunk Dark Theme'}
    >
      {isDark ? (
        <Sun className="w-4 h-4 text-amber-400 transition-transform rotate-0 hover:rotate-45" />
      ) : (
        <Moon className="w-4 h-4 text-purple-600 transition-transform -rotate-12 hover:rotate-0" />
      )}
    </button>
  )
}

export default ThemeSwitcher

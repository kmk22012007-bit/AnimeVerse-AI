import React from 'react'

export const StatCard = ({
  icon: Icon,
  label,
  value,
  sublabel,
  accent = 'purple',
}) => {
  const accentStyles = {
    purple: {
      border: 'border-purple-500/25 hover:border-purple-400/50',
      bgIcon: 'bg-purple-500/15 border-purple-500/30 text-purple-400',
      glow: 'shadow-[0_0_20px_rgba(168,85,247,0.12)] hover:shadow-[0_0_25px_rgba(168,85,247,0.22)]',
      valueColor: 'text-purple-200',
    },
    cyan: {
      border: 'border-cyan-500/25 hover:border-cyan-400/50',
      bgIcon: 'bg-cyan-500/15 border-cyan-500/30 text-cyan-400',
      glow: 'shadow-[0_0_20px_rgba(6,182,212,0.12)] hover:shadow-[0_0_25px_rgba(6,182,212,0.22)]',
      valueColor: 'text-cyan-200',
    },
    emerald: {
      border: 'border-emerald-500/25 hover:border-emerald-400/50',
      bgIcon: 'bg-emerald-500/15 border-emerald-500/30 text-emerald-400',
      glow: 'shadow-[0_0_20px_rgba(16,185,129,0.12)] hover:shadow-[0_0_25px_rgba(16,185,129,0.22)]',
      valueColor: 'text-emerald-200',
    },
  }

  const currentAccent = accentStyles[accent] || accentStyles.purple

  return (
    <div
      role="region"
      aria-label={label}
      className={`p-5 rounded-2xl bg-[#0e101d]/90 border transition-all duration-300 backdrop-blur-md min-h-[110px] flex flex-col justify-between ${currentAccent.border} ${currentAccent.glow} hover:-translate-y-1`}
    >
      <div className="flex items-center justify-between">
        <div className="space-y-1">
          <p className="text-[11px] uppercase tracking-wider text-slate-400 font-semibold font-mono">
            {label}
          </p>
          <h3 className={`text-2xl sm:text-3xl font-extrabold tracking-tight font-mono ${currentAccent.valueColor}`}>
            {value}
          </h3>
          {sublabel && (
            <p className="text-[11px] text-slate-400 font-sans">
              {sublabel}
            </p>
          )}
        </div>

        {Icon && (
          <div
            aria-hidden="true"
            className={`w-12 h-12 rounded-2xl flex items-center justify-center border flex-shrink-0 ${currentAccent.bgIcon}`}
          >
            <Icon className="w-6 h-6" />
          </div>
        )}
      </div>
    </div>
  )
}

export default StatCard

import React from 'react'
import { Inbox, Compass, SearchX } from 'lucide-react'
import { Link } from 'react-router-dom'

export const EmptyState = ({
  icon: Icon = Inbox,
  title = 'No Records Found',
  description = 'No anime entries match the selected filters or query.',
  actionLabel,
  actionLink,
  onAction,
}) => {
  return (
    <div className="rounded-2xl border border-purple-500/20 bg-purple-950/15 p-8 sm:p-12 text-center my-6 backdrop-blur-sm relative overflow-hidden">
      <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-purple-500/10 border border-purple-500/30 text-purple-400 mb-4 shadow-[0_0_15px_rgba(168,85,247,0.15)]">
        <Icon className="w-7 h-7" />
      </div>

      <h3 className="text-lg font-bold text-slate-100 mb-2 tracking-wide">
        {title}
      </h3>

      <p className="text-sm text-slate-400 max-w-md mx-auto mb-6 leading-relaxed">
        {description}
      </p>

      {actionLabel && actionLink && (
        <Link
          to={actionLink}
          className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-purple-600/90 hover:bg-purple-500 text-white font-medium text-sm transition-all shadow-[0_0_15px_rgba(168,85,247,0.3)]"
        >
          <Compass className="w-4 h-4" />
          <span>{actionLabel}</span>
        </Link>
      )}

      {actionLabel && onAction && !actionLink && (
        <button
          onClick={onAction}
          type="button"
          className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-purple-600/90 hover:bg-purple-500 text-white font-medium text-sm transition-all shadow-[0_0_15px_rgba(168,85,247,0.3)] cursor-pointer"
        >
          <span>{actionLabel}</span>
        </button>
      )}
    </div>
  )
}

export default EmptyState

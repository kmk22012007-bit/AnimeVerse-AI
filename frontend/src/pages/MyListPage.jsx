import React, { useState, useMemo } from 'react'
import { Link } from 'react-router-dom'
import {
  BookmarkCheck,
  Plus,
  SlidersHorizontal,
  Search,
  Compass,
  Play,
  CheckCircle2,
  Clock,
  PauseCircle,
  XCircle,
} from 'lucide-react'
import { useWatchlist } from '../context/WatchlistContext'
import WatchlistRowCard from '../components/watchlist/WatchlistRowCard'
import EditRatingNoteModal from '../components/watchlist/EditRatingNoteModal'
import ConfirmDeleteModal from '../components/watchlist/ConfirmDeleteModal'
import EmptyState from '../components/common/EmptyState'

const STATUS_FILTERS = [
  { label: 'All', value: 'all' },
  { label: 'Watching', value: 'Watching', icon: Play },
  { label: 'Completed', value: 'Completed', icon: CheckCircle2 },
  { label: 'Plan to Watch', value: 'Plan to Watch', icon: Clock },
  { label: 'On Hold', value: 'On Hold', icon: PauseCircle },
  { label: 'Dropped', value: 'Dropped', icon: XCircle },
]

export const MyListPage = () => {
  const { entries, loading, saveRatingAndNote, removeAnime } = useWatchlist()

  const [activeStatus, setActiveStatus] = useState('all')
  const [searchQuery, setSearchQuery] = useState('')
  const [sortBy, setSortBy] = useState('updated') // 'updated' | 'title' | 'rating'

  // Modal states
  const [ratingModalEntry, setRatingModalEntry] = useState(null)
  const [deleteModalEntry, setDeleteModalEntry] = useState(null)
  const [deleting, setDeleting] = useState(false)

  // Filter & sort calculations
  const filteredAndSortedEntries = useMemo(() => {
    let result = [...entries]

    // 1. Status Filter
    if (activeStatus !== 'all') {
      result = result.filter((item) => item.status === activeStatus)
    }

    // 2. Search Filter
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase().trim()
      result = result.filter((item) => (item.title || '').toLowerCase().includes(q))
    }

    // 3. Sorting
    result.sort((a, b) => {
      if (sortBy === 'title') {
        return (a.title || '').localeCompare(b.title || '')
      } else if (sortBy === 'rating') {
        const rA = a.rating || 0
        const rB = b.rating || 0
        if (rB !== rA) return rB - rA
        return new Date(b.updated_at || 0) - new Date(a.updated_at || 0)
      } else {
        // 'updated'
        return new Date(b.updated_at || 0) - new Date(a.updated_at || 0)
      }
    })

    return result
  }, [entries, activeStatus, searchQuery, sortBy])

  // Counts by status
  const counts = useMemo(() => {
    const c = { all: entries.length, Watching: 0, Completed: 0, 'Plan to Watch': 0, 'On Hold': 0, Dropped: 0 }
    for (const e of entries) {
      if (c[e.status] !== undefined) c[e.status]++
    }
    return c
  }, [entries])

  const handleDeleteConfirm = async (id) => {
    setDeleting(true)
    await removeAnime(id)
    setDeleting(false)
    setDeleteModalEntry(null)
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-wide flex items-center gap-2.5">
            <BookmarkCheck className="w-7 h-7 text-purple-400" />
            My Watchlist
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-1 font-mono">
            {entries.length} anime tracked in your active demo session
          </p>
        </div>

        <Link
          to="/discover"
          className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-semibold text-xs sm:text-sm transition-all shadow-[0_0_15px_rgba(168,85,247,0.4)] w-fit"
        >
          <Plus className="w-4 h-4" />
          <span>Add More Anime</span>
        </Link>
      </div>

      {/* Filter Tabs & Search Controls */}
      <div className="space-y-4">
        {/* Status Pills Strip */}
        <div className="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-none">
          {STATUS_FILTERS.map((f) => {
            const count = counts[f.value] || 0
            const isSelected = activeStatus === f.value
            return (
              <button
                key={f.value}
                onClick={() => setActiveStatus(f.value)}
                type="button"
                className={`inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold whitespace-nowrap transition-all duration-200 cursor-pointer ${
                  isSelected
                    ? 'bg-purple-600 text-white shadow-[0_0_15px_rgba(168,85,247,0.5)] border border-purple-400 font-bold'
                    : 'bg-purple-950/30 text-slate-400 hover:text-slate-200 border border-purple-500/20 hover:border-purple-400/40'
                }`}
              >
                <span>{f.label}</span>
                <span
                  className={`text-[10px] font-mono px-1.5 py-0.2 rounded-full ${
                    isSelected ? 'bg-black/30 text-white' : 'bg-purple-900/40 text-purple-300'
                  }`}
                >
                  {count}
                </span>
              </button>
            )
          })}
        </div>

        {/* Search inside Watchlist and Sort Row */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="relative w-full sm:w-72">
            <Search className="w-4 h-4 absolute left-3 top-3 text-purple-400 pointer-events-none" />
            <input
              type="text"
              placeholder="Filter your watchlist by title..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-3 py-2 text-xs rounded-xl bg-purple-950/30 border border-purple-500/30 text-white placeholder:text-slate-500 focus:outline-none focus:border-purple-400"
            />
          </div>

          <div className="flex items-center gap-2 text-xs">
            <SlidersHorizontal className="w-3.5 h-3.5 text-purple-400" />
            <span className="text-slate-400 font-mono">Sort by:</span>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="px-3 py-1.5 rounded-xl bg-purple-950/40 border border-purple-500/30 text-purple-200 text-xs font-semibold focus:outline-none focus:border-purple-400 cursor-pointer"
            >
              <option value="updated">Recently Updated</option>
              <option value="title">Title (A - Z)</option>
              <option value="rating">Rating (Highest First)</option>
            </select>
          </div>
        </div>
      </div>

      {/* Watchlist Items */}
      {loading && entries.length === 0 ? (
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-32 rounded-2xl bg-purple-950/20 border border-purple-500/20 animate-pulse"></div>
          ))}
        </div>
      ) : filteredAndSortedEntries.length === 0 ? (
        <EmptyState
          title={
            searchQuery
              ? `No anime matching "${searchQuery}"`
              : activeStatus !== 'all'
              ? `No anime in "${activeStatus.replace('_', ' ')}"`
              : 'Your Watchlist is Empty'
          }
          description={
            searchQuery
              ? 'Try adjusting your title search or clear the filter.'
              : activeStatus !== 'all'
              ? `You do not have any anime marked with status "${activeStatus.replace('_', ' ')}". Change filters above or add anime from Discover.`
              : 'Start building your personal watchlist by exploring trending titles, upcoming releases, or searching your favorite series.'
          }
          actionLabel="Discover Anime"
          actionLink="/discover"
        />
      ) : (
        <div className="space-y-4">
          {filteredAndSortedEntries.map((entry) => (
            <WatchlistRowCard
              key={entry.id}
              entry={entry}
              onEditRatingNote={(e) => setRatingModalEntry(e)}
              onDelete={(e) => setDeleteModalEntry(e)}
            />
          ))}
        </div>
      )}

      {/* Edit Rating & Note Modal */}
      <EditRatingNoteModal
        entry={ratingModalEntry}
        isOpen={!!ratingModalEntry}
        onClose={() => setRatingModalEntry(null)}
        onSave={saveRatingAndNote}
      />

      {/* Confirm Delete Modal */}
      <ConfirmDeleteModal
        entry={deleteModalEntry}
        isOpen={!!deleteModalEntry}
        onClose={() => setDeleteModalEntry(null)}
        onConfirm={handleDeleteConfirm}
        deleting={deleting}
      />
    </div>
  )
}

export default MyListPage

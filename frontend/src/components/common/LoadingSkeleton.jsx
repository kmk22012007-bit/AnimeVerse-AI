import React from 'react'

export const HeroSkeleton = () => (
  <div className="w-full h-80 sm:h-96 rounded-2xl bg-gradient-to-r from-purple-950/20 via-purple-900/10 to-purple-950/20 border border-purple-500/20 animate-pulse relative overflow-hidden flex items-end p-6 sm:p-10">
    <div className="space-y-4 max-w-xl w-full">
      <div className="h-6 w-32 bg-purple-500/20 rounded-md"></div>
      <div className="h-10 w-3/4 bg-purple-500/20 rounded-lg"></div>
      <div className="h-4 w-full bg-purple-500/15 rounded"></div>
      <div className="h-4 w-5/6 bg-purple-500/15 rounded"></div>
      <div className="flex gap-4 pt-2">
        <div className="h-10 w-36 bg-purple-600/30 rounded-xl"></div>
        <div className="h-10 w-28 bg-purple-950/40 border border-purple-500/30 rounded-xl"></div>
      </div>
    </div>
  </div>
)

export const StatSkeleton = () => (
  <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
    {[1, 2, 3].map((i) => (
      <div key={i} className="p-5 rounded-2xl bg-purple-950/20 border border-purple-500/20 animate-pulse flex items-center justify-between">
        <div className="space-y-2">
          <div className="h-3 w-24 bg-purple-500/20 rounded"></div>
          <div className="h-7 w-16 bg-purple-500/30 rounded"></div>
        </div>
        <div className="w-12 h-12 rounded-xl bg-purple-500/20"></div>
      </div>
    ))}
  </div>
)

export const CardSkeleton = ({ count = 6 }) => (
  <div className="grid grid-cols-2 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 2xl:grid-cols-6 gap-5 sm:gap-6">
    {Array.from({ length: count }).map((_, i) => (
      <div key={i} className="rounded-xl overflow-hidden bg-purple-950/20 border border-purple-500/15 animate-pulse flex flex-col">
        <div className="w-full aspect-[3/4] bg-purple-900/20 relative"></div>
        <div className="p-3 space-y-2 flex-1 flex flex-col justify-between">
          <div className="space-y-1.5">
            <div className="h-4 w-full bg-purple-500/20 rounded"></div>
            <div className="h-3 w-2/3 bg-purple-500/15 rounded"></div>
          </div>
          <div className="flex justify-between items-center pt-2">
            <div className="h-3 w-10 bg-purple-500/20 rounded"></div>
            <div className="h-3 w-12 bg-purple-500/20 rounded"></div>
          </div>
        </div>
      </div>
    ))}
  </div>
)

export const ProgressSkeleton = () => (
  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
    {[1, 2].map((i) => (
      <div key={i} className="p-4 rounded-xl bg-purple-950/20 border border-purple-500/20 animate-pulse flex gap-4">
        <div className="w-16 h-24 rounded-lg bg-purple-900/30 flex-shrink-0"></div>
        <div className="flex-1 space-y-2.5 py-1">
          <div className="h-4 w-3/4 bg-purple-500/20 rounded"></div>
          <div className="h-3 w-1/3 bg-purple-500/15 rounded"></div>
          <div className="h-2 w-full bg-purple-500/20 rounded-full mt-3"></div>
          <div className="flex justify-between items-center pt-1">
            <div className="h-3 w-16 bg-purple-500/20 rounded"></div>
            <div className="h-7 w-20 bg-purple-600/30 rounded-lg"></div>
          </div>
        </div>
      </div>
    ))}
  </div>
)

export default {
  HeroSkeleton,
  StatSkeleton,
  CardSkeleton,
  ProgressSkeleton,
}

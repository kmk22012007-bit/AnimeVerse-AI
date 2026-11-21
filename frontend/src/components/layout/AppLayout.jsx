import React, { useState } from 'react'
import { Outlet } from 'react-router-dom'
import Sidebar from './Sidebar'
import TopNav from './TopNav'
import FloatingRyuk from '../common/FloatingRyuk'

export const AppLayout = ({ displayName = 'Guest' }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false)

  return (
    <div className="min-h-screen bg-[#07080f] text-slate-100 cyber-grid flex">
      {/* Sidebar navigation */}
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 md:pl-64 min-h-screen">
        <TopNav
          onToggleSidebar={() => setSidebarOpen((prev) => !prev)}
          displayName={displayName}
        />

        <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-7xl w-full mx-auto min-h-0">
          <Outlet />
        </main>
      </div>

      {/* Floating RYUK AI Assistant trigger */}
      <FloatingRyuk />
    </div>
  )
}

export default AppLayout

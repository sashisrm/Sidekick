import { NavLink, useNavigate } from 'react-router-dom'
import { MessageSquare, FileText, BarChart2, Package, LogOut, ChevronLeft, ChevronRight } from 'lucide-react'
import { useState } from 'react'
import { useAuth } from '../../context/AuthContext'

const NAV = [
  { to: '/chat', icon: MessageSquare, label: 'Chat' },
  { to: '/documents', icon: FileText, label: 'Documents' },
  { to: '/products', icon: Package, label: 'Products' },
  { to: '/competitive', icon: BarChart2, label: 'Competitive' },
]

export function Layout({ children }: { children: React.ReactNode }) {
  const { user, logout } = useAuth()
  const [collapsed, setCollapsed] = useState(false)

  return (
    <div className="flex h-screen bg-gray-50 overflow-hidden">
      {/* Sidebar */}
      <aside className={`flex flex-col bg-white border-r border-gray-200 transition-all duration-200 ${collapsed ? 'w-16' : 'w-52'}`}>
        <div className={`flex items-center h-14 px-4 border-b border-gray-100 ${collapsed ? 'justify-center' : 'gap-2'}`}>
          {!collapsed && <span className="font-bold text-gray-900 text-lg">SideKick</span>}
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="p-1 rounded-md text-gray-400 hover:text-gray-600 hover:bg-gray-100 ml-auto"
          >
            {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
          </button>
        </div>

        <nav className="flex-1 px-2 pt-4 space-y-0.5">
          {NAV.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${
                  isActive
                    ? 'bg-brand-50 text-brand-700 font-medium'
                    : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                } ${collapsed ? 'justify-center' : ''}`
              }
              title={collapsed ? label : undefined}
            >
              <Icon size={18} />
              {!collapsed && label}
            </NavLink>
          ))}
        </nav>

        <div className="border-t border-gray-100 p-3">
          <div className={`flex items-center gap-2 ${collapsed ? 'justify-center' : ''}`}>
            {!collapsed && (
              <div className="flex-1 min-w-0">
                <p className="text-xs font-medium text-gray-800 truncate">{user?.name}</p>
                <p className="text-xs text-gray-400 truncate">{user?.email}</p>
              </div>
            )}
            <button
              onClick={logout}
              className="p-1.5 rounded-lg text-gray-400 hover:text-red-500 hover:bg-red-50 transition-colors"
              title="Sign out"
            >
              <LogOut size={16} />
            </button>
          </div>
        </div>
      </aside>

      <main className="flex-1 flex flex-col overflow-hidden">
        {children}
      </main>
    </div>
  )
}

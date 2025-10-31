import { ReactNode } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { BarChart3, Users, Trophy, Activity, List, Copy, TrendingUp } from 'lucide-react'

interface LayoutProps {
  children: ReactNode
}

export default function Layout({ children }: LayoutProps) {
  const location = useLocation()

  const navItems = [
    { path: '/copy-trading', label: 'Copy Trading', icon: Copy },
    { path: '/dashboard', label: 'Dashboard', icon: BarChart3 },
    { path: '/trades', label: 'Trades', icon: List },
    { path: '/leaderboard', label: 'Leaderboard', icon: Trophy },
  ]

  const isActive = (path: string) => location.pathname === path

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-950 via-gray-900 to-gray-950">
      {/* Header Ultra-Stylé */}
      <header className="bg-gray-900/80 backdrop-blur-xl border-b border-gray-800/50 sticky top-0 z-50 shadow-2xl">
        <div className="max-w-full mx-auto px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            {/* Logo & Title */}
            <div className="flex items-center space-x-3">
              <div className="relative">
                <div className="absolute inset-0 bg-blue-500 blur-xl opacity-50 animate-pulse"></div>
                <TrendingUp className="w-8 h-8 text-blue-400 relative z-10" strokeWidth={2.5} />
              </div>
              <div>
                <h1 className="text-xl font-bold bg-gradient-to-r from-blue-400 via-cyan-400 to-teal-400 bg-clip-text text-transparent">
                  Polymarket Dashboard
                </h1>
                <p className="text-xs text-gray-500">Copy Trading Platform</p>
              </div>
            </div>

            {/* Navigation */}
            <nav className="flex items-center space-x-2">
              {navItems.map((item) => {
                const Icon = item.icon
                const active = isActive(item.path)
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    className={cn(
                      'group relative flex items-center space-x-2 px-4 py-2 rounded-xl font-medium transition-all duration-300',
                      active
                        ? 'bg-gradient-to-r from-blue-600 to-blue-500 text-white shadow-lg shadow-blue-500/50'
                        : 'text-gray-400 hover:text-white hover:bg-gray-800/50'
                    )}
                  >
                    {active && (
                      <div className="absolute inset-0 bg-gradient-to-r from-blue-600 to-blue-500 rounded-xl blur opacity-50 -z-10"></div>
                    )}
                    <Icon className="w-5 h-5" />
                    <span className="text-sm">{item.label}</span>
                  </Link>
                )
              })}
            </nav>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="w-full">
        {children}
      </main>

      {/* Footer Ultra-Dark */}
      <footer className="bg-gray-950 border-t border-gray-800/50 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="text-center text-sm text-gray-500">
            <p className="flex items-center justify-center gap-2">
              <Activity className="w-4 h-4 text-blue-500" />
              Polymarket Copy Trading Dashboard - Made with
              <span className="text-blue-400 font-medium">React</span>
            </p>
          </div>
        </div>
      </footer>
    </div>
  )
}

function cn(...classes: string[]) {
  return classes.filter(Boolean).join(' ')
}

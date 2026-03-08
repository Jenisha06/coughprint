'use client'
import Link from 'next/link'
import { usePathname } from 'next/navigation'

export default function Navbar() {
  const pathname = usePathname()

  const links = [
    { to: '/', label: '🎙️ Record' },
    { to: '/results', label: '📊 Results' },
    { to: '/map', label: '🗺️ Map' },
  ]

  return (
    <nav className="bg-gray-900 border-b border-gray-800 px-6 py-4 flex items-center justify-between">
      <span className="text-xl font-bold text-emerald-400">🫁 CoughPrint</span>
      <div className="flex gap-6">
        {links.map(l => (
          <Link
            key={l.to}
            href={l.to}
            className={`text-sm font-medium transition-colors ${
              pathname === l.to ? 'text-emerald-400' : 'text-gray-400 hover:text-white'
            }`}
          >
            {l.label}
          </Link>
        ))}
      </div>
    </nav>
  )
}
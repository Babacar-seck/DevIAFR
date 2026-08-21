'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

const navItems = [
  { href: '/dashboard', label: 'Dashboard', icon: '📊' },
  { href: '/personas', label: 'Personas', icon: '🎭' },
  { href: '/production', label: 'Production', icon: '🎬' },
  { href: '/videos', label: 'Vidéos', icon: '📹' },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 bg-primary-dark border-r border-primary-light flex flex-col">
      <div className="p-6 border-b border-primary-light">
        <h1 className="text-2xl font-bold text-secondary">DevIAFR</h1>
        <p className="text-sm text-gray-400 mt-1">Production Vidéo</p>
      </div>

      <nav className="flex-1 p-4 space-y-2">
        {navItems.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                isActive
                  ? 'bg-secondary text-primary-dark font-semibold'
                  : 'text-gray-300 hover:bg-primary-light'
              }`}
            >
              <span className="text-xl">{item.icon}</span>
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>

      <div className="p-4 border-t border-primary-light">
        <p className="text-xs text-gray-500">Version 2.0.0</p>
      </div>
    </aside>
  );
}

'use client'

import { useState } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { ShoppingBag, ShoppingCart, User, Menu, X, LogOut } from 'lucide-react'
import { useSession, signOut } from 'next-auth/react'
import { useCart } from '@/context/CartContext'
import clsx from 'clsx'

export default function Navbar() {
  const [mobileOpen, setMobileOpen] = useState(false)
  const { data: session } = useSession()
  const { cartCount } = useCart()
  const pathname = usePathname()

  const navLinks = [
    { href: '/', label: 'Home' },
    { href: '/products', label: 'Products' },
    { href: '/account', label: 'Account' },
  ]

  const isActive = (href: string) =>
    href === '/' ? pathname === '/' : pathname.startsWith(href)

  return (
    <header className="sticky top-0 z-50 bg-white border-b border-gray-200 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2 font-bold text-xl text-blue-600">
            <ShoppingBag size={24} />
            <span>ShopLocal</span>
          </Link>

          {/* Desktop Nav */}
          <nav className="hidden md:flex items-center gap-6">
            {navLinks.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className={clsx(
                  'font-medium transition-colors hover:text-blue-600',
                  isActive(link.href) ? 'text-blue-600' : 'text-gray-600'
                )}
              >
                {link.label}
              </Link>
            ))}
          </nav>

          {/* Desktop Right */}
          <div className="hidden md:flex items-center gap-4">
            {session?.user ? (
              <div className="flex items-center gap-3">
                <span className="text-sm text-gray-600">{session.user.email}</span>
                <button
                  onClick={() => signOut({ callbackUrl: '/' })}
                  className="flex items-center gap-1 text-sm text-gray-600 hover:text-red-600 transition-colors"
                >
                  <LogOut size={16} />
                  Logout
                </button>
              </div>
            ) : (
              <Link
                href="/account/login"
                className="flex items-center gap-1 text-sm font-medium text-gray-600 hover:text-blue-600 transition-colors"
              >
                <User size={18} />
                Login
              </Link>
            )}
            <Link
              href="/cart"
              className="relative flex items-center gap-1 text-gray-600 hover:text-blue-600 transition-colors"
            >
              <ShoppingCart size={22} />
              {cartCount > 0 && (
                <span className="absolute -top-2 -right-2 min-w-[18px] h-[18px] flex items-center justify-center bg-blue-600 text-white text-xs font-bold rounded-full px-1">
                  {cartCount > 99 ? '99+' : cartCount}
                </span>
              )}
            </Link>
          </div>

          {/* Mobile Right */}
          <div className="flex md:hidden items-center gap-3">
            <Link href="/cart" className="relative text-gray-600">
              <ShoppingCart size={22} />
              {cartCount > 0 && (
                <span className="absolute -top-2 -right-2 min-w-[18px] h-[18px] flex items-center justify-center bg-blue-600 text-white text-xs font-bold rounded-full px-1">
                  {cartCount > 99 ? '99+' : cartCount}
                </span>
              )}
            </Link>
            <button
              onClick={() => setMobileOpen(!mobileOpen)}
              className="text-gray-600"
              aria-label="Toggle menu"
            >
              {mobileOpen ? <X size={24} /> : <Menu size={24} />}
            </button>
          </div>
        </div>

        {/* Mobile Menu */}
        {mobileOpen && (
          <div className="md:hidden border-t border-gray-200 py-4 space-y-3">
            {navLinks.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                onClick={() => setMobileOpen(false)}
                className={clsx(
                  'block py-2 font-medium transition-colors hover:text-blue-600',
                  isActive(link.href) ? 'text-blue-600' : 'text-gray-600'
                )}
              >
                {link.label}
              </Link>
            ))}
            {session?.user ? (
              <div className="border-t border-gray-200 pt-3">
                <p className="text-sm text-gray-500 mb-2">{session.user.email}</p>
                <button
                  onClick={() => {
                    setMobileOpen(false)
                    signOut({ callbackUrl: '/' })
                  }}
                  className="flex items-center gap-2 text-sm text-red-600"
                >
                  <LogOut size={16} />
                  Logout
                </button>
              </div>
            ) : (
              <Link
                href="/account/login"
                onClick={() => setMobileOpen(false)}
                className="flex items-center gap-2 text-sm font-medium text-gray-600 border-t border-gray-200 pt-3"
              >
                <User size={16} />
                Login / Register
              </Link>
            )}
          </div>
        )}
      </div>
    </header>
  )
}

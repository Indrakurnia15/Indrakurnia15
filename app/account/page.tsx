'use client'

import { useSession } from 'next-auth/react'
import { useRouter } from 'next/navigation'
import { useEffect } from 'react'
import Link from 'next/link'
import { Package, DollarSign, User, Settings, ChevronRight } from 'lucide-react'

const mockOrders = [
  {
    id: 'ORD-001',
    date: '2024-04-15',
    status: 'delivered' as const,
    total: 279.99,
    itemCount: 1,
  },
  {
    id: 'ORD-002',
    date: '2024-04-28',
    status: 'shipped' as const,
    total: 154.98,
    itemCount: 2,
  },
  {
    id: 'ORD-003',
    date: '2024-05-10',
    status: 'processing' as const,
    total: 44.99,
    itemCount: 1,
  },
]

const statusColors: Record<string, string> = {
  pending: 'bg-gray-100 text-gray-700',
  processing: 'bg-yellow-100 text-yellow-700',
  shipped: 'bg-blue-100 text-blue-700',
  delivered: 'bg-green-100 text-green-700',
  cancelled: 'bg-red-100 text-red-700',
}

export default function AccountPage() {
  const { data: session, status } = useSession()
  const router = useRouter()

  useEffect(() => {
    if (status === 'unauthenticated') {
      router.push('/account/login')
    }
  }, [status, router])

  if (status === 'loading') {
    return (
      <div className="max-w-4xl mx-auto px-4 py-10 animate-pulse space-y-6">
        <div className="h-10 bg-gray-200 rounded w-64" />
        <div className="grid grid-cols-2 gap-4">
          <div className="h-28 bg-gray-200 rounded-xl" />
          <div className="h-28 bg-gray-200 rounded-xl" />
        </div>
        <div className="h-64 bg-gray-200 rounded-xl" />
      </div>
    )
  }

  if (!session) return null

  const totalSpent = mockOrders.reduce((sum, o) => sum + o.total, 0)

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">
          Welcome back, {session.user?.name || session.user?.email}!
        </h1>
        <p className="text-gray-500 mt-1">Manage your account and view your orders</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-8">
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 flex items-center gap-4">
          <div className="w-14 h-14 bg-blue-100 rounded-xl flex items-center justify-center">
            <Package size={28} className="text-blue-600" />
          </div>
          <div>
            <p className="text-2xl font-bold text-gray-900">{mockOrders.length}</p>
            <p className="text-sm text-gray-500">Total Orders</p>
          </div>
        </div>
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 flex items-center gap-4">
          <div className="w-14 h-14 bg-green-100 rounded-xl flex items-center justify-center">
            <DollarSign size={28} className="text-green-600" />
          </div>
          <div>
            <p className="text-2xl font-bold text-gray-900">${totalSpent.toFixed(2)}</p>
            <p className="text-sm text-gray-500">Total Spent</p>
          </div>
        </div>
      </div>

      {/* Recent Orders */}
      <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 mb-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-bold text-gray-900">Recent Orders</h2>
          <Link href="/account/orders" className="text-sm text-blue-600 hover:text-blue-700 font-medium">
            View all
          </Link>
        </div>
        <div className="space-y-3">
          {mockOrders.map((order) => (
            <div
              key={order.id}
              className="flex items-center justify-between py-3 border-b border-gray-100 last:border-0"
            >
              <div>
                <p className="font-medium text-gray-900">{order.id}</p>
                <p className="text-sm text-gray-500">{order.date} · {order.itemCount} item{order.itemCount !== 1 ? 's' : ''}</p>
              </div>
              <div className="flex items-center gap-3">
                <span
                  className={`px-2.5 py-1 text-xs font-semibold rounded-full capitalize ${statusColors[order.status]}`}
                >
                  {order.status}
                </span>
                <span className="font-semibold text-gray-900">${order.total.toFixed(2)}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Account Settings */}
      <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
        <h2 className="text-lg font-bold text-gray-900 mb-4">Account Settings</h2>
        <div className="space-y-1">
          <div className="flex items-center justify-between py-3 border-b border-gray-100">
            <div className="flex items-center gap-3 text-gray-700">
              <User size={18} className="text-gray-400" />
              <div>
                <p className="font-medium">{session.user?.name || 'N/A'}</p>
                <p className="text-sm text-gray-500">{session.user?.email}</p>
              </div>
            </div>
          </div>
          <div className="flex items-center justify-between py-3">
            <div className="flex items-center gap-3 text-gray-700">
              <Settings size={18} className="text-gray-400" />
              <p className="font-medium">Account type</p>
            </div>
            <div className="flex items-center gap-2 text-sm text-gray-500">
              Customer
              <ChevronRight size={16} />
            </div>
          </div>
        </div>
        <p className="text-xs text-gray-400 mt-4">
          This is a demo application. Account data is stored in-memory and resets on server restart.
        </p>
      </div>
    </div>
  )
}

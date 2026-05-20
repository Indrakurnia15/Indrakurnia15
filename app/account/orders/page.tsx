'use client'

import { useSession } from 'next-auth/react'
import { useRouter, useSearchParams } from 'next/navigation'
import { useEffect, Suspense } from 'react'
import Link from 'next/link'
import { Package, CheckCircle, ChevronRight } from 'lucide-react'

const mockOrders = [
  {
    id: 'ORD-001',
    date: '2024-04-15',
    status: 'delivered' as const,
    total: 279.99,
    items: [
      { name: 'Sony WH-1000XM5 Wireless Headphones', quantity: 1, price: 279.99 },
    ],
  },
  {
    id: 'ORD-002',
    date: '2024-04-28',
    status: 'shipped' as const,
    total: 154.98,
    items: [
      { name: 'Classic White Cotton T-Shirt', quantity: 2, price: 49.98 },
      { name: 'Yoga Mat Premium Non-Slip', quantity: 1, price: 44.99 },
      { name: 'Bamboo Cutting Board with Juice Groove', quantity: 2, price: 59.98 },
    ],
  },
  {
    id: 'ORD-003',
    date: '2024-05-10',
    status: 'processing' as const,
    total: 44.99,
    items: [
      { name: 'Yoga Mat Premium Non-Slip', quantity: 1, price: 44.99 },
    ],
  },
]

const statusColors: Record<string, string> = {
  pending: 'bg-gray-100 text-gray-700',
  processing: 'bg-yellow-100 text-yellow-700',
  shipped: 'bg-blue-100 text-blue-700',
  delivered: 'bg-green-100 text-green-700',
  cancelled: 'bg-red-100 text-red-700',
}

const statusDescriptions: Record<string, string> = {
  pending: 'Order received',
  processing: 'Preparing your order',
  shipped: 'On the way',
  delivered: 'Delivered successfully',
  cancelled: 'Order cancelled',
}

function OrdersContent() {
  const { data: session, status } = useSession()
  const router = useRouter()
  const searchParams = useSearchParams()
  const showSuccess = searchParams.get('success') === 'true'

  useEffect(() => {
    if (status === 'unauthenticated') {
      router.push('/account/login')
    }
  }, [status, router])

  if (status === 'loading') {
    return (
      <div className="max-w-4xl mx-auto px-4 py-10 animate-pulse space-y-4">
        {[...Array(3)].map((_, i) => (
          <div key={i} className="h-40 bg-gray-200 rounded-xl" />
        ))}
      </div>
    )
  }

  if (!session) return null

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      {showSuccess && (
        <div className="flex items-center gap-3 p-4 bg-green-50 border border-green-200 rounded-xl mb-8">
          <CheckCircle size={24} className="text-green-600 flex-shrink-0" />
          <div>
            <p className="font-semibold text-green-800">Order placed successfully!</p>
            <p className="text-sm text-green-700">
              Thank you for your purchase. Your order is being processed.
            </p>
          </div>
        </div>
      )}

      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-1">My Orders</h1>
        <p className="text-gray-500">Track and manage your orders</p>
      </div>

      {mockOrders.length > 0 ? (
        <div className="space-y-4">
          {mockOrders.map((order) => (
            <div
              key={order.id}
              className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6"
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
                <div>
                  <div className="flex items-center gap-3 mb-1">
                    <h3 className="font-bold text-gray-900">{order.id}</h3>
                    <span
                      className={`px-2.5 py-0.5 text-xs font-semibold rounded-full capitalize ${statusColors[order.status]}`}
                    >
                      {order.status}
                    </span>
                  </div>
                  <p className="text-sm text-gray-500">
                    {statusDescriptions[order.status]} · Ordered on {order.date}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-lg font-bold text-gray-900">${order.total.toFixed(2)}</p>
                  <p className="text-xs text-gray-400">
                    {order.items.length} item{order.items.length !== 1 ? 's' : ''}
                  </p>
                </div>
              </div>

              <div className="border-t border-gray-100 pt-4 space-y-2">
                {order.items.map((item, i) => (
                  <div key={i} className="flex justify-between text-sm">
                    <span className="text-gray-700">
                      {item.name} <span className="text-gray-400">×{item.quantity}</span>
                    </span>
                    <span className="text-gray-900 font-medium">${item.price.toFixed(2)}</span>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-20">
          <div className="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-6">
            <Package size={36} className="text-gray-400" />
          </div>
          <h3 className="text-xl font-semibold text-gray-700 mb-2">No orders yet</h3>
          <p className="text-gray-500 mb-6">Start shopping to see your orders here.</p>
          <Link href="/products" className="btn-primary">
            Browse Products
          </Link>
        </div>
      )}

      <div className="mt-6 text-center">
        <Link
          href="/account"
          className="inline-flex items-center gap-1 text-blue-600 hover:text-blue-700 font-medium text-sm"
        >
          Back to Account
          <ChevronRight size={16} />
        </Link>
      </div>
    </div>
  )
}

export default function OrdersPage() {
  return (
    <Suspense>
      <OrdersContent />
    </Suspense>
  )
}

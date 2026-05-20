'use client'

import Link from 'next/link'
import { ShoppingBag, ArrowLeft } from 'lucide-react'
import { useCart } from '@/context/CartContext'
import CartItemRow from '@/components/CartItemRow'

const SHIPPING_THRESHOLD = 50
const SHIPPING_COST = 9.99
const TAX_RATE = 0.08

export default function CartPage() {
  const { cartItems, cartTotal, cartCount } = useCart()

  const shipping = cartTotal >= SHIPPING_THRESHOLD || cartTotal === 0 ? 0 : SHIPPING_COST
  const tax = cartTotal * TAX_RATE
  const orderTotal = cartTotal + shipping + tax

  if (cartCount === 0) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-20 text-center">
        <div className="w-24 h-24 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-6">
          <ShoppingBag size={40} className="text-gray-400" />
        </div>
        <h2 className="text-2xl font-bold text-gray-900 mb-3">Your cart is empty</h2>
        <p className="text-gray-500 mb-8">
          Looks like you haven&apos;t added any items yet. Start shopping to fill it up!
        </p>
        <Link href="/products" className="btn-primary">
          Browse Products
        </Link>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      <Link
        href="/products"
        className="inline-flex items-center gap-2 text-blue-600 hover:text-blue-700 mb-8 font-medium"
      >
        <ArrowLeft size={18} />
        Continue Shopping
      </Link>

      <h1 className="text-3xl font-bold text-gray-900 mb-2">Shopping Cart</h1>
      <p className="text-gray-500 mb-8">
        {cartCount} item{cartCount !== 1 ? 's' : ''} in your cart
      </p>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Cart Items */}
        <div className="lg:col-span-2 space-y-4">
          {cartItems.map((item) => (
            <CartItemRow key={item.product.id} item={item} />
          ))}
        </div>

        {/* Order Summary */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-2xl shadow-md border border-gray-100 p-6 sticky top-24">
            <h2 className="text-xl font-bold text-gray-900 mb-6">Order Summary</h2>

            <div className="space-y-3 mb-6">
              <div className="flex justify-between text-gray-600">
                <span>Subtotal ({cartCount} items)</span>
                <span>${cartTotal.toFixed(2)}</span>
              </div>
              <div className="flex justify-between text-gray-600">
                <span>Shipping</span>
                {shipping === 0 ? (
                  <span className="text-green-600 font-medium">Free</span>
                ) : (
                  <span>${shipping.toFixed(2)}</span>
                )}
              </div>
              {cartTotal > 0 && cartTotal < SHIPPING_THRESHOLD && (
                <p className="text-xs text-blue-600 bg-blue-50 rounded-lg p-2">
                  Add ${(SHIPPING_THRESHOLD - cartTotal).toFixed(2)} more for free shipping!
                </p>
              )}
              <div className="flex justify-between text-gray-600">
                <span>Tax (8%)</span>
                <span>${tax.toFixed(2)}</span>
              </div>
              <div className="border-t border-gray-200 pt-3 flex justify-between font-bold text-gray-900 text-lg">
                <span>Total</span>
                <span>${orderTotal.toFixed(2)}</span>
              </div>
            </div>

            <Link
              href="/checkout"
              className="block w-full text-center py-4 bg-blue-600 text-white font-bold text-lg rounded-xl hover:bg-blue-700 transition-colors shadow-md"
            >
              Proceed to Checkout
            </Link>

            <p className="text-xs text-gray-400 text-center mt-3">
              Secure checkout powered by Stripe
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

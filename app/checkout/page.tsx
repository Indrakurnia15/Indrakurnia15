'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { ShieldCheck, AlertCircle, CreditCard } from 'lucide-react'
import { useCart } from '@/context/CartContext'
import { loadStripe } from '@stripe/stripe-js'
import {
  Elements,
  CardElement,
  useStripe,
  useElements,
} from '@stripe/react-stripe-js'

const stripePublishableKey =
  process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY || 'pk_test_placeholder'

const stripePromise = stripePublishableKey.startsWith('pk_test_51')
  ? loadStripe(stripePublishableKey)
  : null

const SHIPPING_THRESHOLD = 50
const SHIPPING_COST = 9.99
const TAX_RATE = 0.08

const CARD_ELEMENT_OPTIONS = {
  style: {
    base: {
      fontSize: '16px',
      color: '#1f2937',
      fontFamily: 'inherit',
      '::placeholder': {
        color: '#9ca3af',
      },
    },
    invalid: {
      color: '#ef4444',
    },
  },
}

function CheckoutForm() {
  const stripe = useStripe()
  const elements = useElements()
  const router = useRouter()
  const { cartItems, cartTotal, clearCart } = useCart()

  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [isProcessing, setIsProcessing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [clientSecret, setClientSecret] = useState<string | null>(null)
  const [isTestMode] = useState(!stripePublishableKey.startsWith('pk_test_51'))

  const shipping = cartTotal >= SHIPPING_THRESHOLD ? 0 : SHIPPING_COST
  const tax = cartTotal * TAX_RATE
  const orderTotal = cartTotal + shipping + tax

  useEffect(() => {
    if (cartItems.length === 0) return

    const createPaymentIntent = async () => {
      try {
        const res = await fetch('/api/checkout', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            items: cartItems.map((item) => ({
              productId: item.product.id,
              quantity: item.quantity,
              price: item.product.price,
              name: item.product.name,
            })),
            total: Math.round(orderTotal * 100),
          }),
        })
        const data = await res.json()
        if (data.clientSecret) {
          setClientSecret(data.clientSecret)
        }
      } catch (err) {
        console.error('Failed to create payment intent:', err)
      }
    }

    createPaymentIntent()
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!name || !email) {
      setError('Please fill in all required fields.')
      return
    }

    setIsProcessing(true)
    setError(null)

    // Demo mode: simulate successful payment
    if (isTestMode || !stripe || !elements || !clientSecret) {
      await new Promise((resolve) => setTimeout(resolve, 1500))
      clearCart()
      router.push('/account/orders?success=true')
      return
    }

    const cardElement = elements.getElement(CardElement)
    if (!cardElement) {
      setError('Card element not found.')
      setIsProcessing(false)
      return
    }

    const { error: stripeError, paymentIntent } = await stripe.confirmCardPayment(
      clientSecret,
      {
        payment_method: {
          card: cardElement,
          billing_details: { name, email },
        },
      }
    )

    if (stripeError) {
      setError(stripeError.message || 'Payment failed. Please try again.')
      setIsProcessing(false)
    } else if (paymentIntent?.status === 'succeeded') {
      clearCart()
      router.push('/account/orders?success=true')
    }
  }

  if (cartItems.length === 0) {
    return (
      <div className="text-center py-20">
        <p className="text-gray-600 text-lg">Your cart is empty.</p>
      </div>
    )
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
      {/* Left: Form */}
      <div>
        <h2 className="text-xl font-bold text-gray-900 mb-6">Payment Details</h2>

        {/* Test Mode Notice */}
        {isTestMode && (
          <div className="flex items-start gap-3 p-4 bg-amber-50 border border-amber-200 rounded-xl mb-6">
            <AlertCircle size={20} className="text-amber-600 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-semibold text-amber-800">Demo Mode</p>
              <p className="text-sm text-amber-700 mt-1">
                Stripe is in demo mode. Click &quot;Place Order&quot; to simulate a successful payment.
                For real Stripe integration, add your API keys to .env.local.
              </p>
            </div>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              Full Name <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="John Doe"
              required
              className="input-field"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              Email Address <span className="text-red-500">*</span>
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="john@example.com"
              required
              className="input-field"
            />
          </div>

          {!isTestMode && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">
                Card Details <span className="text-red-500">*</span>
              </label>
              <div className="input-field py-4">
                <CardElement options={CARD_ELEMENT_OPTIONS} />
              </div>
              <p className="text-xs text-gray-400 mt-1">
                Test card: 4242 4242 4242 4242, any future expiry, any CVC
              </p>
            </div>
          )}

          {error && (
            <div className="flex items-start gap-2 p-3 bg-red-50 border border-red-200 rounded-lg">
              <AlertCircle size={16} className="text-red-500 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-red-700">{error}</p>
            </div>
          )}

          <button
            type="submit"
            disabled={isProcessing}
            className="w-full flex items-center justify-center gap-3 py-4 bg-blue-600 text-white font-bold text-lg rounded-xl hover:bg-blue-700 transition-colors disabled:opacity-60 disabled:cursor-not-allowed shadow-md"
          >
            {isProcessing ? (
              <>
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Processing...
              </>
            ) : (
              <>
                <CreditCard size={22} />
                Place Order — ${orderTotal.toFixed(2)}
              </>
            )}
          </button>
        </form>

        <div className="flex items-center gap-2 mt-4 text-sm text-gray-500">
          <ShieldCheck size={16} className="text-green-600" />
          Your payment info is encrypted and secure
        </div>
      </div>

      {/* Right: Order Summary */}
      <div>
        <h2 className="text-xl font-bold text-gray-900 mb-6">Order Summary</h2>
        <div className="bg-gray-50 rounded-2xl p-6 border border-gray-200">
          <div className="space-y-3 mb-4">
            {cartItems.map((item) => (
              <div key={item.product.id} className="flex justify-between text-sm">
                <span className="text-gray-700">
                  {item.product.name}{' '}
                  <span className="text-gray-400">×{item.quantity}</span>
                </span>
                <span className="font-medium text-gray-900">
                  ${(item.product.price * item.quantity).toFixed(2)}
                </span>
              </div>
            ))}
          </div>
          <div className="border-t border-gray-200 pt-4 space-y-2">
            <div className="flex justify-between text-sm text-gray-600">
              <span>Subtotal</span>
              <span>${cartTotal.toFixed(2)}</span>
            </div>
            <div className="flex justify-between text-sm text-gray-600">
              <span>Shipping</span>
              {shipping === 0 ? (
                <span className="text-green-600">Free</span>
              ) : (
                <span>${shipping.toFixed(2)}</span>
              )}
            </div>
            <div className="flex justify-between text-sm text-gray-600">
              <span>Tax (8%)</span>
              <span>${tax.toFixed(2)}</span>
            </div>
            <div className="border-t border-gray-300 pt-3 flex justify-between font-bold text-gray-900 text-lg">
              <span>Total</span>
              <span>${orderTotal.toFixed(2)}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default function CheckoutPage() {
  const { cartItems } = useCart()

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      <h1 className="text-3xl font-bold text-gray-900 mb-10">Checkout</h1>
      {stripePromise ? (
        <Elements stripe={stripePromise}>
          <CheckoutForm />
        </Elements>
      ) : (
        <CheckoutForm />
      )}
    </div>
  )
}

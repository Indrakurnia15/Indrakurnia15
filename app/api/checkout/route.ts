import { NextRequest, NextResponse } from 'next/server'
import { stripe } from '@/lib/stripe'

interface CheckoutItem {
  productId: string
  quantity: number
  price: number
  name: string
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.json()
    const { items, total } = body as { items: CheckoutItem[]; total: number }

    if (!items || items.length === 0) {
      return NextResponse.json({ error: 'Cart is empty.' }, { status: 400 })
    }

    const amountInCents =
      total ||
      Math.round(
        items.reduce((sum, item) => sum + item.price * item.quantity, 0) * 100
      )

    // Check if Stripe is configured with a real key
    const stripeKey = process.env.STRIPE_SECRET_KEY || ''
    if (!stripeKey || stripeKey === 'sk_test_placeholder' || !stripeKey.startsWith('sk_')) {
      // Return a mock client secret for demo mode
      return NextResponse.json({
        clientSecret: null,
        demo: true,
        message: 'Demo mode: Stripe not configured. Set STRIPE_SECRET_KEY in .env.local for real payments.',
      })
    }

    const paymentIntent = await stripe.paymentIntents.create({
      amount: amountInCents,
      currency: 'usd',
      automatic_payment_methods: { enabled: true },
      metadata: {
        itemCount: items.length.toString(),
        itemNames: items.map((i) => i.name).join(', ').substring(0, 500),
      },
    })

    return NextResponse.json({ clientSecret: paymentIntent.client_secret })
  } catch (error) {
    console.error('Checkout error:', error)
    return NextResponse.json(
      { error: 'Failed to create payment intent.' },
      { status: 500 }
    )
  }
}

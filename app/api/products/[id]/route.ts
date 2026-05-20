import { NextRequest, NextResponse } from 'next/server'
import { products } from '@/data/products'

export async function GET(
  _req: NextRequest,
  { params }: { params: { id: string } }
) {
  const product = products.find((p) => p.id === params.id)

  if (!product) {
    return NextResponse.json({ error: 'Product not found.' }, { status: 404 })
  }

  return NextResponse.json(product)
}

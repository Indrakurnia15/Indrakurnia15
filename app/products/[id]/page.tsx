import { notFound } from 'next/navigation'
import { products } from '@/data/products'
import ProductDetail from './ProductDetail'

interface Props {
  params: { id: string }
}

export default function ProductDetailPage({ params }: Props) {
  const product = products.find((p) => p.id === params.id)

  if (!product) {
    notFound()
  }

  return <ProductDetail product={product} />
}

export function generateStaticParams() {
  return products.map((p) => ({ id: p.id }))
}

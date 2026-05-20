'use client'

import { useState } from 'react'
import Image from 'next/image'
import Link from 'next/link'
import { ArrowLeft, Minus, Plus, ShoppingCart, CheckCircle } from 'lucide-react'
import { Product } from '@/types'
import { useCart } from '@/context/CartContext'
import StarRating from '@/components/StarRating'

interface Props {
  product: Product
}

export default function ProductDetail({ product }: Props) {
  const { addToCart } = useCart()
  const [quantity, setQuantity] = useState(1)
  const [added, setAdded] = useState(false)

  const handleAddToCart = () => {
    addToCart(product, quantity)
    setAdded(true)
    setTimeout(() => setAdded(false), 2000)
  }

  const stockStatus =
    product.stock === 0
      ? 'Out of Stock'
      : product.stock < 10
      ? `Only ${product.stock} left`
      : 'In Stock'

  const stockColor =
    product.stock === 0
      ? 'text-red-600'
      : product.stock < 10
      ? 'text-orange-600'
      : 'text-green-600'

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      <Link
        href="/products"
        className="inline-flex items-center gap-2 text-blue-600 hover:text-blue-700 mb-8 font-medium"
      >
        <ArrowLeft size={18} />
        Back to Products
      </Link>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
        {/* Image */}
        <div className="relative aspect-square rounded-2xl overflow-hidden bg-gray-100 shadow-md">
          <Image
            src={product.image}
            alt={product.name}
            fill
            className="object-cover"
            sizes="(max-width: 1024px) 100vw, 50vw"
            priority
          />
        </div>

        {/* Details */}
        <div className="flex flex-col">
          <div className="mb-2">
            <span className="px-3 py-1 text-sm font-semibold bg-blue-100 text-blue-700 rounded-full">
              {product.category}
            </span>
          </div>

          <h1 className="text-3xl font-bold text-gray-900 mt-3 mb-4">{product.name}</h1>

          <div className="flex items-center gap-3 mb-4">
            <StarRating rating={product.rating} size={20} />
            <span className="text-blue-600 font-semibold">{product.rating.toFixed(1)}</span>
            <span className="text-gray-500">
              ({product.reviewCount.toLocaleString()} reviews)
            </span>
          </div>

          <div className="flex items-baseline gap-2 mb-4">
            <span className="text-4xl font-extrabold text-gray-900">
              ${product.price.toFixed(2)}
            </span>
          </div>

          <p className={`text-sm font-semibold mb-6 ${stockColor}`}>{stockStatus}</p>

          <p className="text-gray-600 leading-relaxed mb-8">{product.description}</p>

          {/* Quantity & Add to Cart */}
          {product.stock > 0 && (
            <div className="space-y-4">
              <div className="flex items-center gap-4">
                <span className="text-sm font-medium text-gray-700">Quantity:</span>
                <div className="flex items-center border border-gray-300 rounded-lg overflow-hidden">
                  <button
                    onClick={() => setQuantity(Math.max(1, quantity - 1))}
                    className="p-3 hover:bg-gray-100 transition-colors"
                    aria-label="Decrease quantity"
                  >
                    <Minus size={16} />
                  </button>
                  <span className="px-4 py-2 text-center w-12 font-medium">{quantity}</span>
                  <button
                    onClick={() => setQuantity(Math.min(product.stock, quantity + 1))}
                    className="p-3 hover:bg-gray-100 transition-colors"
                    aria-label="Increase quantity"
                  >
                    <Plus size={16} />
                  </button>
                </div>
              </div>

              <button
                onClick={handleAddToCart}
                className={`w-full sm:w-auto flex items-center justify-center gap-3 px-8 py-4 rounded-xl font-bold text-lg transition-all ${
                  added
                    ? 'bg-green-600 text-white'
                    : 'bg-blue-600 text-white hover:bg-blue-700 shadow-md hover:shadow-lg'
                }`}
              >
                {added ? (
                  <>
                    <CheckCircle size={22} />
                    Added to Cart!
                  </>
                ) : (
                  <>
                    <ShoppingCart size={22} />
                    Add to Cart
                  </>
                )}
              </button>

              <Link
                href="/cart"
                className="block w-full sm:w-auto text-center px-8 py-4 rounded-xl font-bold text-lg border-2 border-blue-600 text-blue-600 hover:bg-blue-50 transition-colors"
              >
                View Cart
              </Link>
            </div>
          )}

          {/* Info */}
          <div className="mt-8 pt-8 border-t border-gray-200 space-y-2">
            <p className="flex items-center gap-2 text-sm text-gray-600">
              <span className="w-2 h-2 bg-green-500 rounded-full inline-block" />
              Free shipping on orders over $50
            </p>
            <p className="flex items-center gap-2 text-sm text-gray-600">
              <span className="w-2 h-2 bg-blue-500 rounded-full inline-block" />
              30-day hassle-free returns
            </p>
            <p className="flex items-center gap-2 text-sm text-gray-600">
              <span className="w-2 h-2 bg-purple-500 rounded-full inline-block" />
              Secure checkout powered by Stripe
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

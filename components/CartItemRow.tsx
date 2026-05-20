'use client'

import Image from 'next/image'
import { Minus, Plus, Trash2 } from 'lucide-react'
import { CartItem } from '@/types'
import { useCart } from '@/context/CartContext'

interface CartItemRowProps {
  item: CartItem
}

export default function CartItemRow({ item }: CartItemRowProps) {
  const { updateQuantity, removeFromCart } = useCart()

  return (
    <div className="flex gap-4 p-4 bg-white rounded-xl shadow-sm border border-gray-100">
      <div className="relative w-24 h-24 flex-shrink-0 rounded-lg overflow-hidden bg-gray-100">
        <Image
          src={item.product.image}
          alt={item.product.name}
          fill
          className="object-cover"
          sizes="96px"
        />
      </div>

      <div className="flex-grow min-w-0">
        <h3 className="font-semibold text-gray-900 truncate">{item.product.name}</h3>
        <p className="text-sm text-gray-500 mt-0.5">{item.product.category}</p>
        <p className="text-sm text-gray-600 mt-1">${item.product.price.toFixed(2)} each</p>
      </div>

      <div className="flex flex-col items-end justify-between flex-shrink-0">
        <p className="font-bold text-gray-900">
          ${(item.product.price * item.quantity).toFixed(2)}
        </p>

        <div className="flex items-center gap-2 mt-2">
          <button
            onClick={() => updateQuantity(item.product.id, item.quantity - 1)}
            className="p-1.5 rounded-lg bg-gray-100 hover:bg-gray-200 transition-colors"
            aria-label="Decrease quantity"
          >
            <Minus size={14} />
          </button>
          <span className="w-8 text-center font-medium text-sm">{item.quantity}</span>
          <button
            onClick={() => updateQuantity(item.product.id, item.quantity + 1)}
            className="p-1.5 rounded-lg bg-gray-100 hover:bg-gray-200 transition-colors"
            aria-label="Increase quantity"
          >
            <Plus size={14} />
          </button>
          <button
            onClick={() => removeFromCart(item.product.id)}
            className="p-1.5 rounded-lg text-red-500 hover:bg-red-50 transition-colors ml-1"
            aria-label="Remove item"
          >
            <Trash2 size={14} />
          </button>
        </div>
      </div>
    </div>
  )
}

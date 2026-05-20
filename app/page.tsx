import Link from 'next/link'
import {
  ArrowRight,
  Cpu,
  Shirt,
  Leaf,
  Dumbbell,
  Truck,
  RotateCcw,
  ShieldCheck,
  Headphones,
} from 'lucide-react'
import { products } from '@/data/products'
import ProductCard from '@/components/ProductCard'

const categories = [
  {
    name: 'Electronics',
    icon: Cpu,
    description: 'Gadgets & tech',
    color: 'bg-blue-100 text-blue-700',
    href: '/products?category=Electronics',
  },
  {
    name: 'Clothing',
    icon: Shirt,
    description: 'Fashion & apparel',
    color: 'bg-purple-100 text-purple-700',
    href: '/products?category=Clothing',
  },
  {
    name: 'Home & Garden',
    icon: Leaf,
    description: 'For your home',
    color: 'bg-green-100 text-green-700',
    href: '/products?category=Home+%26+Garden',
  },
  {
    name: 'Sports',
    icon: Dumbbell,
    description: 'Fitness & outdoor',
    color: 'bg-orange-100 text-orange-700',
    href: '/products?category=Sports',
  },
]

const trustBadges = [
  {
    icon: Truck,
    title: 'Free Shipping',
    description: 'On orders over $50',
    color: 'text-blue-600',
  },
  {
    icon: RotateCcw,
    title: '30-Day Returns',
    description: 'No questions asked',
    color: 'text-green-600',
  },
  {
    icon: ShieldCheck,
    title: 'Secure Payments',
    description: 'SSL encrypted checkout',
    color: 'text-purple-600',
  },
  {
    icon: Headphones,
    title: '24/7 Support',
    description: 'Always here to help',
    color: 'text-orange-600',
  },
]

const featuredProducts = products.slice(0, 4)

export default function HomePage() {
  return (
    <div>
      {/* Hero Section */}
      <section className="relative bg-gradient-to-br from-blue-700 via-blue-600 to-indigo-700 text-white overflow-hidden">
        <div className="absolute inset-0 opacity-10">
          <div className="absolute top-10 left-20 w-72 h-72 bg-white rounded-full blur-3xl" />
          <div className="absolute bottom-10 right-20 w-96 h-96 bg-white rounded-full blur-3xl" />
        </div>
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24 md:py-32">
          <div className="max-w-2xl">
            <h1 className="text-4xl md:text-6xl font-extrabold leading-tight mb-6 text-balance">
              Shop Quality Products
            </h1>
            <p className="text-xl md:text-2xl text-blue-100 mb-8 leading-relaxed">
              Discover curated electronics, clothing, home goods, and sports gear — all at
              unbeatable prices, delivered to your door.
            </p>
            <div className="flex flex-col sm:flex-row gap-4">
              <Link
                href="/products"
                className="inline-flex items-center justify-center gap-2 px-8 py-4 bg-white text-blue-700 font-bold text-lg rounded-xl hover:bg-blue-50 transition-colors shadow-lg"
              >
                Shop Now
                <ArrowRight size={20} />
              </Link>
              <Link
                href="/account/register"
                className="inline-flex items-center justify-center gap-2 px-8 py-4 border-2 border-white text-white font-bold text-lg rounded-xl hover:bg-white/10 transition-colors"
              >
                Create Account
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Categories */}
      <section className="py-16 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-10">
            <h2 className="text-3xl font-bold text-gray-900 mb-3">Shop by Category</h2>
            <p className="text-gray-500">Find exactly what you&apos;re looking for</p>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {categories.map((cat) => {
              const Icon = cat.icon
              return (
                <Link
                  key={cat.name}
                  href={cat.href}
                  className="group flex flex-col items-center p-6 bg-white rounded-2xl shadow-sm hover:shadow-md transition-all border border-gray-100 hover:border-blue-200"
                >
                  <div
                    className={`w-16 h-16 rounded-xl ${cat.color} flex items-center justify-center mb-3 group-hover:scale-110 transition-transform`}
                  >
                    <Icon size={28} />
                  </div>
                  <h3 className="font-semibold text-gray-900 text-center">{cat.name}</h3>
                  <p className="text-sm text-gray-500 text-center mt-1">{cat.description}</p>
                </Link>
              )
            })}
          </div>
        </div>
      </section>

      {/* Featured Products */}
      <section className="py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between mb-10">
            <div>
              <h2 className="text-3xl font-bold text-gray-900 mb-1">Featured Products</h2>
              <p className="text-gray-500">Our top picks just for you</p>
            </div>
            <Link
              href="/products"
              className="hidden sm:inline-flex items-center gap-2 text-blue-600 font-semibold hover:text-blue-700 transition-colors"
            >
              View all
              <ArrowRight size={18} />
            </Link>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {featuredProducts.map((product) => (
              <ProductCard key={product.id} product={product} />
            ))}
          </div>
          <div className="text-center mt-8 sm:hidden">
            <Link
              href="/products"
              className="inline-flex items-center gap-2 text-blue-600 font-semibold"
            >
              View all products
              <ArrowRight size={18} />
            </Link>
          </div>
        </div>
      </section>

      {/* Trust Badges */}
      <section className="py-16 bg-gray-50 border-t border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            {trustBadges.map((badge) => {
              const Icon = badge.icon
              return (
                <div key={badge.title} className="flex flex-col items-center text-center">
                  <div className={`mb-3 ${badge.color}`}>
                    <Icon size={36} />
                  </div>
                  <h3 className="font-semibold text-gray-900 mb-1">{badge.title}</h3>
                  <p className="text-sm text-gray-500">{badge.description}</p>
                </div>
              )
            })}
          </div>
        </div>
      </section>
    </div>
  )
}

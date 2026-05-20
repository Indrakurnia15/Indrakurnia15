export interface Product {
  id: string
  name: string
  description: string
  price: number
  category: string
  image: string
  stock: number
  rating: number
  reviewCount: number
}

export interface CartItem {
  product: Product
  quantity: number
}

export interface User {
  id: string
  name: string
  email: string
  password: string
  createdAt: string
}

export interface OrderItem {
  productId: string
  productName: string
  price: number
  quantity: number
  image: string
}

export interface Order {
  id: string
  userId: string
  items: OrderItem[]
  total: number
  status: 'pending' | 'processing' | 'shipped' | 'delivered' | 'cancelled'
  createdAt: string
  shippingAddress?: {
    name: string
    email: string
    address: string
    city: string
    state: string
    zip: string
  }
}

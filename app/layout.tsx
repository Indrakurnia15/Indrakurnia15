import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { getServerSession } from 'next-auth'
import { authOptions } from '@/lib/auth'
import SessionProviderWrapper from './SessionProviderWrapper'
import { CartProvider } from '@/context/CartContext'
import Navbar from '@/components/Navbar'
import Footer from '@/components/Footer'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: {
    default: 'ShopLocal - Your Neighborhood Store',
    template: '%s | ShopLocal',
  },
  description:
    'Quality products for everyday life. Electronics, clothing, home & garden, and sports gear — all in one place.',
  keywords: ['shop', 'ecommerce', 'electronics', 'clothing', 'home', 'sports'],
}

export default async function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const session = await getServerSession(authOptions)

  return (
    <html lang="en">
      <body className={`${inter.className} min-h-screen flex flex-col`}>
        <SessionProviderWrapper session={session}>
          <CartProvider>
            <Navbar />
            <main className="flex-grow">{children}</main>
            <Footer />
          </CartProvider>
        </SessionProviderWrapper>
      </body>
    </html>
  )
}

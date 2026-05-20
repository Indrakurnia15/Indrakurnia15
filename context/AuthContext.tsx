'use client'

// This is a thin wrapper around next-auth/react for consistency.
// Use useSession directly from next-auth/react in most cases.
export { useSession, signIn, signOut } from 'next-auth/react'

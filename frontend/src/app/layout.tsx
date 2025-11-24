import './globals.css'
import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Mental Health ChatBot',
  description: 'A professional mental health assistant for students',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-black text-white bg-grid">
        <div className="pointer-events-none fixed inset-0 bg-[radial-gradient(50%_50%_at_50%_0%,rgba(0,229,255,0.15),transparent_60%)]" />
        <main className="relative z-10">{children}</main>
      </body>
    </html>
  )
}




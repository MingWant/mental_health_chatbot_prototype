"use client";
import Link from 'next/link'
import { useEffect, useState } from 'react'
import { getAuth, clearAuth } from '@/lib/auth'

export default function Home() {
  const [auth, setAuthState] = useState<any>(null)
  useEffect(() => {
    setAuthState(getAuth())
  }, [])
  return (
    <div className="px-6 py-16 md:py-24">
      <header className="mx-auto max-w-6xl flex items-center justify-between">
        <div className="text-xl font-semibold tracking-wide">MHB</div>
        <nav className="space-x-6 text-sm text-white/70">
          <Link href="/chat">Chat</Link>
          {/* Hide Wellness Tools for now */}
          {/* <Link href="/wellness">Wellness Tools</Link> */}
          <Link href="/rag">RAG Management</Link>
          {auth ? (
            <button onClick={() => { clearAuth(); setAuthState(null) }} className="ml-4 underline">Logout</button>
          ) : (
            <Link href="/auth" className="ml-4 underline">Login</Link>
          )}
        </nav>
      </header>
      <section className="mx-auto mt-24 max-w-5xl text-center">
        <h1 className="text-5xl md:text-7xl font-bold tracking-tight">
          Self-Care Strategies
          <span className="block mt-3 bg-gradient-to-r from-primary-400 to-white bg-clip-text text-transparent">for Students</span>
        </h1>
        <p className="mt-6 text-white/70 max-w-2xl mx-auto">
          Your compassionate AI companion for managing stress, tracking mood, and building healthy self-care habits. 
          Evidence-based strategies to support your mental health journey.
        </p>
        <div className="mt-10 flex items-center justify-center gap-4">
          <Link href="/chat" className="neon-border rounded-lg px-6 py-3 bg-white/5 hover:bg-white/10 transition">Start Chatting</Link>
          {/* Hide Wellness CTA */}
          {/* <Link href="/wellness" className="neon-border rounded-lg px-6 py-3 bg-white/5 hover:bg-white/10 transition">Wellness Tools</Link> */}
          <Link href="/rag" className="px-6 py-3 rounded-lg bg-primary-500 text-black font-medium shadow-glow">RAG Management</Link>
          {auth ? (
            <button onClick={() => { clearAuth(); setAuthState(null) }} className="px-6 py-3 rounded-lg bg-white/10 hover:bg-white/20 transition">Logout</button>
          ) : (
            <Link href="/auth" className="px-6 py-3 rounded-lg bg-white/10 hover:bg-white/20 transition">Login</Link>
          )}
        </div>
      </section>
      <section className="mx-auto mt-24 max-w-6xl grid md:grid-cols-3 gap-6">
        {[
          {
            title: "Mental Health ChatBot",
            description: "Intelligent conversation partner for emotional support and self-care guidance.",
            link: "/chat"
          },
          // Hide Wellness card for now
          // {
          //   title: "Wellness Tools",
          //   description: "Professional mental health tools for emotion assessment, meditation guidance, and self-care planning.",
          //   link: "/wellness"
          // },
          {
            title: "RAG Management", 
            description: "Upload and manage mental health resources and educational content.",
            link: "/rag"
          }
        ].map((feature, i) => (
          <Link key={i} href={feature.link}>
            <div className="rounded-2xl border border-white/10 p-6 bg-white/[0.02] backdrop-blur-sm neon-border hover:bg-white/[0.05] transition">
              <div className="text-primary-400 text-sm">Feature</div>
              <div className="mt-2 text-xl font-semibold">{feature.title}</div>
              <p className="mt-2 text-white/60 text-sm">{feature.description}</p>
            </div>
          </Link>
        ))}
      </section>
      <section className="mx-auto mt-24 max-w-4xl">
        <h2 className="text-3xl font-bold text-center mb-12">Mental Health Resources</h2>
        <div className="grid md:grid-cols-2 gap-6">
          <div className="rounded-xl border border-white/10 p-6 bg-white/[0.02]">
            <h3 className="text-lg font-semibold mb-3">Crisis Support</h3>
            <ul className="space-y-2 text-sm text-white/70">
              <li>• National Suicide Prevention Lifeline: 988</li>
              <li>• Crisis Text Line: Text HOME to 741741</li>
              <li>• Emergency: 911</li>
            </ul>
          </div>
          <div className="rounded-xl border border-white/10 p-6 bg-white/[0.02]">
            <h3 className="text-lg font-semibold mb-3">Self-Care Tips</h3>
            <ul className="space-y-2 text-sm text-white/70">
              <li>• Practice deep breathing exercises</li>
              <li>• Maintain regular sleep schedule</li>
              <li>• Stay connected with loved ones</li>
              <li>• Seek professional help when needed</li>
            </ul>
          </div>
        </div>
      </section>
    </div>
  )
}

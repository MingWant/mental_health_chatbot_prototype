"use client";
import { useState } from 'react'
import { setAuth, getAuth, clearAuth } from '@/lib/auth'

export default function AuthPage() {
  const [mode, setMode] = useState<'login' | 'register'>("login")
  const [username, setUsername] = useState("")
  // Email field removed from registration for now
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [inviteCode, setInviteCode] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'

  const onSubmit = async () => {
    setLoading(true)
    setError("")
    try {
      if (mode === 'login') {
        const res = await fetch(`${apiUrl}/api/v1/auth/login`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ username, password })
        })
        if (!res.ok) throw new Error((await res.json()).detail || 'Login failed')
        const data = await res.json()
        setAuth({ user_id: data.user_id, username: data.username, token: data.token })
        window.location.href = '/chat'
      } else {
        const res = await fetch(`${apiUrl}/api/v1/auth/register`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ username, password, invite_code: inviteCode })
        })
        if (!res.ok) throw new Error((await res.json()).detail || 'Register failed')
        const data = await res.json()
        setAuth({ user_id: data.user_id, username: data.username, token: data.token })
        window.location.href = '/chat'
      }
    } catch (e: any) {
      setError(e.message || 'Operation failed')
    } finally {
      setLoading(false)
    }
  }

  const authed = getAuth()

  return (
    <div className="flex min-h-screen items-center justify-center bg-black">
      <div className="w-full max-w-md bg-white/[0.02] border border-white/10 rounded-lg p-6">
        <div className="flex items-center justify-between">
          <div className="text-lg font-semibold">{mode === 'login' ? 'Login' : 'Register'}</div>
          <button className="text-xs text-primary-400" onClick={() => setMode(mode === 'login' ? 'register' : 'login')}>
            {mode === 'login' ? 'Need an account?' : 'Have an account?'}
          </button>
        </div>
        {authed && (
          <div className="mt-3 text-xs text-white/60">Logged in as {authed.username} <button className="ml-2 underline" onClick={() => { clearAuth(); window.location.reload() }}>Logout</button></div>
        )}

        <div className="space-y-3 mt-4">
          <input value={username} onChange={e => setUsername(e.target.value)} placeholder="Username" className="w-full px-3 py-2 bg-white/[0.04] border border-white/10 rounded" />
          {/* Email field removed */}
          <input type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="Password" className="w-full px-3 py-2 bg-white/[0.04] border border-white/10 rounded" />
          {mode === 'register' && (
            <input value={inviteCode} onChange={e => setInviteCode(e.target.value)} placeholder="Invite code" className="w-full px-3 py-2 bg-white/[0.04] border border-white/10 rounded" />
          )}
        </div>

        {error && <div className="mt-3 text-sm text-red-400">{error}</div>}

        <button onClick={onSubmit} disabled={loading} className="w-full mt-4 px-4 py-2 bg-primary-500 text-black rounded disabled:opacity-50">
          {loading ? 'Please wait...' : (mode === 'login' ? 'Login' : 'Register')}
        </button>
      </div>
    </div>
  )
}


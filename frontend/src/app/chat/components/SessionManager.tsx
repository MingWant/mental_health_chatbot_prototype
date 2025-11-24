"use client";
import { useState, useEffect } from 'react'
import { getAuth } from '@/lib/auth'

export interface Session {
  id: number
  session_id: string
  user_id: string
  agent_type: string
  title: string
  created_at: string
  updated_at: string
}

interface SessionManagerProps {
  currentSessionId: string
  onSessionChange: (sessionId: string) => void
  onSessionDelete: (sessionId: string) => void
  onLoadHistory: (sessionId: string) => void
  refreshKey?: number
}

export default function SessionManager({
  currentSessionId,
  onSessionChange,
  onSessionDelete,
  onLoadHistory,
  refreshKey
}: SessionManagerProps) {
  const [sessions, setSessions] = useState<Session[]>([])
  const [loading, setLoading] = useState(false)
  const [showSessions, setShowSessions] = useState(false)
  const [newSessionTitle, setNewSessionTitle] = useState('')

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'

  // Load session list
  const loadSessions = async () => {
    setLoading(true)
    try {
      const auth = getAuth()
      const response = await fetch(`${apiUrl}/api/v1/chat/sessions?user_id=${auth?.user_id || 1}&agent_type=mental_health`)
      if (response.ok) {
        const data = await response.json()
        const sessions = data.sessions || (Array.isArray(data) ? data : [])
        
        // Ensure sessions are sorted by time in descending order (backend already sorted, but frontend confirms)
        const sortedSessions = sessions.sort((a: any, b: any) => {
          const timeA = new Date(a.updated_at || a.created_at || '').getTime()
          const timeB = new Date(b.updated_at || b.created_at || '').getTime()
          return timeB - timeA // Descending order, newest first
        })
        
        setSessions(sortedSessions)
      }
    } catch (error) {
      console.error('Failed to load sessions:', error)
    } finally {
      setLoading(false)
    }
  }

  // Create new session
  const createNewSession = async () => {
    if (!newSessionTitle.trim()) return

    try {
      const auth = getAuth()
      const response = await fetch(`${apiUrl}/api/v1/chat/sessions?agent_type=mental_health&user_id=${auth?.user_id || 1}&title=${encodeURIComponent(newSessionTitle)}`, {
        method: 'POST'
      })
      
      if (response.ok) {
        const sessionData = await response.json()
        // Add new session to the top of the list (because backend already sorts by time in descending order)
        setSessions(prev => [sessionData, ...prev])
        onSessionChange(sessionData.session_id)
        setNewSessionTitle('')
        setShowSessions(false)
      }
    } catch (error) {
      console.error('Failed to create session:', error)
    }
  }

  // Delete session
  const deleteSession = async (sessionId: string) => {
    if (!confirm('Are you sure you want to delete this session? This action cannot be undone.')) return

    try {
      const auth = getAuth()
      const response = await fetch(`${apiUrl}/api/v1/chat/sessions/${sessionId}?user_id=${auth?.user_id || 1}&agent_type=mental_health`, {
        method: 'DELETE'
      })
      
      if (response.ok) {
        setSessions(prev => prev.filter(s => s.session_id !== sessionId))
        onSessionDelete(sessionId)
      }
    } catch (error) {
      console.error('Failed to delete session:', error)
    }
  }

  // Switch session
  const switchSession = async (sessionId: string) => {
    try {
      // First load history, then switch session
      await onLoadHistory(sessionId);
      onSessionChange(sessionId);
      setShowSessions(false);
    } catch (error) {
      console.error('Failed to switch session:', error);
    }
  }

  useEffect(() => {
    loadSessions()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [refreshKey])

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffInHours = (now.getTime() - date.getTime()) / (1000 * 60 * 60)
    
    if (diffInHours < 24) {
      return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
    } else if (diffInHours < 168) { // 7 days
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
    } else {
      return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })
    }
  }

  return (
    <div className="relative">
      {/* Session toggle button */}
      <button
        onClick={() => setShowSessions(!showSessions)}
        className="flex items-center gap-2 px-3 py-2 bg-white/[0.05] border border-white/10 rounded-lg hover:bg-white/[0.08] transition"
      >
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
        </svg>
        <span className="text-sm">Sessions</span>
        <svg className={`w-4 h-4 transition-transform ${showSessions ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {/* Session management panel */}
      {showSessions && (
        <div className="absolute top-full right-0 mt-2 bg-black/95 border border-white/10 rounded-lg shadow-xl z-50 w-80 max-h-96 overflow-hidden">
          <div className="p-4 border-b border-white/10">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-lg font-semibold">Session Management</h3>
              <button
                onClick={loadSessions}
                disabled={loading}
                className="p-1 text-white/60 hover:text-white/80 transition disabled:opacity-50"
                title="Refresh sessions"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
              </button>
            </div>
            
            {/* Create new session */}
            <div className="flex gap-2 mb-4">
              <input
                type="text"
                value={newSessionTitle}
                onChange={(e) => setNewSessionTitle(e.target.value)}
                placeholder="New session title..."
                className="flex-1 px-3 py-2 bg-white/[0.04] border border-white/10 rounded outline-none focus:ring-2 focus:ring-primary-500 text-sm"
                onKeyPress={(e) => e.key === 'Enter' && createNewSession()}
              />
              <button
                onClick={createNewSession}
                disabled={!newSessionTitle.trim()}
                className="px-4 py-2 bg-primary-500 text-black font-medium rounded disabled:opacity-50 disabled:cursor-not-allowed hover:bg-primary-400 transition text-sm"
              >
                Create
              </button>
            </div>
          </div>

          {/* Session list */}
          <div className="overflow-y-auto max-h-64">
            {loading ? (
              <div className="p-4 text-center text-white/50">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary-500 mx-auto mb-2"></div>
                Loading...
              </div>
            ) : sessions.length === 0 ? (
              <div className="p-4 text-center text-white/50">
                No sessions found
              </div>
            ) : (
              <div className="space-y-1 p-2">
                {sessions.map((session) => (
                  <div
                    key={session.session_id}
                    className={`flex items-center justify-between p-3 rounded-lg cursor-pointer transition ${
                      currentSessionId === session.session_id
                        ? 'bg-primary-500/20 border border-primary-500/30'
                        : 'bg-white/[0.02] border border-white/5 hover:bg-white/[0.05]'
                    }`}
                  >
                    <div
                      className="flex-1 min-w-0"
                      onClick={() => switchSession(session.session_id)}
                    >
                      <div className="font-medium text-sm truncate">
                        {session.title || 'Untitled Session'}
                      </div>
                      <div className="text-xs text-white/50 mt-1">
                        {formatDate(session.updated_at)}
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-2 ml-2">
                      <button
                        onClick={() => switchSession(session.session_id)}
                        className="p-1 text-white/60 hover:text-white/80 transition"
                        title="Switch to this session"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
                        </svg>
                      </button>
                      
                      <button
                        onClick={() => deleteSession(session.session_id)}
                        className="p-1 text-red-400 hover:text-red-300 transition"
                        title="Delete session"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

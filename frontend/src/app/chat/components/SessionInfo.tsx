"use client";
import { useState, useEffect } from 'react'

interface SessionInfoProps {
  sessionId: string
  onTitleChange: (title: string) => void
}

export default function SessionInfo({ sessionId, onTitleChange }: SessionInfoProps) {
  const [title, setTitle] = useState('New Chat')
  const [isEditing, setIsEditing] = useState(false)
  const [editValue, setEditValue] = useState('')

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'

  // Load session information
  const loadSessionInfo = async () => {
    try {
      const response = await fetch(`${apiUrl}/api/v1/chat/sessions?user_id=1&agent_type=mental_health`)
      if (response.ok) {
        const data = await response.json()
        const sessions = data.sessions || (Array.isArray(data) ? data : [])
        const session = sessions.find((s: any) => s.session_id === sessionId)
        if (session) {
                     setTitle(session.title || 'Untitled Session')
           setEditValue(session.title || 'Untitled Session')
        }
      }
    } catch (error) {
      console.error('Failed to load session information:', error)
    }
  }

  // Save session title
  const saveTitle = async () => {
    if (!editValue.trim()) return

    try {
      // Here you can add API call to update session title
      setTitle(editValue)
      onTitleChange(editValue)
      setIsEditing(false)
    } catch (error) {
      console.error('Failed to save title:', error)
    }
  }

  useEffect(() => {
    if (sessionId) {
      loadSessionInfo()
    }
  }, [sessionId])

  if (isEditing) {
    return (
      <div className="flex items-center gap-2">
        <input
          type="text"
          value={editValue}
          onChange={(e) => setEditValue(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && saveTitle()}
          onBlur={saveTitle}
          className="px-2 py-1 bg-white/[0.04] border border-white/10 rounded text-sm outline-none focus:ring-2 focus:ring-primary-500"
          autoFocus
        />
        <button
          onClick={saveTitle}
          className="p-1 text-primary-400 hover:text-primary-300 transition"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        </button>
      </div>
    )
  }

  return (
    <div className="flex items-center gap-2">
      <span className="text-sm text-white/80">{title}</span>
      <button
        onClick={() => setIsEditing(true)}
        className="p-1 text-white/40 hover:text-white/60 transition"
      >
        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
        </svg>
      </button>
    </div>
  )
}

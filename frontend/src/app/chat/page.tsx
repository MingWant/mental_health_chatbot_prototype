"use client";
import { useState, useRef, useEffect } from 'react'
import { getAuth } from '@/lib/auth'
import Link from 'next/link'
import SessionManager, { Session } from './components/SessionManager'
import SessionInfo from './components/SessionInfo'

type Message = {
  id: number
  role: 'user' | 'assistant'
  content: string
  timestamp: string
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [sessionId, setSessionId] = useState(`session_${Date.now()}`)
  const [currentSessionTitle, setCurrentSessionTitle] = useState('New Chat')
  const [isInitialized, setIsInitialized] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const [useStreaming, setUseStreaming] = useState(true)
  const [refreshKey, setRefreshKey] = useState(0)
  const [isLoadingHistory, setIsLoadingHistory] = useState(false)

  const createSessionIfNeededWithoutHistory = async (): Promise<string> => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';
      const auth = getAuth()
      
      // Check existing session list
      const sessionsResponse = await fetch(`${apiUrl}/api/v1/chat/sessions?user_id=${auth?.user_id || 1}&agent_type=mental_health`);
      if (sessionsResponse.ok) {
        const sessionsData = await sessionsResponse.json();
        const sessions = sessionsData.sessions || (Array.isArray(sessionsData) ? sessionsData : []);
        
        if (sessions.length > 0) {
          // Ensure sessions are sorted by time in descending order (backend already sorted, but frontend confirms)
          const sortedSessions = sessions.sort((a: any, b: any) => {
            const timeA = new Date(a.updated_at || a.created_at || '').getTime()
            const timeB = new Date(b.updated_at || b.created_at || '').getTime()
            return timeB - timeA // Descending order, newest first
          })
          
          // Use the latest session (sorted by time in descending order, newest first)
          const latestSession = sortedSessions[0];
          setSessionId(latestSession.session_id);
          setRefreshKey(k => k + 1)
          setCurrentSessionTitle(latestSession.title || 'New Chat');
          
          // Don't trigger history loading to avoid overwriting user messages
          return latestSession.session_id;
        }
      }
      
      // If no existing sessions, create a new one
      const response = await fetch(`${apiUrl}/api/v1/chat/sessions?agent_type=mental_health&user_id=${auth?.user_id || 1}&title=${encodeURIComponent(currentSessionTitle)}`, {
        method: 'POST'
      });
      
      if (response.ok) {
        const sessionData = await response.json();
        if (sessionData.session_id) {
          setSessionId(sessionData.session_id);
          setRefreshKey(k => k + 1)
          return sessionData.session_id;
        }
      }
    } catch (error) {
      console.error('Failed to create session:', error);
    }
    // If failed, fallback to current sessionId
    return sessionId;
  };

  const createSessionIfNeeded = async (): Promise<string> => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';
      const auth = getAuth()
      
      // Check existing session list
      const sessionsResponse = await fetch(`${apiUrl}/api/v1/chat/sessions?user_id=${auth?.user_id || 1}&agent_type=mental_health`);
      if (sessionsResponse.ok) {
        const sessionsData = await sessionsResponse.json();
        const sessions = sessionsData.sessions || (Array.isArray(sessionsData) ? sessionsData : []);
        
        if (sessions.length > 0) {
          // Ensure sessions are sorted by time in descending order (backend already sorted, but frontend confirms)
          const sortedSessions = sessions.sort((a: any, b: any) => {
            const timeA = new Date(a.updated_at || a.created_at || '').getTime()
            const timeB = new Date(b.updated_at || b.created_at || '').getTime()
            return timeB - timeA // Descending order, newest first
          })
          
          // Use the latest session (sorted by time in descending order, newest first)
          const latestSession = sortedSessions[0];
          setSessionId(latestSession.session_id);
          setRefreshKey(k => k + 1)
          setCurrentSessionTitle(latestSession.title || 'New Chat');
          
          // Automatically load recent session history
          await loadChatHistory(latestSession.session_id);
          return latestSession.session_id;
        }
      }
      
      // If no existing sessions, create a new one
      const response = await fetch(`${apiUrl}/api/v1/chat/sessions?agent_type=mental_health&user_id=${auth?.user_id || 1}&title=${encodeURIComponent(currentSessionTitle)}`, {
        method: 'POST'
      });
      
      if (response.ok) {
        const sessionData = await response.json();
        if (sessionData.session_id) {
          setSessionId(sessionData.session_id);
          setRefreshKey(k => k + 1)
          return sessionData.session_id;
        }
      }
    } catch (error) {
      console.error('Failed to create session:', error);
    }
    // If failed, fallback to current sessionId
    return sessionId;
  };

  // Load chat history
  const loadChatHistory = async (sessionId: string) => {
    setIsLoadingHistory(true)
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';
      const auth = getAuth()
      const response = await fetch(`${apiUrl}/api/v1/chat/sessions/${sessionId}/messages?user_id=${auth?.user_id || 1}&agent_type=mental_health`);
      
      if (response.ok) {
        const data = await response.json();
        const messages = data.messages || (Array.isArray(data) ? data : [])
        const historyMessages: Message[] = messages.map((msg: any) => ({
          id: msg.id,
          role: msg.role as 'user' | 'assistant',
          content: msg.content,
          timestamp: msg.created_at
        }));
        
        // Only set history messages when there are no current messages to avoid overwriting user's new messages
        setMessages(prev => {
          // If no current messages, directly set history messages
          if (prev.length === 0) {
            return historyMessages;
          }
          // If there are current messages, keep them, don't overwrite
          return prev;
        });
      }
    } catch (error) {
      console.error('Failed to load history:', error);
    } finally {
      setIsLoadingHistory(false)
    }
  };

  // Handle session switching
  const handleSessionChange = (newSessionId: string) => {
    setSessionId(newSessionId);
    setMessages([]); // Clear current messages
    setRefreshKey(k => k + 1)
  };

  // Handle session deletion
  const handleSessionDelete = (deletedSessionId: string) => {
    if (deletedSessionId === sessionId) {
      // If the deleted session is the current one, reset to temporary sessionId
      const newSessionId = `session_${Date.now()}`;
      setSessionId(newSessionId);
      setCurrentSessionTitle('New Chat');
      setMessages([]);
    }
  };

  // Handle history loading
  const handleLoadHistory = (sessionId: string) => {
    loadChatHistory(sessionId);
  };

  // Initialize function: automatically load the most recent session when page loads
  const initializeSession = async () => {
    if (isInitialized) return;
    
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';
      const auth = getAuth()
      
      // Get session list
      const sessionsResponse = await fetch(`${apiUrl}/api/v1/chat/sessions?user_id=${auth?.user_id || 1}&agent_type=mental_health`);
      if (sessionsResponse.ok) {
        const sessionsData = await sessionsResponse.json();
        const sessions = sessionsData.sessions || (Array.isArray(sessionsData) ? sessionsData : []);
        
        console.log('Retrieved session list:', sessions);
        
        if (sessions.length > 0) {
          // Ensure sessions are sorted by time in descending order (backend already sorted, but frontend confirms)
          const sortedSessions = sessions.sort((a: any, b: any) => {
            const timeA = new Date(a.updated_at || a.created_at || '').getTime()
            const timeB = new Date(b.updated_at || b.created_at || '').getTime()
            return timeB - timeA // Descending order, newest first
          })
          
          console.log('Sorted session list:', sortedSessions);
          
          // Use the latest session (sorted by time in descending order, newest first)
          const latestSession = sortedSessions[0];
          console.log('Selected latest session:', latestSession);
          
          setSessionId(latestSession.session_id);
          setRefreshKey(k => k + 1)
          setCurrentSessionTitle(latestSession.title || 'New Chat');
          
          // Automatically load recent session history
          await loadChatHistory(latestSession.session_id);
        }
      }
      
      setIsInitialized(true);
    } catch (error) {
      console.error('Failed to initialize session:', error);
      setIsInitialized(true);
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  // Initialize session when page loads
  useEffect(() => {
    initializeSession();
  }, []);

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  useEffect(() => {
    const auth = getAuth()
    if (!auth) {
      window.location.href = '/auth'
      return
    }
  }, [])

  const sendMessage = async () => {
    if (!input.trim() || loading) return

    const userMessage: Message = {
      id: Date.now() + Math.random(), // Use more unique ID
      role: 'user',
      content: input,
      timestamp: new Date().toISOString()
    }

    // Immediately add user message to state
    setMessages(prev => [...prev, userMessage])
    setInput('')
    setLoading(true)

    // Ensure user message has been added to state before sending
    await new Promise(resolve => setTimeout(resolve, 0))

    if (useStreaming) {
      await sendStreamingMessage(userMessage.content)
    } else {
      await sendNonStreamingMessage(userMessage.content)
    }
  }

  const sendStreamingMessage = async (content: string) => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';
      
      // First create or get valid session ID, but don't trigger history loading
      const sid = await createSessionIfNeededWithoutHistory();
      
      const response = await fetch(`${apiUrl}/api/v1/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: sid,
          message: content,
          agent_type: "mental_health"
        })
      })

      if (!response.ok) {
        throw new Error('Network response was not ok')
      }

      const reader = response.body?.getReader()
      if (!reader) {
        throw new Error('No reader available')
      }

      const decoder = new TextDecoder()
      const assistantMessageId = Date.now() + Math.random() + 1
      const assistantMessage: Message = {
        id: assistantMessageId,
        role: 'assistant',
        content: '',
        timestamp: new Date().toISOString()
      }

      setMessages(prev => [...prev, assistantMessage])

      try {
        while (true) {
          const { done, value } = await reader.read()
          if (done) break

          const chunk = decoder.decode(value)
          const lines = chunk.split('\n')

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const data = JSON.parse(line.slice(6))
                if (data.type === 'content') {
                  setMessages(prev => 
                    prev.map(msg => 
                      msg.id === assistantMessageId
                        ? { ...msg, content: data.content }
                        : msg
                    )
                  )
                } else if (data.type === 'done') {
                  break
                }
              } catch (e) {
                // Ignore parsing errors for incomplete JSON
              }
            }
          }
        }
      } finally {
        reader.releaseLock()
      }
    } catch (error) {
      console.error('Streaming error:', error)
      const errorMessage: Message = {
        id: Date.now() + Math.random() + 1,
        role: 'assistant',
        content: 'Sorry, there was an error processing your message. Please try again.',
        timestamp: new Date().toISOString()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setLoading(false)
    }
  }

  const sendNonStreamingMessage = async (content: string) => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';
      
      // First create or get valid session ID, but don't trigger history loading
      const sid = await createSessionIfNeededWithoutHistory();
      
      const response = await fetch(`${apiUrl}/api/v1/chat/messages`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: sid,
          message: content,
          agent_type: "mental_health"
        })
      })

      if (!response.ok) {
        throw new Error('Network response was not ok')
      }

      const data = await response.json()
      
      const assistantMessage: Message = {
        id: Date.now() + Math.random() + 1,
        role: 'assistant',
        content: data.ai_message.content,
        timestamp: data.ai_message.created_at
      }

      setMessages(prev => [...prev, assistantMessage])
    } catch (error) {
      console.error('Non-streaming error:', error)
      const errorMessage: Message = {
        id: Date.now() + Math.random() + 1,
        role: 'assistant',
        content: 'Sorry, there was an error processing your message. Please try again.',
        timestamp: new Date().toISOString()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  return (
    <div className="flex flex-col h-screen bg-black">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-white/10">
        <div className="flex items-center gap-4">
          <div className="text-xl font-semibold">Mental Health ChatBot</div>
          <div className="text-sm text-white/60">|</div>
          <SessionInfo
            sessionId={sessionId}
            onTitleChange={setCurrentSessionTitle}
          />
        </div>
        <div className="flex items-center gap-4">
          <Link href="/" className="px-3 py-2 bg-white/[0.05] border border-white/10 rounded hover:bg-white/[0.08] text-sm">
            Home
          </Link>
          <SessionManager
            currentSessionId={sessionId}
            onSessionChange={handleSessionChange}
            onSessionDelete={handleSessionDelete}
            onLoadHistory={handleLoadHistory}
            refreshKey={refreshKey}
          />
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={useStreaming}
              onChange={(e) => setUseStreaming(e.target.checked)}
              className="rounded"
            />
            Streaming
          </label>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {isLoadingHistory && messages.length === 0 && (
          <div className="text-center text-white/50 py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500 mx-auto mb-2"></div>
            <div className="text-sm">Loading chat history...</div>
          </div>
        )}
        
        {messages.length === 0 && !isLoadingHistory && (
          <div className="text-center text-white/50 py-8">
            <div className="text-lg font-medium mb-2">Welcome to Mental Health ChatBot</div>
            <div className="text-sm">
              I'm here to help you with self-care strategies and emotional well-being.
              <br />
              Share how you're feeling or ask for support.
            </div>
          </div>
        )}
        
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex items-end gap-3 ${message.role === 'user' ? 'justify-end' : 'justify-start'} animate-fade-in`}
          >
            {message.role === 'assistant' && (
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-blue-400 to-purple-500 flex items-center justify-center shadow-lg transition-transform duration-200 hover:scale-110">
                <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-2 0c0 .993-.241 1.929-.668 2.754l-1.524-1.525a3.997 3.997 0 00.078-2.183l1.562-1.562C15.802 8.249 16 9.1 16 10zm-5.165 3.913l1.58 1.58A5.98 5.98 0 0110 16a5.976 5.976 0 01-2.516-.552l1.562-1.562a4.006 4.006 0 001.789.027zm-4.677-2.796a4.002 4.002 0 01-.041-2.08l-.08-.08-1.53-1.53C3.338 6.36 3 7.14 3 8a5 5 0 005 5c.86 0 1.64-.338 2.22-.887l1.53 1.53a4.002 4.002 0 002.08.041l.08.08-1.562 1.562a3.997 3.997 0 01-1.789-.027z" clipRule="evenodd" />
                </svg>
              </div>
            )}
            
            <div
              className={`max-w-[70%] p-4 rounded-2xl transition-all duration-200 hover:scale-[1.02] ${
                message.role === 'user'
                  ? 'bg-gradient-to-r from-primary-500 to-primary-600 text-black shadow-lg hover:shadow-glow'
                  : 'bg-white/[0.08] border border-white/20 shadow-lg backdrop-blur-sm hover:bg-white/[0.12]'
              }`}
            >
              <div className="whitespace-pre-wrap leading-relaxed">
                {message.content}
              </div>
              <div className={`text-xs mt-2 ${
                message.role === 'user' ? 'text-black/60' : 'text-white/40'
              }`}>
                {new Date(message.timestamp).toLocaleTimeString()}
              </div>
            </div>
            
            {message.role === 'user' && (
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-green-400 to-blue-500 flex items-center justify-center shadow-lg transition-transform duration-200 hover:scale-110">
                <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clipRule="evenodd" />
                </svg>
              </div>
            )}
          </div>
        ))}
        
        {loading && (
          <div className="flex items-end gap-3 justify-start">
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-blue-400 to-purple-500 flex items-center justify-center">
              <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-2 0c0 .993-.241 1.929-.668 2.754l-1.524-1.525a3.997 3.997 0 00.078-2.183l1.562-1.562C15.802 8.249 16 9.1 16 10zm-5.165 3.913l1.58 1.58A5.98 5.98 0 0110 16a5.976 5.976 0 01-2.516-.552l1.562-1.562a4.006 4.006 0 001.789.027zm-4.677-2.796a4.002 4.002 0 01-.041-2.08l-.08-.08-1.53-1.53C3.338 6.36 3 7.14 3 8a5 5 0 005 5c.86 0 1.64-.338 2.22-.887l1.53 1.53a4.002 4.002 0 002.08.041l.08.08-1.562 1.562a3.997 3.997 0 01-1.789-.027z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="bg-white/[0.08] border border-white/20 p-4 rounded-2xl shadow-lg backdrop-blur-sm">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="p-4 border-t border-white/10">
        <div className="flex gap-2 items-end">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Share how you're feeling or ask for self-care tips..."
            className="flex-1 p-4 bg-white/[0.04] border border-white/10 rounded-lg resize-none outline-none focus:ring-2 focus:ring-primary-500 text-base min-h-[64px] max-h-[200px]"
            rows={3}
            disabled={loading || isLoadingHistory}
          />
          <button
            onClick={sendMessage}
            disabled={loading || !input.trim() || isLoadingHistory}
            className="px-6 py-3 bg-primary-500 text-black font-medium rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-primary-400 transition h-[52px]"
          >
            Send
          </button>
        </div>
        
        <div className="text-xs text-white/50 mt-2">
          Press Enter to send, Shift+Enter for new line
        </div>
      </div>
    </div>
  )
}

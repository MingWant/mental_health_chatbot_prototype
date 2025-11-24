"use client";
import { useState, useRef, useEffect } from 'react'
import { getAuth } from '@/lib/auth'
import Link from 'next/link'

type Document = {
  id: string
  name: string
  type: string
  size?: string
  uploaded_at?: string
  status?: 'processing' | 'ready' | 'error'
  categories?: string[]
  chunking_strategy?: string
  chunk_count?: number
}

type DocChunk = {
  chunk_id: number
  text: string
  length: number
  word_count: number
  created_at: string
  mode?: 'chars' | 'words' | 'sentences' | 'paragraphs'
  chunk_size?: number
  overlap?: number
  chunk_type?: string
  strategy?: string
}

type ChunkingStrategy = {
  value: string
  label: string
  description: string
  recommended: boolean
  icon: string
}

export default function RAGManagementPage() {
  const [documents, setDocuments] = useState<Document[]>([])
  const [uploading, setUploading] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState<any[]>([])
  const [searching, setSearching] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [previewingDocId, setPreviewingDocId] = useState<string | null>(null)
  const [previewChunks, setPreviewChunks] = useState<DocChunk[] | null>(null)
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';
  const [chunkSize, setChunkSize] = useState<number>(200)
  const [overlap, setOverlap] = useState<number>(30)
  const [mode, setMode] = useState<'chars' | 'words' | 'sentences' | 'paragraphs'>('sentences')
  const [customKeywords, setCustomKeywords] = useState<string>('')
  const [chunkingStrategy, setChunkingStrategy] = useState<string>('semantic')
  const [showAdvancedSettings, setShowAdvancedSettings] = useState(false)
  const [testText, setTestText] = useState<string>('')
  const [testResults, setTestResults] = useState<any>(null)
  const [testingChunking, setTestingChunking] = useState(false)

  // Chunking strategies (UI labels)
  const chunkingStrategies: ChunkingStrategy[] = [
    {
      value: 'fixed_length',
      label: 'Fixed-length chunking',
      description: 'Split by fixed number of characters or words; simple and fast',
      recommended: false,
      icon: '📏'
    },
    {
      value: 'semantic',
      label: 'Semantic chunking',
      description: 'Split by paragraph/sentence boundaries to preserve meaning',
      recommended: true,
      icon: '🧠'
    },
    {
      value: 'session',
      label: 'Session chunking',
      description: 'Split by conversation/meeting transcript turns',
      recommended: false,
      icon: '💬'
    },
    {
      value: 'hierarchical',
      label: 'Hierarchical chunking',
      description: 'Split by headings/chapters/sections',
      recommended: true,
      icon: '📚'
    },
    {
      value: 'adaptive',
      label: 'Adaptive chunking',
      description: 'Automatically select the best strategy based on text',
      recommended: true,
      icon: '🤖'
    }
  ]

  // Recommended defaults per strategy
  const strategyDefaults: Record<string, { size: number; overlap: number; mode: 'chars' | 'words' | 'sentences' | 'paragraphs' }> = {
    fixed_length: { size: 200, overlap: 30, mode: 'chars' },
    semantic: { size: 520, overlap: 60, mode: 'sentences' },
    hierarchical: { size: 600, overlap: 80, mode: 'sentences' },
    session: { size: 520, overlap: 60, mode: 'sentences' },
    adaptive: { size: 520, overlap: 60, mode: 'sentences' },
  }

  // Apply defaults when strategy changes
  useEffect(() => {
    const d = strategyDefaults[chunkingStrategy]
    if (d) {
      setChunkSize(d.size)
      setOverlap(d.overlap)
      setMode(d.mode)
    }
  }, [chunkingStrategy])

  const fetchDocuments = async () => {
    try {
      const res = await fetch(`${apiUrl}/api/v1/mental-health-rag/documents`)
      if (res.ok) {
        const data = await res.json()
        const docs = (data.documents || []).map((d: any) => ({
          id: d.doc_id,
          name: d.filename,
          type: d.file_type,
          uploaded_at: d.created_at,
          status: 'ready' as const,
          categories: d.categories || [],
          chunking_strategy: d.chunking_strategy || 'fixed_length',
          chunk_count: d.total_chunks || 0
        })) as Document[]
        setDocuments(docs)
      }
    } catch (e) {
      console.error('Load documents failed:', e)
    }
  }

  useEffect(() => {
    const auth = getAuth()
    if (!auth) {
      window.location.href = '/auth'
      return
    }
    fetchDocuments()
  }, [])

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files
    if (!files || files.length === 0) return

    setUploading(true)
    
    try {
      for (let i = 0; i < files.length; i++) {
        const file = files[i]
        const formData = new FormData()
        formData.append('file', file)
        formData.append('chunking_strategy', chunkingStrategy)
        formData.append('chunk_size', String(chunkSize))
        formData.append('overlap', String(overlap))
        formData.append('mode', mode)
        if (customKeywords.trim()) {
          formData.append('custom_keywords', customKeywords)
        }
        
        const response = await fetch(`${apiUrl}/api/v1/mental-health-rag/upload`, {
          method: 'POST',
          body: formData
        })
        
        if (response.ok) {
          await fetchDocuments()
        }
      }
    } catch (error) {
      console.error('Upload failed:', error)
    } finally {
      setUploading(false)
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    }
  }

  const handleSearch = async () => {
    if (!searchQuery.trim()) return
    
    setSearching(true)
    try {
      const response = await fetch(`${apiUrl}/api/v1/mental-health-rag/search?query=${encodeURIComponent(searchQuery)}`)
      if (response.ok) {
        const data = await response.json()
        setSearchResults(data.results || [])
      }
    } catch (error) {
      console.error('Search failed:', error)
    } finally {
      setSearching(false)
    }
  }

  const openPreview = async (docId: string) => {
    try {
      setPreviewingDocId(docId)
      setPreviewChunks(null)
      const res = await fetch(`${apiUrl}/api/v1/mental-health-rag/documents/${docId}`)
      if (res.ok) {
        const data = await res.json()
        setPreviewChunks(data.chunks || [])
      }
    } catch (e) {
      console.error('Load chunks failed:', e)
    }
  }

  const closePreview = () => {
    setPreviewingDocId(null)
    setPreviewChunks(null)
  }

  const removeDocument = async (id: string) => {
    try {
      if (!confirm('Are you sure you want to remove this document? This cannot be undone.')) return
      const res = await fetch(`${apiUrl}/api/v1/mental-health-rag/documents/${id}`, { method: 'DELETE' })
      if (res.ok) {
        await fetchDocuments()
      } else {
        // fallback: optimistic remove if server didn't confirm
        setDocuments(prev => prev.filter(doc => doc.id !== id))
      }
    } catch (e) {
      console.error('Delete document failed:', e)
      setDocuments(prev => prev.filter(doc => doc.id !== id))
    }
  }

  const testChunkingStrategy = async () => {
    if (!testText.trim()) return
    
    setTestingChunking(true)
    try {
      const response = await fetch(`${apiUrl}/api/test-chunking`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text: testText,
          chunking_strategy: chunkingStrategy,
          chunk_size: chunkSize,
          overlap: overlap,
          mode: mode
        })
      })
      
      if (response.ok) {
        const data = await response.json()
        setTestResults(data)
      } else {
        console.error('Test chunking failed')
      }
    } catch (error) {
      console.error('Test chunking failed:', error)
    } finally {
      setTestingChunking(false)
    }
  }

  const getStrategyIcon = (strategy: string) => {
    const strategyObj = chunkingStrategies.find(s => s.value === strategy)
    return strategyObj?.icon || '📄'
  }

  const getStrategyLabel = (strategy: string) => {
    const strategyObj = chunkingStrategies.find(s => s.value === strategy)
    return strategyObj?.label || strategy
  }

  return (
    <div className="px-6 py-10 max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div className="text-2xl font-semibold">RAG Management</div>
        <Link href="/" className="px-3 py-2 bg-white/[0.05] border border-white/10 rounded hover:bg-white/[0.08] text-sm">Home</Link>
      </div>
      
      <div className="grid md:grid-cols-2 gap-8">
        {/* Document Upload */}
        <div className="space-y-6">
          <div className="text-lg font-semibold">Upload Documents</div>
          
          <div className="p-6 bg-white/[0.02] rounded-lg border border-white/10">
            <div className="text-sm text-white/70 mb-4">
              Upload mental health resources, educational content, and support materials.
              Supported formats: PDF, TXT, DOC, DOCX
            </div>
            
            {/* Chunking strategy selection */}
            <div className="mb-4">
              <div className="mb-2 text-sm font-medium text-white/80">Chunking strategy</div>
              <div className="grid grid-cols-1 gap-2">
                {chunkingStrategies.map((strategy) => (
                  <label key={strategy.value} className="flex items-center p-3 bg-white/[0.02] border border-white/10 rounded cursor-pointer hover:bg-white/[0.04] transition">
                    <input
                      type="radio"
                      name="chunkingStrategy"
                      value={strategy.value}
                      checked={chunkingStrategy === strategy.value}
                      onChange={(e) => setChunkingStrategy(e.target.value)}
                      className="mr-3"
                    />
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="text-lg">{strategy.icon}</span>
                        <span className="font-medium text-sm">{strategy.label}</span>
                        {strategy.recommended && (
                          <span className="px-2 py-1 bg-green-500/20 text-green-300 text-xs rounded">Recommended</span>
                        )}
                      </div>
                      <div className="text-xs text-white/60 mt-1">{strategy.description}</div>
                    </div>
                  </label>
                ))}
              </div>
            </div>

            {/* Advanced settings */}
            <div className="mb-4">
              <button
                onClick={() => setShowAdvancedSettings(!showAdvancedSettings)}
                className="flex items-center gap-2 text-sm text-primary-400 hover:text-primary-300 transition"
              >
                <span>{showAdvancedSettings ? '▼' : '▶'}</span>
                Advanced settings
              </button>
              
              {showAdvancedSettings && (
                <div className="mt-3 grid grid-cols-2 gap-3 text-sm">
                  <div>
                    <div className="mb-1 text-white/70">Chunk size</div>
                    <input 
                      type="number" 
                      value={chunkSize} 
                      onChange={e => setChunkSize(Number(e.target.value) || 0)} 
                      className="w-full px-3 py-2 bg-white/[0.04] border border-white/10 rounded" 
                    />
                  </div>
                  <div>
                    <div className="mb-1 text-white/70">Overlap</div>
                    <input 
                      type="number" 
                      value={overlap} 
                      onChange={e => setOverlap(Number(e.target.value) || 0)} 
                      className="w-full px-3 py-2 bg-white/[0.04] border border-white/10 rounded" 
                    />
                  </div>
                  <div>
                    <div className="mb-1 text-white/70">Mode</div>
                    <select 
                      value={mode} 
                      onChange={e => setMode(e.target.value as any)} 
                      className="w-full px-3 py-2 bg-black/70 text-white border border-white/10 rounded"
                    >
                      <option value="chars">Characters</option>
                      <option value="words">Words</option>
                      <option value="sentences">Sentences</option>
                      <option value="paragraphs">Paragraphs</option>
                    </select>
                  </div>
                  <div>
                    <div className="mb-1 text-white/70">Custom keywords</div>
                    <input 
                      type="text" 
                      value={customKeywords} 
                      onChange={e => setCustomKeywords(e.target.value)} 
                      placeholder="anxiety, stress, meditation" 
                      className="w-full px-3 py-2 bg-white/[0.04] border border-white/10 rounded" 
                    />
                  </div>
                </div>
              )}
            </div>
            
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept=".pdf,.txt,.doc,.docx"
              onChange={handleFileUpload}
              className="hidden"
            />
            
            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={uploading}
              className="w-full px-4 py-3 bg-primary-500 text-black font-medium rounded disabled:opacity-50 hover:bg-primary-400 transition"
            >
              {uploading ? 'Uploading...' : 'Choose Files'}
            </button>
          </div>

          {/* Chunking strategy test */}
          <div className="p-6 bg-white/[0.02] rounded-lg border border-white/10">
            <div className="text-sm font-medium mb-3">Chunking test</div>
            <div className="text-xs text-white/70 mb-3">Enter sample text to preview chunking and choose a strategy</div>
            
            <textarea
              value={testText}
              onChange={(e) => setTestText(e.target.value)}
              placeholder="Enter sample text, e.g. the first chapter of a guide..."
              className="w-full h-24 px-3 py-2 bg-white/[0.04] border border-white/10 rounded text-sm resize-none"
            />
            
            <div className="flex gap-2 mt-3">
              <button
                onClick={testChunkingStrategy}
                disabled={testingChunking || !testText.trim()}
                className="px-4 py-2 bg-blue-500 text-white text-sm rounded disabled:opacity-50 hover:bg-blue-400 transition"
              >
                {testingChunking ? 'Testing...' : 'Test Strategy'}
              </button>
              <button
                onClick={() => {
                  setTestText('')
                  setTestResults(null)
                }}
                className="px-4 py-2 bg-white/[0.1] text-white text-sm rounded hover:bg-white/[0.2] transition"
              >
                Clear
              </button>
            </div>

            {/* Test results */}
            {testResults && (
              <div className="mt-4 p-3 bg-white/[0.02] border border-white/10 rounded">
                <div className="text-sm font-medium mb-2">Test results</div>
                <div className="text-xs text-white/70 mb-2">
                  Strategy: {getStrategyLabel(chunkingStrategy)} • 
                  Chunks: {testResults.chunk_count} • 
                  Avg length: {testResults.statistics?.avg_chunk_length?.toFixed(1)} chars
                </div>
                <div className="space-y-2 max-h-32 overflow-y-auto">
                  {testResults.chunks?.slice(0, 3).map((chunk: any, index: number) => (
                    <div key={index} className="p-2 bg-white/[0.02] border border-white/5 rounded text-xs">
                      <div className="text-white/60 mb-1">
                        Chunk {chunk.id} • {chunk.length} chars • {chunk.chunk_type || 'default'}
                      </div>
                      <div className="text-white/80 line-clamp-2">{chunk.text}</div>
                    </div>
                  ))}
                  {testResults.chunks?.length > 3 && (
                    <div className="text-xs text-white/50 text-center">... {testResults.chunks.length - 3} more chunks</div>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Document List */}
          <div className="space-y-3">
            <div className="text-sm font-medium">Uploaded Documents</div>
            {documents.length === 0 ? (
              <div className="text-white/50 text-sm">No documents uploaded yet</div>
            ) : (
              <div className="space-y-2 max-h-64 overflow-y-auto">
                {documents.map((doc) => (
                  <div key={doc.id} className="p-3 bg-white/[0.02] rounded border border-white/5">
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <div className="font-medium text-sm">{doc.name}</div>
                        <div className="text-xs text-white/60 mt-1">
                          <div className="flex items-center gap-2 mb-1">
                            <span>{getStrategyIcon(doc.chunking_strategy || 'fixed_length')}</span>
                            <span>{getStrategyLabel(doc.chunking_strategy || 'fixed_length')}</span>
                            {doc.chunk_count && (
                              <span className="px-1 py-0.5 bg-blue-500/20 text-blue-300 rounded text-xs">
                                {doc.chunk_count} chunks
                              </span>
                            )}
                          </div>
                          <div>
                            {doc.categories && doc.categories.length > 0 ? doc.categories.join(', ') : 'uncategorized'}
                            {doc.uploaded_at ? ` • ${new Date(doc.uploaded_at).toLocaleDateString()}` : ''}
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        {doc.status && (
                          <div className={`px-2 py-1 rounded text-xs ${
                            doc.status === 'ready' ? 'bg-green-500/20 text-green-300' :
                            doc.status === 'processing' ? 'bg-yellow-500/20 text-yellow-300' :
                            'bg-red-500/20 text-red-300'
                          }`}>
                            {doc.status}
                          </div>
                        )}
                        <button
                          onClick={() => openPreview(doc.id)}
                          className="text-primary-400 hover:text-primary-300 text-xs"
                        >
                          Preview
                        </button>
                        <button
                          onClick={() => removeDocument(doc.id)}
                          className="text-red-400 hover:text-red-300 text-xs"
                        >
                          Remove
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Document Search */}
        <div className="space-y-6">
          <div className="text-lg font-semibold">Search Documents</div>
          
          <div className="p-6 bg-white/[0.02] rounded-lg border border-white/10">
            <div className="text-sm text-white/70 mb-4">
              Search through uploaded mental health resources and educational content.
            </div>
            
            <div className="flex gap-2">
              <input
                type="text"
                placeholder="Search for mental health topics..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                className="flex-1 px-3 py-2 bg-white/[0.04] border border-white/10 rounded outline-none focus:ring-2 focus:ring-primary-500"
              />
              <button
                onClick={handleSearch}
                disabled={searching || !searchQuery.trim()}
                className="px-4 py-2 bg-primary-500 text-black font-medium rounded disabled:opacity-50 hover:bg-primary-400 transition"
              >
                {searching ? 'Searching...' : 'Search'}
              </button>
            </div>
          </div>

          {/* Search Results */}
          <div className="space-y-3">
            <div className="text-sm font-medium">Search Results</div>
            {searchResults.length === 0 ? (
              <div className="text-white/50 text-sm">
                {searchQuery ? 'No results found' : 'Enter a search query to find documents'}
              </div>
            ) : (
              <div className="space-y-2 max-h-64 overflow-y-auto">
                {searchResults.map((result, index) => (
                  <div key={index} className="p-3 bg-white/[0.02] rounded border border-white/5">
                    <div className="font-medium text-sm mb-1">{result.title || 'Untitled'}</div>
                    <div className="text-xs text-white/70 mb-2">{result.source || 'Unknown source'}</div>
                    <div className="text-xs text-white/60 line-clamp-3">
                      {result.content || result.text || 'No content available'}
                    </div>
                    {result.similarity && (
                      <div className="text-xs text-primary-400 mt-1">
                        Relevance: {(result.similarity * 100).toFixed(1)}%
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* RAG Health Status */}
      <div className="mt-8 p-6 bg-white/[0.02] rounded-lg border border-white/10">
        <div className="text-lg font-semibold mb-4">System Status</div>
        <div className="grid md:grid-cols-3 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-green-400">{documents.length}</div>
            <div className="text-sm text-white/70">Documents Uploaded</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-400">
              {documents.filter(d => d.status === 'ready').length}
            </div>
            <div className="text-sm text-white/70">Ready for Search</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-purple-400">{searchResults.length}</div>
            <div className="text-sm text-white/70">Search Results</div>
          </div>
        </div>
      </div>

      {previewingDocId && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50">
          <div className="w-[90vw] max-w-4xl max-h-[80vh] bg-black/95 border border-white/10 rounded-lg overflow-hidden">
            <div className="flex items-center justify-between p-4 border-b border-white/10">
              <div className="font-semibold">Chunks Preview - {previewingDocId}</div>
              <button onClick={closePreview} className="text-white/60 hover:text-white">✕</button>
            </div>
            <div className="p-4 overflow-y-auto" style={{maxHeight: '70vh'}}>
              {!previewChunks && (
                <div className="text-white/50 text-sm">Loading chunks...</div>
              )}
              {previewChunks && previewChunks.length === 0 && (
                <div className="text-white/50 text-sm">No chunks found</div>
              )}
              {previewChunks && previewChunks.length > 0 && (
                <div className="space-y-3">
                  {previewChunks.map((chunk) => (
                    <div key={chunk.chunk_id} className="p-3 bg-white/[0.02] rounded border border-white/5">
                      <div className="flex items-center justify-between mb-2">
                        <div className="text-xs text-white/60">
                          Chunk #{chunk.chunk_id} • {chunk.mode === 'words' ? `${chunk.word_count} tokens` : `${chunk.length} chars`} 
                          {chunk.chunk_type && ` • ${chunk.chunk_type}`}
                          {chunk.strategy && ` • ${chunk.strategy}`}
                        </div>
                        <div className="text-xs text-white/40">{new Date(chunk.created_at).toLocaleString()}</div>
                      </div>
                      <div className="text-sm whitespace-pre-wrap leading-6">{chunk.text}</div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

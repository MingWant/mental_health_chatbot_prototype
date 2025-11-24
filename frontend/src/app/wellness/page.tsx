"use client";
import { useState } from 'react'

type ToolResult = {
  success: boolean
  data?: any
  error?: string
}

export default function WellnessPage() {
  const [selectedTool, setSelectedTool] = useState<string>('')
  const [input, setInput] = useState('')
  const [result, setResult] = useState<ToolResult | null>(null)
  const [loading, setLoading] = useState(false)

  const tools = [
    {
      id: 'emotion_assessment',
      name: 'Emotion Assessment',
      description: 'Analyze your emotional state and provide recommendations',
      placeholder: 'Describe how you feel today...',
      endpoint: '/api/v1/mental-health/assess'
    },
    {
      id: 'coping_strategies',
      name: 'Coping Strategies',
      description: 'Get coping methods for specific emotions',
      placeholder: 'Choose emotion type (anxiety, depression, anger, stress, loneliness)',
      endpoint: '/api/v1/mental-health/coping-strategies'
    },
    {
      id: 'meditation',
      name: 'Meditation Guide',
      description: 'Provide meditation practice guidance for different levels',
      placeholder: 'Choose level (beginner/advanced) and type (breathing meditation/body scan)',
      endpoint: '/api/v1/mental-health/meditation'
    },
    {
      id: 'sleep_advice',
      name: 'Sleep Advice',
      description: 'Professional advice to improve sleep quality',
      placeholder: 'Click to get sleep advice',
      endpoint: '/api/v1/mental-health/sleep-advice'
    },
    {
      id: 'study_wellness',
      name: 'Study Wellness',
      description: 'Mental health advice during the learning process',
      placeholder: 'Click to get study wellness advice',
      endpoint: '/api/v1/mental-health/study-wellness'
    },
    {
      id: 'self_care_plan',
      name: 'Self-Care Plan',
      description: 'Create personalized self-care plans',
      placeholder: 'Describe your preferences (meditation, exercise, journaling, etc.)',
      endpoint: '/api/v1/mental-health/self-care-plan'
    },
    {
      id: 'resources',
      name: 'Mental Health Resources',
      description: 'Get professional resources and emergency contact information',
      placeholder: 'Click to get mental health resources',
      endpoint: '/api/v1/mental-health/resources'
    },
    {
      id: 'mood_tracker',
      name: 'Mood Tracker',
      description: 'Generate mood tracking templates',
      placeholder: 'Click to generate mood tracker',
      endpoint: '/api/v1/mental-health/mood-tracker'
    }
  ]

  const handleToolSelect = (toolId: string) => {
    setSelectedTool(toolId)
    setInput('')
    setResult(null)
  }

  const handleSubmit = async () => {
    if (!selectedTool) return

    setLoading(true)
    setResult(null)

    try {
      const tool = tools.find(t => t.id === selectedTool)
      if (!tool) throw new Error('Tool does not exist')

      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';
      let url = `${apiUrl}${tool.endpoint}`
      let body: any = {}

      // Build request based on tool type
      switch (selectedTool) {
        case 'emotion_assessment':
          body = { message: input }
          break
        case 'coping_strategies':
          const [emotion, intensity] = input.split(',').map(s => s.trim())
          url += `?emotion=${encodeURIComponent(emotion)}&intensity=${encodeURIComponent(intensity || 'medium')}`
          break
        case 'meditation':
          const [level, type] = input.split(',').map(s => s.trim())
          url += `?level=${encodeURIComponent(level || 'beginner')}&type=${encodeURIComponent(type || 'breathing meditation')}`
          break
        case 'self_care_plan':
          body = { preferences: { meditation: input.includes('meditation'), exercise: input.includes('exercise'), journaling: input.includes('journaling') } }
          break
        default:
          // Other tools don't need additional parameters
          break
      }

      const response = await fetch(url, {
        method: selectedTool === 'sleep_advice' || selectedTool === 'study_wellness' || selectedTool === 'resources' || selectedTool === 'mood_tracker' ? 'GET' : 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: Object.keys(body).length > 0 ? JSON.stringify(body) : undefined
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      setResult({ success: true, data })
    } catch (error) {
      console.error('Error:', error)
      setResult({ success: false, error: error instanceof Error ? error.message : 'Unknown error' })
    } finally {
      setLoading(false)
    }
  }

  const renderResult = () => {
    if (!result) return null

    if (!result.success) {
      return (
        <div className="bg-red-500/10 border border-red-500/20 p-4 rounded-lg">
          <div className="text-red-400 font-medium">Error</div>
          <div className="text-red-300 text-sm mt-1">{result.error}</div>
        </div>
      )
    }

    return (
      <div className="bg-white/[0.02] border border-white/10 p-4 rounded-lg">
        <div className="text-primary-400 font-medium mb-2">Result</div>
        <div className="text-sm text-white/80 whitespace-pre-wrap">
          {JSON.stringify(result.data, null, 2)}
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-screen bg-black">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-white/10">
        <div className="text-xl font-semibold">Mental Health Tools</div>
        <div className="text-sm text-white/60">
          Professional mental health self-care toolset
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4">
        <div className="max-w-4xl mx-auto">
          {/* Tool Selection */}
          <div className="mb-6">
            <h2 className="text-lg font-semibold mb-4">Select Tool</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {tools.map((tool) => (
                <button
                  key={tool.id}
                  onClick={() => handleToolSelect(tool.id)}
                  className={`p-4 rounded-lg border transition ${
                    selectedTool === tool.id
                      ? 'border-primary-500 bg-primary-500/10'
                      : 'border-white/10 bg-white/[0.02] hover:bg-white/[0.05]'
                  }`}
                >
                  <div className="text-left">
                    <div className="font-medium mb-1">{tool.name}</div>
                    <div className="text-sm text-white/60">{tool.description}</div>
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Tool Usage */}
          {selectedTool && (
            <div className="mb-6">
              <h2 className="text-lg font-semibold mb-4">Use Tool</h2>
              <div className="bg-white/[0.02] border border-white/10 p-4 rounded-lg">
                <div className="mb-4">
                  <div className="font-medium mb-2">
                    {tools.find(t => t.id === selectedTool)?.name}
                  </div>
                  <div className="text-sm text-white/60 mb-3">
                    {tools.find(t => t.id === selectedTool)?.description}
                  </div>
                </div>

                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium mb-2">
                      Input Parameters
                    </label>
                    <textarea
                      value={input}
                      onChange={(e) => setInput(e.target.value)}
                      placeholder={tools.find(t => t.id === selectedTool)?.placeholder}
                      className="w-full p-3 bg-white/[0.04] border border-white/10 rounded-lg resize-none outline-none focus:ring-2 focus:ring-primary-500"
                      rows={3}
                      disabled={loading}
                    />
                  </div>

                  <button
                    onClick={handleSubmit}
                    disabled={loading}
                    className="px-6 py-2 bg-primary-500 text-black font-medium rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-primary-400 transition"
                  >
                    {loading ? 'Processing...' : 'Execute'}
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Result Display */}
          {result && (
            <div className="mb-6">
              <h2 className="text-lg font-semibold mb-4">Result</h2>
              {renderResult()}
            </div>
          )}

          {/* Usage Instructions */}
          <div className="bg-white/[0.02] border border-white/10 p-4 rounded-lg">
            <h3 className="font-medium mb-2">Usage Instructions</h3>
            <div className="text-sm text-white/60 space-y-2">
              <div>• <strong>Emotion Assessment</strong>: Describe your mood, system will analyze emotional state</div>
              <div>• <strong>Coping Strategies</strong>: Enter emotion type, such as "anxiety,high"</div>
              <div>• <strong>Meditation Guide</strong>: Enter level and type, such as "beginner,breathing meditation"</div>
              <div>• <strong>Sleep Advice</strong>: Click execute directly to get advice</div>
              <div>• <strong>Study Wellness</strong>: Click execute directly to get advice</div>
              <div>• <strong>Self-Care Plan</strong>: Describe your preferences, such as "meditation,exercise,journaling"</div>
              <div>• <strong>Mental Health Resources</strong>: Click execute directly to get resources</div>
              <div>• <strong>Mood Tracker</strong>: Click execute directly to generate template</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

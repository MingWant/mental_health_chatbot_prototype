"use client";
import { useEffect, useState } from 'react'

type Tool = {
  name: string
  description: string
  parameters: {
    type: string
    properties: Record<string, any>
    required: string[]
  }
}

type ToolExecutionRequest = {
  tool_name: string
  parameters: Record<string, any>
}

export default function ToolsPage() {
  const [tools, setTools] = useState<Tool[]>([])
  const [selectedTool, setSelectedTool] = useState<Tool | null>(null)
  const [executionResult, setExecutionResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [parameters, setParameters] = useState<Record<string, any>>({})

  useEffect(() => {
    loadTools()
  }, [])

  const loadTools = async () => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';
      const response = await fetch(`${apiUrl}/agent-tools/`)
      if (response.ok) {
        const data = await response.json()
        setTools(data.tools)
      }
    } catch (error) {
      console.error('Failed to load tools:', error)
    }
  }

  const executeTool = async () => {
    if (!selectedTool) return

    setLoading(true)
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';
      const response = await fetch(`${apiUrl}/agent-tools/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          tool_name: selectedTool.name,
          parameters: parameters
        })
      })
      
      if (response.ok) {
        const result = await response.json()
        setExecutionResult(result)
      }
    } catch (error) {
      console.error('Failed to execute tool:', error)
      setExecutionResult({ success: false, error: error instanceof Error ? error.message : 'Unknown error' })
    } finally {
      setLoading(false)
    }
  }

  const handleToolSelect = (tool: Tool) => {
    setSelectedTool(tool)
    setParameters({})
    setExecutionResult(null)
  }

  const updateParameter = (key: string, value: any) => {
    setParameters(prev => ({
      ...prev,
      [key]: value
    }))
  }

  const renderParameterInput = (paramName: string, paramSchema: any) => {
    const isRequired = selectedTool?.parameters.required.includes(paramName)
    
    if (paramSchema.type === 'integer') {
      return (
        <input
          type="number"
          placeholder={paramSchema.description || paramName}
          value={parameters[paramName] || ''}
          onChange={(e) => updateParameter(paramName, parseInt(e.target.value) || 0)}
          className="px-3 py-2 bg-white/[0.04] border border-white/10 rounded outline-none focus:ring-2 focus:ring-primary-500"
          required={isRequired}
        />
      )
    } else if (paramSchema.type === 'string' && paramSchema.enum) {
      return (
        <select
          value={parameters[paramName] || ''}
          onChange={(e) => updateParameter(paramName, e.target.value)}
          className="px-3 py-2 bg-white/[0.04] border border-white/10 rounded outline-none focus:ring-2 focus:ring-primary-500"
          required={isRequired}
        >
          <option value="">Select {paramName}</option>
          {paramSchema.enum.map((option: string) => (
            <option key={option} value={option}>{option}</option>
          ))}
        </select>
      )
    } else if (paramSchema.type === 'string') {
      return (
        <input
          type="text"
          placeholder={paramSchema.description || paramName}
          value={parameters[paramName] || ''}
          onChange={(e) => updateParameter(paramName, e.target.value)}
          className="px-3 py-2 bg-white/[0.04] border border-white/10 rounded outline-none focus:ring-2 focus:ring-primary-500"
          required={isRequired}
        />
      )
    } else if (paramSchema.type === 'number') {
      return (
        <input
          type="number"
          step="0.1"
          placeholder={paramSchema.description || paramName}
          value={parameters[paramName] || ''}
          onChange={(e) => updateParameter(paramName, parseFloat(e.target.value) || 0)}
          className="px-3 py-2 bg-white/[0.04] border border-white/10 rounded outline-none focus:ring-2 focus:ring-primary-500"
          required={isRequired}
        />
      )
    }
    
    return (
      <input
        type="text"
        placeholder={paramSchema.description || paramName}
        value={parameters[paramName] || ''}
        onChange={(e) => updateParameter(paramName, e.target.value)}
        className="px-3 py-2 bg-white/[0.04] border border-white/10 rounded outline-none focus:ring-2 focus:ring-primary-500"
        required={isRequired}
      />
    )
  }

  return (
    <div className="px-6 py-10 max-w-6xl mx-auto">
      <div className="text-2xl font-semibold mb-6">FunctionTool Agent Tools</div>
      
      <div className="grid md:grid-cols-2 gap-8">
        {/* Tools List */}
        <div className="space-y-4">
          <div className="text-lg font-semibold">Available Tools</div>
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {tools.map((tool) => (
              <div
                key={tool.name}
                onClick={() => handleToolSelect(tool)}
                className={`p-4 rounded-lg border cursor-pointer transition ${
                  selectedTool?.name === tool.name
                    ? 'border-primary-500 bg-primary-500/10'
                    : 'border-white/10 bg-white/[0.02] hover:bg-white/[0.05]'
                }`}
              >
                <div className="font-medium text-primary-400">{tool.name}</div>
                <div className="text-sm text-white/70 mt-1">{tool.description}</div>
                <div className="text-xs text-white/50 mt-2">
                  Parameters: {Object.keys(tool.parameters.properties).length}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Tool Execution */}
        <div className="space-y-4">
          <div className="text-lg font-semibold">Tool Execution</div>
          
          {selectedTool ? (
            <div className="space-y-4">
              <div className="p-4 bg-white/[0.02] rounded-lg border border-white/10">
                <div className="font-medium text-primary-400">{selectedTool.name}</div>
                <div className="text-sm text-white/70 mt-1">{selectedTool.description}</div>
              </div>

              {/* Parameters */}
              <div className="space-y-3">
                <div className="text-sm font-medium">Parameters</div>
                {Object.entries(selectedTool.parameters.properties).map(([paramName, paramSchema]) => (
                  <div key={paramName} className="space-y-1">
                    <label className="text-sm text-white/70">
                      {paramName}
                      {selectedTool.parameters.required.includes(paramName) && (
                        <span className="text-red-400 ml-1">*</span>
                      )}
                    </label>
                    {renderParameterInput(paramName, paramSchema)}
                    {paramSchema.description && (
                      <div className="text-xs text-white/50">{paramSchema.description}</div>
                    )}
                  </div>
                ))}
              </div>

              {/* Execute Button */}
              <button
                onClick={executeTool}
                disabled={loading}
                className="w-full px-4 py-2 bg-primary-500 text-black font-medium rounded disabled:opacity-50"
              >
                {loading ? 'Executing...' : 'Execute Tool'}
              </button>

              {/* Results */}
              {executionResult && (
                <div className="p-4 bg-white/[0.02] rounded-lg border border-white/10">
                  <div className="text-sm font-medium mb-2">Execution Result</div>
                  <pre className="text-xs text-white/70 overflow-auto max-h-48">
                    {JSON.stringify(executionResult, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          ) : (
            <div className="p-8 text-center text-white/50">
              Select a tool from the list to execute it
            </div>
          )}
        </div>
      </div>

      {/* Tool Categories */}
      <div className="mt-8">
        <div className="text-lg font-semibold mb-4">Tool Categories</div>
        <div className="grid md:grid-cols-3 gap-4">
          {[
            {
              name: "Mood Tracking",
              tools: tools.filter(t => t.name.includes('mood')),
              color: "blue"
            },
            {
              name: "Self-Care",
              tools: tools.filter(t => t.name.includes('self-care') || t.name.includes('activity')),
              color: "green"
            },
            {
              name: "Analysis",
              tools: tools.filter(t => t.name.includes('analyze') || t.name.includes('detect')),
              color: "purple"
            },
            {
              name: "Resources",
              tools: tools.filter(t => t.name.includes('resource') || t.name.includes('crisis')),
              color: "red"
            },
            {
              name: "Wellness",
              tools: tools.filter(t => t.name.includes('wellness') || t.name.includes('dashboard')),
              color: "yellow"
            }
          ].map((category) => (
            <div key={category.name} className="p-4 bg-white/[0.02] rounded-lg border border-white/10">
              <div className="font-medium text-primary-400">{category.name}</div>
              <div className="text-sm text-white/70 mt-2">
                {category.tools.length} tools available
              </div>
              <div className="text-xs text-white/50 mt-1">
                {category.tools.map(t => t.name).join(', ')}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

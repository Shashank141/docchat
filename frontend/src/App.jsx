import { useState, useRef, useEffect } from 'react'

const API_BASE = 'http://localhost:8000'

export default function App() {
  const [sessionId, setSessionId] = useState(null)
  const [filename, setFilename] = useState('')
  const [messages, setMessages] = useState([])
  const [question, setQuestion] = useState('')
  const [uploading, setUploading] = useState(false)
  const [asking, setAsking] = useState(false)
  const [error, setError] = useState('')
  const fileInputRef = useRef(null)
  const messagesEndRef = useRef(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  async function handleFileUpload(e) {
    const file = e.target.files[0]
    if (!file) return

    setError('')
    setUploading(true)
    setMessages([])

    const formData = new FormData()
    formData.append('file', file)

    try {
      const res = await fetch(`${API_BASE}/upload`, {
        method: 'POST',
        body: formData,
      })
      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || 'Upload failed')
      }
      const data = await res.json()
      setSessionId(data.session_id)
      setFilename(data.filename)
      setMessages([
        {
          role: 'assistant',
          content: `Loaded "${data.filename}" (${data.num_chunks} chunks indexed). Ask me anything about it.`,
        },
      ])
    } catch (err) {
      setError(err.message)
    } finally {
      setUploading(false)
    }
  }

  async function handleAsk(e) {
    e.preventDefault()
    if (!question.trim() || !sessionId || asking) return

    const userMessage = question.trim()
    setMessages((prev) => [...prev, { role: 'user', content: userMessage }])
    setQuestion('')
    setAsking(true)
    setError('')

    try {
      const res = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId, question: userMessage }),
      })
      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || 'Failed to get an answer')
      }
      const data = await res.json()
      setMessages((prev) => [...prev, { role: 'assistant', content: data.answer }])
    } catch (err) {
      setError(err.message)
    } finally {
      setAsking(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center px-4 py-10">
      <div className="w-full max-w-2xl">
        <header className="mb-8 text-center">
          <h1 className="text-2xl font-semibold text-gray-900">DocChat</h1>
          <p className="text-sm text-gray-500 mt-1">Upload a PDF and ask questions about it.</p>
        </header>

        <div className="bg-white border border-gray-200 rounded-lg shadow-sm">
          {/* Upload bar */}
          <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100">
            <div className="text-sm text-gray-700 truncate">
              {filename ? (
                <span>
                  <span className="text-gray-400">Document:</span> {filename}
                </span>
              ) : (
                <span className="text-gray-400">No document loaded</span>
              )}
            </div>
            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={uploading}
              className="text-sm px-3 py-1.5 rounded-md bg-gray-900 text-white hover:bg-gray-700 disabled:opacity-50 transition"
            >
              {uploading ? 'Uploading…' : filename ? 'Replace PDF' : 'Upload PDF'}
            </button>
            <input
              ref={fileInputRef}
              type="file"
              accept="application/pdf"
              onChange={handleFileUpload}
              className="hidden"
            />
          </div>

          {/* Chat window */}
          <div className="h-96 overflow-y-auto px-5 py-4 space-y-3">
            {messages.length === 0 && (
              <div className="h-full flex items-center justify-center text-sm text-gray-400">
                Upload a PDF to start chatting
              </div>
            )}
            {messages.map((m, i) => (
              <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div
                  className={`max-w-[80%] rounded-lg px-3 py-2 text-sm ${
                    m.role === 'user'
                      ? 'bg-gray-900 text-white'
                      : 'bg-gray-100 text-gray-800'
                  }`}
                >
                  {m.content}
                </div>
              </div>
            ))}
            {asking && (
              <div className="flex justify-start">
                <div className="max-w-[80%] rounded-lg px-3 py-2 text-sm bg-gray-100 text-gray-400 italic">
                  Thinking…
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input bar */}
          <form onSubmit={handleAsk} className="flex items-center gap-2 px-5 py-4 border-t border-gray-100">
            <input
              type="text"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder={sessionId ? 'Ask a question about the document…' : 'Upload a document first'}
              disabled={!sessionId || asking}
              className="flex-1 text-sm border border-gray-200 rounded-md px-3 py-2 focus:outline-none focus:ring-1 focus:ring-gray-400 disabled:bg-gray-50"
            />
            <button
              type="submit"
              disabled={!sessionId || asking || !question.trim()}
              className="text-sm px-4 py-2 rounded-md bg-gray-900 text-white hover:bg-gray-700 disabled:opacity-50 transition"
            >
              Send
            </button>
          </form>
        </div>

        {error && (
          <p className="mt-3 text-sm text-red-600 text-center">{error}</p>
        )}
      </div>
    </div>
  )
}

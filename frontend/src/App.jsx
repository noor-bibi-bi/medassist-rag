import { useState, useEffect, useRef } from 'react'
import ReactMarkdown from 'react-markdown'

const ABSTENTION_PHRASE = "don't have enough information"

const EXAMPLE_QUESTIONS = [
  "What are the contraindications for metformin?",
  "What are the allergy warnings for ibuprofen?",
  "Will ibuprofen interact with my cat's medication?",
]

function SourceCard({ source, index }) {
  return (
    <details className="bg-white border border-parchment rounded-md p-3 group">
      <summary className="cursor-pointer font-body text-sm text-ink flex items-center justify-between">
        <span>
          <span className="font-mono text-xs text-warmgray mr-2">[{index + 1}]</span>
          <span className="font-medium">{source.drug_name}</span>
          <span className="text-warmgray"> — {source.section_type}</span>
        </span>
        <span className="font-mono text-xs text-warmgray">
          d={source.distance.toFixed(3)}
        </span>
      </summary>
      <div className="mt-3 pt-3 border-t border-parchment">
        <p className="font-mono text-xs text-warmgray mb-2">
          {source.manufacturer}
          {source.subheader && ` · ${source.subheader}`}
        </p>
        <p className="font-body text-sm text-ink leading-relaxed">
          {source.text}
        </p>
      </div>
    </details>
  )
}

function AnswerCard({ result }) {
  const isAbstention = result.answer.toLowerCase().includes(ABSTENTION_PHRASE)

  if (isAbstention) {
    return (
      <div className="border-l-4 border-amber bg-white rounded-md p-5">
        <p className="font-mono text-xs text-amber uppercase tracking-wider mb-2">
          No confident match in source data
        </p>
        <p className="font-body text-ink leading-relaxed">{result.answer}</p>
      </div>
    )
  }

  return (
    <div className="bg-white border border-parchment rounded-md p-5">
      <p className="font-body text-ink leading-relaxed whitespace-pre-line">
        {result.answer}
      </p>

      {result.sources.length > 0 && (
        <div className="mt-5">
          <p className="font-mono text-xs text-warmgray uppercase tracking-wider mb-2">
            Sources ({result.sources.length})
          </p>
          <div className="space-y-2">
            {result.sources.map((source, i) => (
              <SourceCard key={i} source={source} index={i} />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function flattenListIndentation(text) {
  return text
    .split('\n')
    .map((line) => line.replace(/^\s+([*\-])/, '$1'))
    .join('\n')
}

function ChatMessage({ message, onEdit }) {
  const isAbstention = message.answer?.toLowerCase().includes(ABSTENTION_PHRASE)

  return (
    <div className="mb-6">
      {/* Question bubble */}
      <div className="flex justify-end mb-2 group">
        <button
          onClick={() => onEdit(message.id, message.question)}
          className="opacity-0 group-hover:opacity-100 transition-opacity font-mono text-xs text-warmgray self-center mr-2 hover:text-pharmacy"
          title="Edit and resend"
        >
          edit
        </button>
        <div className="bg-pharmacy text-paper font-body rounded-2xl rounded-tr-sm px-4 py-2 max-w-md">
          {message.question}
        </div>
      </div>

      {/* Answer */}
      <div className="flex justify-start">
        <div className="max-w-xl w-full">
          {message.loading && (
            <p className="font-mono text-xs text-warmgray">Searching label data…</p>
          )}

          {message.error && (
            <p className="font-mono text-sm text-amber">Request failed: {message.error}</p>
          )}

          {message.answer && !message.loading && (
            isAbstention ? (
              <div className="border-l-4 border-amber bg-white rounded-md p-4">
                <p className="font-mono text-xs text-amber uppercase tracking-wider mb-2">
                  No confident match in source data
                </p>
                <p className="font-body text-ink leading-relaxed">{message.answer}</p>
              </div>
            ) : (
              <div className="bg-white border border-parchment rounded-md p-4">
                <div className="font-body text-ink leading-relaxed prose prose-sm max-w-none prose-p:my-2 prose-ul:my-2 prose-li:my-0.5">
                  <ReactMarkdown>{flattenListIndentation(message.answer)}</ReactMarkdown>
                </div>
                {message.sources.length > 0 && (
                  <div className="mt-4">
                    <p className="font-mono text-xs text-warmgray uppercase tracking-wider mb-2">
                      Sources ({message.sources.length})
                    </p>
                    <div className="space-y-2">
                      {message.sources.map((source, i) => (
                        <SourceCard key={i} source={source} index={i} />
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )
          )}
        </div>
      </div>
    </div>
  )
}

function App() {
  const [input, setInput] = useState('')
  const [messages, setMessages] = useState([])
  const [editingId, setEditingId] = useState(null)

  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const askBackend = async (questionText) => {
    const response = await fetch('http://127.0.0.1:8000/ask', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question: questionText }),
    })

    if (!response.ok) {
      throw new Error(`Server responded with status ${response.status}`)
    }

    return response.json()
  }

  const handleSend = async () => {
    const trimmed = input.trim()
    if (!trimmed) return

    if (editingId !== null) {
      // Editing an existing message: truncate everything from that point
      // forward, then re-ask with the edited text.
      const editIndex = messages.findIndex((m) => m.id === editingId)
      const messageId = editingId

      setMessages((prev) => [
        ...prev.slice(0, editIndex),
        { id: messageId, question: trimmed, answer: null, sources: [], loading: true, error: null },
      ])
      setEditingId(null)
      setInput('')

      try {
        const data = await askBackend(trimmed)
        setMessages((prev) =>
          prev.map((m) =>
            m.id === messageId
              ? { ...m, answer: data.answer, sources: data.sources, loading: false }
              : m
          )
        )
      } catch (err) {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === messageId ? { ...m, loading: false, error: err.message } : m
          )
        )
      }
      return
    }

    // Sending a brand-new message
    const messageId = crypto.randomUUID()
    setMessages((prev) => [
      ...prev,
      { id: messageId, question: trimmed, answer: null, sources: [], loading: true, error: null },
    ])
    setInput('')

    try {
      const data = await askBackend(trimmed)
      setMessages((prev) =>
        prev.map((m) =>
          m.id === messageId
            ? { ...m, answer: data.answer, sources: data.sources, loading: false }
            : m
        )
      )
    } catch (err) {
      setMessages((prev) =>
        prev.map((m) =>
          m.id === messageId ? { ...m, loading: false, error: err.message } : m
        )
      )
    }
  }

  const startEditing = (messageId, currentQuestion) => {
    setEditingId(messageId)
    setInput(currentQuestion)
  }

  const cancelEditing = () => {
    setEditingId(null)
    setInput('')
  }

  return (
    <div className="bg-paper min-h-screen flex flex-col">
      {/* Scrollable message area */}
      <div className="flex-1 overflow-y-auto px-6 py-8">
        <div className="max-w-2xl mx-auto">

          {messages.length === 0 && (
            <header className="mb-10">
              <p className="font-mono text-xs text-warmgray uppercase tracking-wider">
                clinical reference tool — demo
              </p>
              <h1 className="font-display text-5xl font-bold text-pharmacy mt-1">
                MedAssist
              </h1>
              <p className="font-body text-warmgray mt-3 max-w-lg">
                Ask a question about an FDA-labeled drug. Answers are grounded in
                real label data and cite their source — or decline when the
                source data doesn't support a confident answer.
              </p>
              <p className="font-mono text-xs text-amber mt-3 max-w-lg">
                Educational demo only — not medical advice. Built on public FDA label
                data, not a substitute for consulting a healthcare professional.
              </p>

              <div className="mt-6 flex flex-wrap gap-2">
                {EXAMPLE_QUESTIONS.map((q) => (
                  <button
                    key={q}
                    onClick={() => {
                      setInput(q)
                      // auto-send on next tick, after input state updates
                      setTimeout(() => {
                        document.getElementById('chat-input-form').requestSubmit()
                      }, 0)
                    }}
                    className="font-mono text-xs text-warmgray border border-parchment bg-white rounded-full px-3 py-1.5 hover:border-pharmacy hover:text-pharmacy transition-colors"
                  >
                    {q}
                  </button>
                ))}
              </div>
            </header>
          )}

          {messages.map((message) => (
            <ChatMessage key={message.id} message={message} onEdit={startEditing} />
          ))}
          <div ref={bottomRef} />

        </div>
      </div>

      {/* Fixed input bar at the bottom */}
      <div className="border-t border-parchment bg-paper px-6 py-4">
        <div className="max-w-2xl mx-auto">
          {editingId !== null && (
            <div className="flex items-center justify-between mb-2">
              <p className="font-mono text-xs text-pharmacy">Editing message — this will regenerate the answer</p>
              <button onClick={cancelEditing} className="font-mono text-xs text-warmgray hover:text-amber">
                cancel
              </button>
            </div>
          )}
          <form
            id="chat-input-form"
            onSubmit={(e) => {
              e.preventDefault()
              handleSend()
            }}
            className="relative flex items-end"
          >
            <textarea
              className="w-full font-body text-ink bg-white border border-parchment rounded-md p-3 pr-12 resize-none focus:outline-none focus:ring-2 focus:ring-pharmacy"
              rows={1}
              placeholder="Ask about an FDA-labeled drug…"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault()
                  handleSend()
                }
              }}
            />
            <button
              type="submit"
              disabled={!input.trim()}
              className="absolute right-2 bottom-2 bg-pharmacy text-paper rounded-full w-8 h-8 flex items-center justify-center disabled:opacity-30 hover:opacity-90 transition-opacity"
              aria-label="Send"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 19V5M5 12l7-7 7 7" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}

export default App
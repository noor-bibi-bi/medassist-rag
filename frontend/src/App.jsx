import { useState } from 'react'

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

function App() {
  const [question, setQuestion] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  const handleAsk = async () => {
    if (!question.trim()) return

    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const response = await fetch('http://127.0.0.1:8000/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question }),
      })

      if (!response.ok) {
        throw new Error(`Server responded with status ${response.status}`)
      }

      const data = await response.json()
      setResult(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="bg-paper min-h-screen px-6 py-12">
      <div className="max-w-2xl mx-auto">

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
        </header>

        <div className="mb-8">
          <textarea
            className="w-full font-body text-ink bg-white border border-parchment rounded-md p-4 resize-none focus:outline-none focus:ring-2 focus:ring-pharmacy"
            rows={3}
            placeholder="e.g. What are the contraindications for metformin?"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
          />
          <button
            onClick={handleAsk}
            disabled={loading}
            className="mt-3 bg-pharmacy text-paper font-body font-medium px-5 py-2 rounded-md disabled:opacity-50"
          >
            {loading ? 'Searching label data…' : 'Ask'}
          </button>

          {!result && !loading && (
            <div className="mt-4 flex flex-wrap gap-2">
              {EXAMPLE_QUESTIONS.map((q) => (
                <button
                  key={q}
                  onClick={() => setQuestion(q)}
                  className="font-mono text-xs text-warmgray border border-parchment bg-white rounded-full px-3 py-1.5 hover:border-pharmacy hover:text-pharmacy transition-colors"
                >
                  {q}
                </button>
              ))}
            </div>
          )}
        </div>

        {error && (
          <p className="font-mono text-sm text-amber">
            Request failed: {error}
          </p>
        )}

        {result && <AnswerCard result={result} />}

      </div>
    </div>
  )
}

export default App
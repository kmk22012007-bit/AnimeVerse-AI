import React, { useState, useRef, useEffect } from 'react'
import { Bot, Sparkles, Send, User, Loader2, RefreshCw } from 'lucide-react'
import { sendRyukMessage } from '../api/ryuk'

const SUGGESTIONS = [
  'Recommend dark psychological anime like Death Note',
  'Summarize my progress',
  'Recommend cyberpunk anime with high ratings',
  'Who is Frieren and what is her story?',
]

export const RyukAssistantPage = () => {
  const [messages, setMessages] = useState([
    {
      id: 'init',
      role: 'assistant',
      text: 'Greetings, human. I am RYUK, your cybernetic anime companion powered by Gemini AI and the Tenrai registry. Ask me for recommendations, plot explanations, character analyses, or progress summaries from your watchlist.',
      isFallback: false,
    },
  ])
  const [inputText, setInputText] = useState('')
  const [loading, setLoading] = useState(false)
  const [conversationId, setConversationId] = useState(null)
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, loading])

  const handleSendMessage = async (textToSend) => {
    const query = (textToSend || inputText).trim()
    if (!query || loading) return

    const userMsg = {
      id: Date.now().toString(),
      role: 'user',
      text: query,
    }

    setMessages((prev) => [...prev, userMsg])
    setInputText('')
    setLoading(true)

    try {
      const res = await sendRyukMessage(query, conversationId)
      if (res?.conversation_id) {
        setConversationId(res.conversation_id)
      }

      const botReply = res?.reply || 'I hear you, mortal. What else do you seek from the anime realm?'
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          text: botReply,
          isFallback: false,
        },
      ])
    } catch (err) {
      // Handle fallback response
      const errData = err.response?.data
      const fallbackMsg =
        errData?.message ||
        "I'm temporarily conserving power, human. Here are some top trending anime you might enjoy instead."

      if (errData?.conversation_id) {
        setConversationId(errData.conversation_id)
      }

      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          text: fallbackMsg,
          isFallback: true,
          suggestions: errData?.suggestions || [],
        },
      ])
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-wide flex items-center gap-2.5">
            <Bot className="w-7 h-7 text-purple-400" />
            RYUK AI Assistant
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-1 font-mono">
            Cybernetic Anime Intelligence • Gemini Powered • Real Metadata
          </p>
        </div>
      </div>

      {/* Main Terminal Container */}
      <div className="rounded-3xl bg-[#0c0e1e] border border-purple-500/30 overflow-hidden shadow-[0_0_35px_rgba(168,85,247,0.18)] flex flex-col h-[600px]">
        {/* Terminal Header */}
        <div className="p-4 border-b border-purple-500/20 bg-purple-950/40 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-xl bg-purple-600 border border-purple-400 flex items-center justify-center text-white shadow-[0_0_10px_rgba(168,85,247,0.5)]">
              <Bot className="w-4 h-4" />
            </div>
            <div>
              <div className="text-sm font-bold text-white flex items-center gap-2">
                RYUK <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-cyan-500/20 text-cyan-300 border border-cyan-400/40">ONLINE</span>
              </div>
              <div className="text-[11px] text-slate-400 font-mono">
                Integrated Anime Intelligence Core
              </div>
            </div>
          </div>

          <button
            onClick={() => {
              setMessages([
                {
                  id: 'init',
                  role: 'assistant',
                  text: 'Greetings, human. I am RYUK, your cybernetic anime companion. Ask me for recommendations, plot explanations, or watchlist progress.',
                  isFallback: false,
                },
              ])
              setConversationId(null)
            }}
            type="button"
            className="inline-flex items-center gap-1.5 px-3 py-1 rounded-xl bg-purple-900/30 hover:bg-purple-800/50 border border-purple-500/20 text-xs font-mono text-purple-300 transition-colors cursor-pointer"
            title="Reset conversation"
          >
            <RefreshCw className="w-3 h-3" />
            <span>Reset</span>
          </button>
        </div>

        {/* Message Thread */}
        <div className="flex-1 p-4 sm:p-6 space-y-4 overflow-y-auto">
          {messages.map((m) => {
            const isUser = m.role === 'user'
            return (
              <div
                key={m.id}
                className={`flex items-start gap-3 max-w-2xl ${
                  isUser ? 'ml-auto flex-row-reverse' : ''
                }`}
              >
                <div
                  className={`w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0 text-white ${
                    isUser
                      ? 'bg-purple-600 border border-purple-400'
                      : 'bg-purple-950/80 border border-purple-500/40 text-purple-300'
                  }`}
                >
                  {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
                </div>

                <div
                  className={`p-4 rounded-2xl text-xs sm:text-sm leading-relaxed ${
                    isUser
                      ? 'bg-purple-600 text-white font-medium rounded-tr-none shadow-[0_0_15px_rgba(168,85,247,0.3)]'
                      : 'bg-[#12142a] border border-purple-500/25 text-slate-200 rounded-tl-none shadow-sm'
                  }`}
                >
                  <p className="whitespace-pre-wrap">{m.text}</p>

                  {/* Fallback suggestion pills */}
                  {m.suggestions && m.suggestions.length > 0 && (
                    <div className="mt-3 pt-2 border-t border-purple-500/20 flex flex-wrap gap-2">
                      {m.suggestions.map((s, idx) => (
                        <span
                          key={idx}
                          className="px-2.5 py-1 rounded-lg bg-purple-950/60 border border-purple-500/30 text-purple-300 text-xs font-mono"
                        >
                          {s.title || s}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )
          })}

          {loading && (
            <div className="flex items-start gap-3 max-w-lg">
              <div className="w-8 h-8 rounded-xl bg-purple-950/80 border border-purple-500/40 flex items-center justify-center flex-shrink-0 text-purple-300">
                <Bot className="w-4 h-4" />
              </div>
              <div className="p-3.5 rounded-2xl bg-[#12142a] border border-purple-500/25 text-xs text-purple-300 flex items-center gap-2 font-mono">
                <Loader2 className="w-3.5 h-3.5 animate-spin text-purple-400" />
                <span>RYUK is consulting the death note archives...</span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Quick Suggestions Strip */}
        <div className="px-4 py-2 border-t border-purple-950/80 bg-purple-950/20 flex items-center gap-2 overflow-x-auto scrollbar-none text-xs">
          <span className="text-slate-400 font-mono text-[11px] whitespace-nowrap flex items-center gap-1">
            <Sparkles className="w-3 h-3 text-cyan-400" /> Ask:
          </span>
          {SUGGESTIONS.map((prompt, idx) => (
            <button
              key={idx}
              onClick={() => handleSendMessage(prompt)}
              disabled={loading}
              type="button"
              className="px-2.5 py-1 rounded-lg bg-purple-950/40 hover:bg-purple-900/60 border border-purple-500/20 text-purple-300 text-[11px] whitespace-nowrap transition-colors cursor-pointer disabled:opacity-40"
            >
              {prompt}
            </button>
          ))}
        </div>

        {/* Input Bar */}
        <div className="p-4 border-t border-purple-500/20 bg-purple-950/30 flex gap-3">
          <input
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask RYUK for recommendations, plot questions, or progress..."
            disabled={loading}
            className="flex-1 px-4 py-2.5 rounded-xl bg-purple-950/40 border border-purple-500/30 text-xs sm:text-sm text-slate-100 placeholder:text-slate-500 focus:outline-none focus:border-purple-400"
          />
          <button
            onClick={() => handleSendMessage()}
            disabled={!inputText.trim() || loading}
            type="button"
            className="px-5 py-2.5 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-medium text-xs sm:text-sm transition-all shadow-[0_0_15px_rgba(168,85,247,0.4)] flex items-center gap-2 disabled:opacity-40 cursor-pointer"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
            <span>Send</span>
          </button>
        </div>
      </div>
    </div>
  )
}

export default RyukAssistantPage

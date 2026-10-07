import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { clearChatHistory, fetchChatHistory, sendChatMessage } from '../lib/api'
import type { PageContext } from '../lib/api'
import { renderChatText } from '../lib/formatChatText'
import { useAuth } from '../context/AuthContext'
import { useChatResults } from '../context/ChatResultsContext'
import { useViewingProduct } from '../context/ViewingProductContext'
import type { Product } from '../types/product'

interface ChatMessage {
  id: number
  role: 'user' | 'assistant'
  text: string
  products?: Product[]
}

const GREETING: ChatMessage = {
  id: 0,
  role: 'assistant',
  text: "Hi! I'm the Campus Customs shopping assistant.",
}

// Cycled while waiting on a reply, in place of a plain "..." — small bit of
// Yale personality in an otherwise purely functional loading state.
const LOADING_MESSAGES = [
  'Asking the Bulldog…',
  'Checking Phelps Gate…',
  'Flipping through the catalogue…',
  'Consulting Handsome Dan…',
  'Sniffing out your size…',
  'Fetching from the Yale Co-op…',
]

// A fun, deterministic easter egg: detected client-side (not left to the
// model to decide) so the confetti always fires the instant someone types
// Yale's fight song cheer, regardless of what the agent itself says back.
const BOOLA_BOOLA_REGEX = /\bboola\s*boola\b/i
const CONFETTI_COLORS = ['#00356b', '#286dc0', '#ffffff', '#978d85']

function pageFromPathname(pathname: string): PageContext['page'] {
  if (pathname === '/') return 'home'
  if (pathname === '/products') return 'products'
  if (pathname.startsWith('/products/')) return 'product_detail'
  if (pathname === '/about') return 'about'
  if (pathname === '/login') return 'login'
  if (pathname === '/create-account') return 'create_account'
  return 'unknown'
}

function ChatWidget() {
  const { user } = useAuth()
  const { setResults } = useChatResults()
  const { viewingProduct } = useViewingProduct()
  const navigate = useNavigate()
  const location = useLocation()
  const [isOpen, setIsOpen] = useState(false)
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const [messages, setMessages] = useState<ChatMessage[]>([GREETING])
  const [loadingMessageIndex, setLoadingMessageIndex] = useState(0)
  const [confettiKey, setConfettiKey] = useState<number | null>(null)

  useEffect(() => {
    if (!sending) return
    setLoadingMessageIndex(Math.floor(Math.random() * LOADING_MESSAGES.length))
    const interval = setInterval(() => {
      setLoadingMessageIndex((i) => (i + 1) % LOADING_MESSAGES.length)
    }, 1400)
    return () => clearInterval(interval)
  }, [sending])

  useEffect(() => {
    if (confettiKey === null) return
    const timeout = setTimeout(() => setConfettiKey(null), 1800)
    return () => clearTimeout(timeout)
  }, [confettiKey])

  // Returning, logged-in shoppers get their past conversation back; guests
  // (and a logged-out visitor) always start fresh, since their history was
  // never saved server-side in the first place.
  useEffect(() => {
    if (!user) {
      setMessages([GREETING])
      return
    }
    let cancelled = false
    fetchChatHistory(user.sessionToken)
      .then((history) => {
        if (cancelled) return
        if (history.length === 0) {
          setMessages([GREETING])
          return
        }
        setMessages(
          history.map((m, i) => ({
            id: i,
            role: m.role,
            text: m.content,
            products: m.products,
          })),
        )
      })
      .catch(() => {
        if (!cancelled) setMessages([GREETING])
      })
    return () => {
      cancelled = true
    }
  }, [user])

  async function handleClearHistory() {
    if (!user) return
    if (!window.confirm('Clear your saved chat history? This can’t be undone.')) return
    try {
      await clearChatHistory(user.sessionToken)
      setMessages([GREETING])
    } catch {
      // Leave the visible history as-is if the request failed — better than
      // pretending it was cleared when the server still has it.
    }
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    const text = input.trim()
    if (!text || sending) return

    const userMessage: ChatMessage = { id: Date.now(), role: 'user', text }
    setMessages((prev) => [...prev, userMessage])
    setInput('')
    setSending(true)

    if (BOOLA_BOOLA_REGEX.test(text)) {
      setConfettiKey(Date.now())
    }

    const page = pageFromPathname(location.pathname)
    const pageContext: PageContext =
      page === 'product_detail' && viewingProduct ? { page, productId: viewingProduct.productId } : { page }

    try {
      const reply = await sendChatMessage({ token: user?.sessionToken ?? null, message: text, pageContext })
      setMessages((prev) => [
        ...prev,
        { id: Date.now() + 1, role: 'assistant', text: reply.message, products: reply.products },
      ])
      // Only treat this as a "search" that should take the shopper to a
      // results page when they weren't already looking at a specific
      // product. On a product detail page, any products in the reply are
      // just the agent confirming/describing the item already on screen
      // (stock, color, size questions) — navigating away to a one-item
      // "results" list would yank them off the page they're reading.
      if (reply.products.length > 0 && page !== 'product_detail') {
        setResults(reply.products)
        navigate('/products')
      }
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 1,
          role: 'assistant',
          text: "Sorry, I'm having trouble connecting right now. Please try again in a moment.",
        },
      ])
    } finally {
      setSending(false)
    }
  }

  return (
    <div className="chat-widget">
      {confettiKey !== null && (
        <div className="confetti-burst" aria-hidden="true">
          {Array.from({ length: 28 }).map((_, i) => (
            <span
              key={`${confettiKey}-${i}`}
              className="confetti-piece"
              style={{
                left: `${Math.random() * 100}%`,
                animationDelay: `${Math.random() * 0.3}s`,
                background: CONFETTI_COLORS[i % CONFETTI_COLORS.length],
                transform: `rotate(${Math.random() * 360}deg)`,
              }}
            />
          ))}
        </div>
      )}
      {isOpen && (
        <div className="chat-panel">
          <div className="chat-panel-header">
            <span>Campus Customs Assistant</span>
            <div className="chat-panel-header-actions">
              {user && (
                <button
                  type="button"
                  className="chat-clear-history"
                  onClick={handleClearHistory}
                  aria-label="Clear chat history"
                  title="Clear chat history"
                >
                  🗑
                </button>
              )}
              <button
                type="button"
                className="chat-close"
                onClick={() => setIsOpen(false)}
                aria-label="Close chat"
              >
                ×
              </button>
            </div>
          </div>
          <div className="chat-messages">
            {messages.map((message) => (
              <div key={message.id} className={`chat-message ${message.role}`}>
                <div>{renderChatText(message.text)}</div>
                {message.products && message.products.length > 0 && (
                  <div className="chat-product-chips">
                    {message.products.map((product) => (
                      <Link
                        key={product.productId}
                        to={`/products/${product.productId}`}
                        className="chat-product-chip"
                        onClick={() => setIsOpen(false)}
                      >
                        {product.name} — ${product.price.toFixed(2)}
                      </Link>
                    ))}
                  </div>
                )}
              </div>
            ))}
            {sending && (
              <div className="chat-message assistant chat-loading" aria-label="Assistant is typing">
                <span className="chat-typing">
                  <span />
                  <span />
                  <span />
                </span>
                <span className="chat-loading-text">{LOADING_MESSAGES[loadingMessageIndex]}</span>
              </div>
            )}
          </div>
          <form className="chat-input-row" onSubmit={handleSubmit}>
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about a product…"
              aria-label="Chat message"
              disabled={sending}
            />
            <button type="submit" className="btn btn-primary" disabled={sending}>
              Send
            </button>
          </form>
        </div>
      )}
      {!isOpen && (
        <button
          type="button"
          className="chat-toggle"
          onClick={() => setIsOpen(true)}
          aria-label="Open chat"
        >
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
            <path
              d="M4 5.5C4 4.67 4.67 4 5.5 4h13c.83 0 1.5.67 1.5 1.5v10c0 .83-.67 1.5-1.5 1.5H9l-4 3.5v-3.5H5.5C4.67 17 4 16.33 4 15.5v-10Z"
              stroke="currentColor"
              strokeWidth="1.8"
              strokeLinejoin="round"
            />
            <circle cx="8.5" cy="10.5" r="1" fill="currentColor" />
            <circle cx="12" cy="10.5" r="1" fill="currentColor" />
            <circle cx="15.5" cy="10.5" r="1" fill="currentColor" />
          </svg>
        </button>
      )}
    </div>
  )
}

export default ChatWidget

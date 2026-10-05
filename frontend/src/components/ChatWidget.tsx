import { useState } from 'react'
import type { FormEvent } from 'react'

interface ChatMessage {
  id: number
  role: 'user' | 'assistant'
  text: string
}

// Stub for now — Problem 5 wires this up to call the FastAPI agent backend.
async function sendToAssistant(_message: string): Promise<string> {
  return "Thanks for reaching out! I can't look anything up yet, but I'll be able to help you find products soon."
}

function ChatWidget() {
  const [isOpen, setIsOpen] = useState(false)
  const [input, setInput] = useState('')
  const [messages, setMessages] = useState<ChatMessage[]>([
    { id: 0, role: 'assistant', text: 'Hi! I\'m the Campus Customs shopping assistant.' },
  ])

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    const text = input.trim()
    if (!text) return

    const userMessage: ChatMessage = { id: Date.now(), role: 'user', text }
    setMessages((prev) => [...prev, userMessage])
    setInput('')

    const reply = await sendToAssistant(text)
    setMessages((prev) => [...prev, { id: Date.now() + 1, role: 'assistant', text: reply }])
  }

  return (
    <div className="chat-widget">
      {isOpen && (
        <div className="chat-panel">
          <div className="chat-panel-header">
            <span>Campus Customs Assistant</span>
            <button
              type="button"
              className="chat-close"
              onClick={() => setIsOpen(false)}
              aria-label="Close chat"
            >
              ×
            </button>
          </div>
          <div className="chat-messages">
            {messages.map((message) => (
              <div key={message.id} className={`chat-message ${message.role}`}>
                {message.text}
              </div>
            ))}
          </div>
          <form className="chat-input-row" onSubmit={handleSubmit}>
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about a product…"
              aria-label="Chat message"
            />
            <button type="submit" className="btn btn-primary">
              Send
            </button>
          </form>
        </div>
      )}
      <button
        type="button"
        className="chat-toggle"
        onClick={() => setIsOpen((prev) => !prev)}
        aria-label={isOpen ? 'Close chat' : 'Open chat'}
      >
        {isOpen ? '×' : '💬'}
      </button>
    </div>
  )
}

export default ChatWidget

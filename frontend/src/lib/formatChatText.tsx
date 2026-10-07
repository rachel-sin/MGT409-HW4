import type { ReactNode } from 'react'

// Renders the small markdown subset the agent actually produces (**bold**
// and "- " bullet lists — confirmed against output/audit_trail.json) as real
// React elements, not raw HTML — so there's no need for dangerouslySetInnerHTML
// or a sanitizer, and nothing beyond that subset is supported since the
// agent's prompt never asks it to write anything else.

function renderInline(text: string, keyPrefix: string): ReactNode[] {
  const parts = text.split(/(\*\*[^*]+\*\*)/g).filter((part) => part.length > 0)
  return parts.map((part, i) =>
    part.startsWith('**') && part.endsWith('**') ? (
      <strong key={`${keyPrefix}-${i}`}>{part.slice(2, -2)}</strong>
    ) : (
      <span key={`${keyPrefix}-${i}`}>{part}</span>
    ),
  )
}

export function renderChatText(text: string): ReactNode {
  const lines = text.split('\n')
  const blocks: ReactNode[] = []
  let bulletBuffer: string[] = []

  function flushBullets(key: string) {
    if (bulletBuffer.length === 0) return
    blocks.push(
      <ul key={`ul-${key}`} className="chat-text-list">
        {bulletBuffer.map((item, i) => (
          <li key={`li-${key}-${i}`}>{renderInline(item, `li-${key}-${i}`)}</li>
        ))}
      </ul>,
    )
    bulletBuffer = []
  }

  lines.forEach((line, idx) => {
    const bulletMatch = line.trim().match(/^[-*•]\s+(.*)$/)
    if (bulletMatch) {
      bulletBuffer.push(bulletMatch[1])
      return
    }
    flushBullets(String(idx))
    if (line.trim().length === 0) return
    blocks.push(
      <p key={`p-${idx}`} className="chat-text-line">
        {renderInline(line, `p-${idx}`)}
      </p>,
    )
  })
  flushBullets('end')

  return blocks
}

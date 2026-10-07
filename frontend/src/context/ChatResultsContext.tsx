import { createContext, useContext, useState } from 'react'
import type { ReactNode } from 'react'
import type { Product } from '../types/product'

interface ChatResultsContextValue {
  results: Product[]
  setResults: (products: Product[]) => void
  clearResults: () => void
}

const ChatResultsContext = createContext<ChatResultsContextValue | undefined>(undefined)

export function ChatResultsProvider({ children }: { children: ReactNode }) {
  const [results, setResults] = useState<Product[]>([])

  return (
    <ChatResultsContext.Provider value={{ results, setResults, clearResults: () => setResults([]) }}>
      {children}
    </ChatResultsContext.Provider>
  )
}

export function useChatResults(): ChatResultsContextValue {
  const ctx = useContext(ChatResultsContext)
  if (!ctx) throw new Error('useChatResults must be used within ChatResultsProvider')
  return ctx
}

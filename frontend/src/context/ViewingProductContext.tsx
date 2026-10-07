import { createContext, useContext, useState } from 'react'
import type { ReactNode } from 'react'

interface ViewingProduct {
  productId: string
}

interface ViewingProductContextValue {
  viewingProduct: ViewingProduct | null
  setViewingProduct: (product: ViewingProduct | null) => void
}

const ViewingProductContext = createContext<ViewingProductContextValue | undefined>(undefined)

export function ViewingProductProvider({ children }: { children: ReactNode }) {
  const [viewingProduct, setViewingProduct] = useState<ViewingProduct | null>(null)

  return (
    <ViewingProductContext.Provider value={{ viewingProduct, setViewingProduct }}>
      {children}
    </ViewingProductContext.Provider>
  )
}

export function useViewingProduct(): ViewingProductContextValue {
  const ctx = useContext(ViewingProductContext)
  if (!ctx) throw new Error('useViewingProduct must be used within ViewingProductProvider')
  return ctx
}

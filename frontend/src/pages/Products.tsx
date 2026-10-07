import { useEffect, useState } from 'react'
import ProductCard from '../components/ProductCard'
import { fetchProducts } from '../lib/api'
import { useChatResults } from '../context/ChatResultsContext'
import type { Product } from '../types/product'

function Products() {
  const { results, clearResults } = useChatResults()
  const [products, setProducts] = useState<Product[]>([])
  const [status, setStatus] = useState<'loading' | 'error' | 'ready'>('loading')

  useEffect(() => {
    let cancelled = false
    fetchProducts()
      .then((data) => {
        if (!cancelled) {
          setProducts(data)
          setStatus('ready')
        }
      })
      .catch(() => {
        if (!cancelled) setStatus('error')
      })
    return () => {
      cancelled = true
    }
  }, [])

  const showingChatResults = results.length > 0
  const visibleProducts = showingChatResults ? results : products

  return (
    <div className="page products-page">
      <h1>Products</h1>

      {showingChatResults && (
        <div className="chat-filter-banner">
          <span>
            Showing {results.length} result{results.length === 1 ? '' : 's'} from your chat
          </span>
          <button type="button" className="chat-filter-clear" onClick={clearResults}>
            Show All Products
          </button>
        </div>
      )}

      {!showingChatResults && status === 'loading' && <p>Loading products…</p>}
      {!showingChatResults && status === 'error' && (
        <p>Couldn't load products. Is the backend running at {import.meta.env.VITE_API_BASE_URL}?</p>
      )}
      {(showingChatResults || status === 'ready') && (
        <div className="product-grid">
          {visibleProducts.map((product) => (
            <ProductCard key={product.productId} product={product} />
          ))}
        </div>
      )}
    </div>
  )
}

export default Products

import { useEffect, useState } from 'react'
import ProductCard from '../components/ProductCard'
import { fetchProducts } from '../lib/api'
import type { Product } from '../types/product'

function Products() {
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

  return (
    <div className="page products-page">
      <h1>Products</h1>
      {status === 'loading' && <p>Loading products…</p>}
      {status === 'error' && (
        <p>Couldn't load products. Is the backend running at {import.meta.env.VITE_API_BASE_URL}?</p>
      )}
      {status === 'ready' && (
        <div className="product-grid">
          {products.map((product) => (
            <ProductCard key={product.productId} product={product} />
          ))}
        </div>
      )}
    </div>
  )
}

export default Products

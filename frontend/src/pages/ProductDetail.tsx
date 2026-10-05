import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { fetchProduct } from '../lib/api'
import type { Product } from '../types/product'

function ProductDetail() {
  const { productId } = useParams<{ productId: string }>()
  const [product, setProduct] = useState<Product | null>(null)
  const [status, setStatus] = useState<'loading' | 'error' | 'ready'>('loading')

  useEffect(() => {
    if (!productId) return
    let cancelled = false
    setStatus('loading')
    fetchProduct(productId)
      .then((data) => {
        if (!cancelled) {
          setProduct(data)
          setStatus('ready')
        }
      })
      .catch(() => {
        if (!cancelled) setStatus('error')
      })
    return () => {
      cancelled = true
    }
  }, [productId])

  if (status === 'loading') {
    return (
      <div className="page product-detail-page">
        <p>Loading product…</p>
      </div>
    )
  }

  if (status === 'error' || !product) {
    return (
      <div className="page product-detail-page">
        <h1>Product not found</h1>
        <Link to="/products" className="btn btn-secondary">
          Back to Products
        </Link>
      </div>
    )
  }

  const totalStock = product.sizes.reduce((sum, s) => sum + s.quantity, 0)

  return (
    <div className="page product-detail-page">
      <Link to="/products" className="back-link">
        ← Back to Products
      </Link>
      <div className="product-detail">
        <div className="product-detail-image">
          <img src={product.image} alt={product.name} />
        </div>
        <div className="product-detail-info">
          <p className="eyebrow">{product.garmentType}</p>
          <h1>{product.name}</h1>
          <p className="product-detail-price">${product.price.toFixed(2)}</p>
          <p className="product-detail-description">{product.description}</p>

          <div className="product-detail-section">
            <h3>Colors</h3>
            <div className="chip-row">
              {product.colors.map((color) => (
                <span key={color} className="chip">
                  {color}
                </span>
              ))}
            </div>
          </div>

          <div className="product-detail-section">
            <h3>Sizes &amp; Availability</h3>
            {totalStock > 0 ? (
              <div className="size-grid">
                {product.sizes.map((s) => (
                  <div
                    key={s.size}
                    className={s.quantity > 0 ? 'size-option' : 'size-option out-of-stock'}
                  >
                    <span className="size-label">{s.size}</span>
                    <span className="size-stock">
                      {s.quantity > 0 ? `${s.quantity} in stock` : 'Out of stock'}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <p>Currently out of stock in all sizes.</p>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default ProductDetail

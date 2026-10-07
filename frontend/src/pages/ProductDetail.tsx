import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { fetchProduct } from '../lib/api'
import { useViewingProduct } from '../context/ViewingProductContext'
import type { Product } from '../types/product'

// The database only tracks stock per SIZE, never per color — a product's
// colors share one combined quantity per size (see output/harness.md's
// "Known open gaps"). There's no real per-color number to look up, so this
// deterministically splits the one real total across a product's listed
// colors instead of inventing new figures: every color's share always sums
// back to the exact real total for that size (any remainder from an uneven
// split goes to the first colors in the list, so nothing is gained or lost).
function colorShareOfSize(totalQuantity: number, colorCount: number, colorIndex: number): number {
  const base = Math.floor(totalQuantity / colorCount)
  const remainder = totalQuantity % colorCount
  return colorIndex < remainder ? base + 1 : base
}

function ProductDetail() {
  const { productId } = useParams<{ productId: string }>()
  const [product, setProduct] = useState<Product | null>(null)
  const [status, setStatus] = useState<'loading' | 'error' | 'ready'>('loading')
  const [selectedColor, setSelectedColor] = useState<string | null>(null)
  const { setViewingProduct } = useViewingProduct()

  useEffect(() => {
    if (!productId) return
    let cancelled = false
    setStatus('loading')
    setSelectedColor(null)
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

  // Tells the chat widget which product the shopper is looking at, so a
  // vague "do you have this in pink" can resolve without re-naming it.
  // Cleared on unmount so the chat doesn't keep treating a page the shopper
  // has since navigated away from as the one they're asking about.
  useEffect(() => {
    if (product) {
      setViewingProduct({ productId: product.productId })
    }
    return () => setViewingProduct(null)
  }, [product, setViewingProduct])

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

  const selectedColorIndex = selectedColor ? product.colors.indexOf(selectedColor) : -1
  const displaySizes =
    selectedColorIndex === -1
      ? product.sizes
      : product.sizes.map((s) => ({
          size: s.size,
          quantity: colorShareOfSize(s.quantity, product.colors.length, selectedColorIndex),
        }))
  const totalStock = displaySizes.reduce((sum, s) => sum + s.quantity, 0)

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

          {product.colors.length > 0 && (
            <div className="product-detail-section">
              <h3>Colors</h3>
              <div className="chip-row">
                {product.colors.map((color) => (
                  <button
                    key={color}
                    type="button"
                    className={color === selectedColor ? 'chip chip-active' : 'chip'}
                    onClick={() => setSelectedColor((current) => (current === color ? null : color))}
                    aria-pressed={color === selectedColor}
                  >
                    {color}
                  </button>
                ))}
              </div>
            </div>
          )}

          <div className="product-detail-section">
            <h3>
              Sizes &amp; Availability
              {selectedColor && <span className="text-capitalize"> — {selectedColor}</span>}
            </h3>
            {selectedColor && (
              <p className="size-grid-note">
                Estimated for this color — the database tracks total stock per size, not a separate
                count per color.
              </p>
            )}
            {totalStock > 0 ? (
              <div className="size-grid">
                {displaySizes.map((s) => (
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
              <p>
                {selectedColor
                  ? `Currently out of stock in ${selectedColor} for all sizes.`
                  : 'Currently out of stock in all sizes.'}
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default ProductDetail

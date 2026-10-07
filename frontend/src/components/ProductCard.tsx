import { Link } from 'react-router-dom'
import type { Product } from '../types/product'

// Total-stock-based badge for the grid — separate from the chat's per-size
// urgency wording (backend/prompts/prompt.md's "Low-stock urgency" section),
// since the grid doesn't know which size a shopper wants yet. Threshold is
// deliberately higher (10 total across all sizes) than the chat's per-size
// threshold (3), since "10 units left across 6 sizes" is a meaningfully
// different signal from "10 units left in the one size you asked about."
const LOW_STOCK_TOTAL_THRESHOLD = 10

function stockBadge(product: Product): { label: string; className: string } | null {
  const total = product.sizes.reduce((sum, s) => sum + s.quantity, 0)
  if (total === 0) return { label: 'Out of stock', className: 'stock-badge out-of-stock' }
  if (total <= LOW_STOCK_TOTAL_THRESHOLD) return { label: `Only ${total} left`, className: 'stock-badge low-stock' }
  return null
}

function ProductCard({ product }: { product: Product }) {
  const badge = stockBadge(product)

  return (
    <Link to={`/products/${product.productId}`} className="product-card">
      <div className="product-card-image">
        <img src={product.image} alt={product.name} loading="lazy" />
        {badge && <span className={badge.className}>{badge.label}</span>}
      </div>
      <div className="product-card-body">
        <h3>{product.name}</h3>
        <p className="product-card-description">{product.description}</p>
        <p className="product-card-price">${product.price.toFixed(2)}</p>
      </div>
    </Link>
  )
}

export default ProductCard

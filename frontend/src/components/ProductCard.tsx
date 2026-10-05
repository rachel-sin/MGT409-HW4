import { Link } from 'react-router-dom'
import type { Product } from '../types/product'

function ProductCard({ product }: { product: Product }) {
  return (
    <Link to={`/products/${product.productId}`} className="product-card">
      <div className="product-card-image">
        <img src={product.image} alt={product.name} loading="lazy" />
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

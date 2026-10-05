import type { Product, ProductSize } from '../types/product'

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL

interface ApiProduct {
  product_id: string
  name: string
  garment_type: string
  description: string
  colors: string[]
  search_tags: string[]
  image: string
  price: number
  sizes: ProductSize[]
}

function toProduct(p: ApiProduct): Product {
  return {
    productId: p.product_id,
    name: p.name,
    garmentType: p.garment_type,
    description: p.description,
    colors: p.colors,
    searchTags: p.search_tags,
    image: `${API_BASE_URL}${p.image}`,
    price: p.price,
    sizes: p.sizes,
  }
}

export async function fetchProducts(): Promise<Product[]> {
  const res = await fetch(`${API_BASE_URL}/api/products`)
  if (!res.ok) throw new Error('Failed to load products')
  const data: ApiProduct[] = await res.json()
  return data.map(toProduct)
}

export async function fetchProduct(productId: string): Promise<Product | null> {
  const res = await fetch(`${API_BASE_URL}/api/products/${productId}`)
  if (res.status === 404) return null
  if (!res.ok) throw new Error('Failed to load product')
  const data: ApiProduct = await res.json()
  return toProduct(data)
}

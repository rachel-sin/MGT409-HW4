export interface ProductSize {
  size: string
  quantity: number
}

export interface Product {
  productId: string
  name: string
  garmentType: string
  description: string
  colors: string[]
  searchTags: string[]
  image: string
  price: number
  sizes: ProductSize[]
}

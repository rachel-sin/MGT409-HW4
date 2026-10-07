import type { Product, ProductSize } from '../types/product'
import type { AuthUser } from '../types/user'

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

interface ApiAuthUser {
  id: number
  first_name: string
  last_name: string
  email: string
  session_token: string
}

interface ApiError {
  detail?: string
}

function toAuthUser(u: ApiAuthUser): AuthUser {
  return {
    id: u.id,
    firstName: u.first_name,
    lastName: u.last_name,
    email: u.email,
    sessionToken: u.session_token,
  }
}

async function readErrorDetail(res: Response, fallback: string): Promise<string> {
  const body: ApiError = await res.json().catch(() => ({}))
  return body.detail ?? fallback
}

export async function signup(input: {
  firstName: string
  lastName: string
  email: string
  password: string
  confirmPassword: string
}): Promise<AuthUser> {
  const res = await fetch(`${API_BASE_URL}/api/auth/signup`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      first_name: input.firstName,
      last_name: input.lastName,
      email: input.email,
      password: input.password,
      confirm_password: input.confirmPassword,
    }),
  })
  if (!res.ok) throw new Error(await readErrorDetail(res, 'Could not create account'))
  const data: ApiAuthUser = await res.json()
  return toAuthUser(data)
}

export async function login(input: { email: string; password: string }): Promise<AuthUser> {
  const res = await fetch(`${API_BASE_URL}/api/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email: input.email, password: input.password }),
  })
  if (!res.ok) throw new Error(await readErrorDetail(res, 'Could not log in'))
  const data: ApiAuthUser = await res.json()
  return toAuthUser(data)
}

export async function logout(token: string): Promise<void> {
  // Best-effort: the frontend clears its own local state regardless, so a
  // failed request here (e.g. offline) shouldn't block logging out locally.
  await fetch(`${API_BASE_URL}/api/auth/logout`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
  }).catch(() => {})
}

export interface ChatResult {
  message: string
  products: Product[]
}

export interface PageContext {
  page: 'home' | 'products' | 'product_detail' | 'about' | 'login' | 'create_account' | 'unknown'
  productId?: string
}

export async function sendChatMessage(input: {
  token: string | null
  message: string
  pageContext?: PageContext
}): Promise<ChatResult> {
  const res = await fetch(`${API_BASE_URL}/api/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(input.token ? { Authorization: `Bearer ${input.token}` } : {}),
    },
    body: JSON.stringify({
      message: input.message,
      page_context: input.pageContext
        ? { page: input.pageContext.page, product_id: input.pageContext.productId ?? null }
        : null,
    }),
  })
  if (!res.ok) throw new Error(await readErrorDetail(res, 'Chat request failed'))
  const data: { message: string; products: ApiProduct[] } = await res.json()
  return { message: data.message, products: data.products.map(toProduct) }
}

export interface ChatHistoryMessage {
  role: 'user' | 'assistant'
  content: string
  products: Product[]
}

export async function fetchChatHistory(token: string): Promise<ChatHistoryMessage[]> {
  const res = await fetch(`${API_BASE_URL}/api/chat/history`, {
    headers: { Authorization: `Bearer ${token}` },
  })
  if (res.status === 401) return []
  if (!res.ok) throw new Error('Failed to load chat history')
  const data: { messages: { role: string; content: string; products: ApiProduct[] }[] } = await res.json()
  return data.messages.map((m) => ({
    role: m.role === 'user' ? 'user' : 'assistant',
    content: m.content,
    products: m.products.map(toProduct),
  }))
}

export async function clearChatHistory(token: string): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/api/chat/history`, {
    method: 'DELETE',
    headers: { Authorization: `Bearer ${token}` },
  })
  if (!res.ok) throw new Error('Failed to clear chat history')
}

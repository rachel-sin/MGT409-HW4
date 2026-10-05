import { Route, Routes } from 'react-router-dom'
import Navbar from './components/Navbar'
import ChatWidget from './components/ChatWidget'
import Home from './pages/Home'
import Products from './pages/Products'
import ProductDetail from './pages/ProductDetail'
import AboutUs from './pages/AboutUs'
import Login from './pages/Login'
import CreateAccount from './pages/CreateAccount'

function App() {
  return (
    <div className="app-shell">
      <Navbar />
      <main className="page-content">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/products" element={<Products />} />
          <Route path="/products/:productId" element={<ProductDetail />} />
          <Route path="/about" element={<AboutUs />} />
          <Route path="/login" element={<Login />} />
          <Route path="/create-account" element={<CreateAccount />} />
        </Routes>
      </main>
      <ChatWidget />
    </div>
  )
}

export default App

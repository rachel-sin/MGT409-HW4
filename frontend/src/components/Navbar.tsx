import { NavLink, useNavigate } from 'react-router-dom'
import { logout as logoutRequest } from '../lib/api'
import { useAuth } from '../context/AuthContext'

const navLinks = [
  { to: '/', label: 'Home' },
  { to: '/products', label: 'Products' },
  { to: '/about', label: 'About Us' },
]

const authLinks = [
  { to: '/login', label: 'Log In' },
  { to: '/create-account', label: 'Create Account' },
]

function Navbar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  async function handleLogout() {
    if (user) {
      await logoutRequest(user.sessionToken)
    }
    logout()
    navigate('/')
  }

  return (
    <header className="navbar">
      <NavLink to="/" className="brand">
        Campus Customs
      </NavLink>
      <nav className="nav-links">
        {navLinks.map((link) => (
          <NavLink
            key={link.to}
            to={link.to}
            className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}
            end={link.to === '/'}
          >
            {link.label}
          </NavLink>
        ))}
      </nav>
      <div className="auth-links">
        {user ? (
          <>
            <span className="nav-greeting">Hi, {user.firstName}</span>
            <button type="button" className="nav-link auth" onClick={handleLogout}>
              Log Out
            </button>
          </>
        ) : (
          authLinks.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              className={({ isActive }) =>
                isActive ? 'nav-link auth active' : 'nav-link auth'
              }
            >
              {link.label}
            </NavLink>
          ))
        )}
      </div>
    </header>
  )
}

export default Navbar

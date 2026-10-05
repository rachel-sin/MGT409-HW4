import { NavLink } from 'react-router-dom'

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
        {authLinks.map((link) => (
          <NavLink
            key={link.to}
            to={link.to}
            className={({ isActive }) =>
              isActive ? 'nav-link auth active' : 'nav-link auth'
            }
          >
            {link.label}
          </NavLink>
        ))}
      </div>
    </header>
  )
}

export default Navbar

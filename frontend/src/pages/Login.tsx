function Login() {
  return (
    <div className="page auth-page">
      <h1>Log In</h1>
      <form className="auth-form">
        <label>
          Email
          <input type="email" name="email" autoComplete="email" />
        </label>
        <label>
          Password
          <input type="password" name="password" autoComplete="current-password" />
        </label>
        <button type="submit" className="btn btn-primary">
          Log In
        </button>
      </form>
    </div>
  )
}

export default Login

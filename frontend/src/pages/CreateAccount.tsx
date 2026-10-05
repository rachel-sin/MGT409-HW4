function CreateAccount() {
  return (
    <div className="page auth-page">
      <h1>Create Account</h1>
      <form className="auth-form">
        <label>
          First Name
          <input type="text" name="firstName" autoComplete="given-name" />
        </label>
        <label>
          Last Name
          <input type="text" name="lastName" autoComplete="family-name" />
        </label>
        <label>
          Email
          <input type="email" name="email" autoComplete="email" />
        </label>
        <label>
          Password
          <input type="password" name="password" autoComplete="new-password" />
        </label>
        <button type="submit" className="btn btn-primary">
          Create Account
        </button>
      </form>
    </div>
  )
}

export default CreateAccount

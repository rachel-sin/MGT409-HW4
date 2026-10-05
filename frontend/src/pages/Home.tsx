import { Link } from 'react-router-dom'

function Home() {
  return (
    <div className="page home-page">
      <section className="hero-section">
        <p className="eyebrow">Campus Customs</p>
        <h1>Bulldog gear, made for the way you actually wear it.</h1>
        <p className="lede">
          From first-years to graduates fifty years out, Campus Customs
          designs apparel and accessories that carry your Yale story —
          residential college pride, class year milestones, game day
          traditions, and everyday campus life.
        </p>
        <div className="hero-actions">
          <Link to="/products" className="btn btn-primary">
            Shop the Collection
          </Link>
          <Link to="/about" className="btn btn-secondary">
            Our Story
          </Link>
        </div>
      </section>

      <section className="highlights">
        <div className="highlight-card">
          <h3>Designed on Campus</h3>
          <p>
            Every print starts with input from current students, so the
            designs actually reflect how Yale looks and feels today.
          </p>
        </div>
        <div className="highlight-card">
          <h3>For the Whole Bulldog Family</h3>
          <p>
            Students, alumni, parents, and relatives — if you've got a
            connection to Yale, there's something here that fits.
          </p>
        </div>
        <div className="highlight-card">
          <h3>Need Help Finding Something?</h3>
          <p>
            Our shopping assistant can help you track down the right size,
            color, or style in seconds — just ask.
          </p>
        </div>
      </section>
    </div>
  )
}

export default Home

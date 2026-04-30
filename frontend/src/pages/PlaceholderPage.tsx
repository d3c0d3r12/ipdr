import { Link } from 'react-router-dom'

export default function PlaceholderPage({ title }: { title: string }) {
  return (
    <section>
      <h1>{title}</h1>
      <div className="card">
        <p>
          This module has been moved to the new React shell and is ready for endpoint wiring.
          Core workflows (auth, dashboard, upload, lookup, records, analytics, FIR details) are active.
        </p>
        <p>
          Continue from <Link to="/dashboard">Dashboard</Link>.
        </p>
      </div>
    </section>
  )
}

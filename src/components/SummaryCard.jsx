export function SummaryCard({ label, value, change }) {
  const changeClass = change.startsWith('+') ? 'positive' : 'negative'

  return (
    <article className="summary-card">
      <p className="summary-label">{label}</p>
      <p className="summary-value">{value}</p>
      <p className={`summary-change ${changeClass}`}>전주 대비 {change}</p>
    </article>
  )
}

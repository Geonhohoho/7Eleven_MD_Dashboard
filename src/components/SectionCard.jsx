export function SectionCard({ title, caption, children }) {
  return (
    <section className="section-card">
      <div className="section-head">
        <h2 className="section-title">{title}</h2>
        <p className="section-caption">{caption}</p>
      </div>
      <div className="section-body">{children}</div>
    </section>
  )
}

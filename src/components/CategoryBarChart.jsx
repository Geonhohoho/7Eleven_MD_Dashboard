export function CategoryBarChart({ data }) {
  const maxValue = Math.max(...data.map((item) => item.value))

  return (
    <div className="bar-list">
      {data.map((item) => (
        <div className="bar-row" key={item.name}>
          <span className="bar-label">{item.name}</span>
          <div className="bar-track">
            <div className="bar-fill" style={{ width: `${(item.value / maxValue) * 100}%` }} />
          </div>
          <span className="bar-value">{item.value}</span>
        </div>
      ))}
    </div>
  )
}

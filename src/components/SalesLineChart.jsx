function toPath(data, width, height, padding) {
  const values = data.map((d) => d.value)
  const min = Math.min(...values)
  const max = Math.max(...values)
  const stepX = (width - padding * 2) / (data.length - 1)
  const scaleY = (height - padding * 2) / (max - min || 1)

  return data
    .map((point, index) => {
      const x = padding + stepX * index
      const y = height - padding - (point.value - min) * scaleY
      return `${index === 0 ? 'M' : 'L'} ${x} ${y}`
    })
    .join(' ')
}

export function SalesLineChart({ data }) {
  const width = 640
  const height = 280
  const padding = 28
  const path = toPath(data, width, height, padding)

  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="line-chart" role="img" aria-label="일자별 발주 추이 차트">
      <line x1={padding} y1={height - padding} x2={width - padding} y2={height - padding} stroke="#cbd5e1" />
      <path d={path} fill="none" stroke="#4f46e5" strokeWidth="3" strokeLinejoin="round" strokeLinecap="round" />
      {data.map((point, index) => {
        const x = padding + ((width - padding * 2) / (data.length - 1)) * index
        const values = data.map((d) => d.value)
        const min = Math.min(...values)
        const max = Math.max(...values)
        const y = height - padding - ((point.value - min) / (max - min || 1)) * (height - padding * 2)
        return (
          <g key={point.date}>
            <circle cx={x} cy={y} r="4" fill="#4f46e5" />
            <text x={x} y={height - 8} textAnchor="middle" className="chart-axis-label">
              {point.date}
            </text>
          </g>
        )
      })}
    </svg>
  )
}

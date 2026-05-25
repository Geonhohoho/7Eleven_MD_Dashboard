function formatNumber(value) {
  return value.toLocaleString('ko-KR')
}

export function OrderTable({ rows }) {
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>센터</th>
            <th>상품명</th>
            <th>예상 수요량</th>
            <th>권장 발주량</th>
            <th>리스크</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr key={`${row.center}-${index}`}>
              <td>{row.center}</td>
              <td>{row.item}</td>
              <td>{formatNumber(row.demand)}</td>
              <td>{formatNumber(row.recommend)}</td>
              <td>{row.risk}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

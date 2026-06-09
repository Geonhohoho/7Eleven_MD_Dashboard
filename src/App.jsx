import './App.css'
import { Fragment, useEffect, useMemo, useState } from 'react'

const outflowBand = (n) => {
  if (n < 50) return 'over'
  if (n <= 100) return 'normal'
  return 'shortage'
}
const pctColor = (n) => {
  const band = outflowBand(n)
  if (band === 'over') return 'red'
  if (band === 'normal') return 'green'
  return 'amber'
}

function App() {
  const [activeTab, setActiveTab] = useState('금주+MD')
  const [data, setData] = useState(null)
  const [qtyMap, setQtyMap] = useState({})
  const [centerQtyMap, setCenterQtyMap] = useState({})
  const [centerWeightMap, setCenterWeightMap] = useState({})
  const [confirmedMap, setConfirmedMap] = useState({})
  const [selectedItemCode, setSelectedItemCode] = useState('')
  const [currentDate, setCurrentDate] = useState('')
  const [similarOpenMap, setSimilarOpenMap] = useState({})
  const [pastCategory, setPastCategory] = useState('전체')
  const [pastCategoryMid, setPastCategoryMid] = useState('전체')
  const [pastCategorySub, setPastCategorySub] = useState('전체')
  const [pastSort, setPastSort] = useState('latest')
  const [pastDateFrom, setPastDateFrom] = useState('')
  const [pastDateTo, setPastDateTo] = useState('')
  const [pastQuery, setPastQuery] = useState('')
  const [pastExpandedKey, setPastExpandedKey] = useState('')

  useEffect(() => {
    fetch('/data/dashboard-data.json')
      .then((res) => res.json())
      .then((json) => {
        setData(json)
        const initRows = json.allRows || []
        setCurrentDate('2025-12-23')
        setQtyMap(
          Object.fromEntries(
            initRows.map((r) => {
              const ldu = Math.max(Number(r.lduEa || 1), 1)
              const recoEa = Number(r.mlRecommendQty || r.recommendQty || r.inputQty || 0)
              return [r.rowKey, String(Math.round(recoEa / ldu))]
            }),
          ),
        )
      })
  }, [])

  const reservationDates = [
    ...new Set(
      Object.values(data?.itemDetails || {})
        .flatMap((d) => d.reservation4d?.map((p) => p.date) || [])
        .filter(Boolean),
    ),
  ].sort()
  const minDate = reservationDates[0] || ''
  const maxDate = reservationDates[reservationDates.length - 1] || ''
  const selectedBaseDate = currentDate || minDate || (data?.latestReleaseDate || '')
  const baseRows = data?.allRows ?? []
  const deadlineDates = baseRows.map((r) => r.deadlineDate).filter(Boolean).sort()
  const minDeadlineDate = deadlineDates[0] || ''
  const maxDeadlineDate = deadlineDates[deadlineDates.length - 1] || ''
  const weeklyRows = baseRows.filter((r) => {
    const detail = data?.itemDetails?.[r.rowKey]
    const reservation4d = detail?.reservation4d || []
    const hasFull4Days =
      reservation4d.length === 4 &&
      reservation4d.every((p) => p.qty > 0)
    const isDeadlineDay = (r.deadlineDate || '') === selectedBaseDate
    return hasFull4Days && isDeadlineDay
  })
  const pastRows = data?.pastRows ?? []
  const pastRowsWithKey = useMemo(
    () => pastRows.map((r) => ({ ...r, rowKey: `${r.releaseDate}_${r.itemCode}_${r.itemName}` })),
    [pastRows],
  )
  const pastCategoryOptions = useMemo(
    () => ['전체', ...Array.from(new Set(pastRowsWithKey.map((r) => r.category).filter(Boolean))).sort()],
    [pastRowsWithKey],
  )
  const pastCategoryMidOptions = useMemo(() => {
    const rows = pastRowsWithKey.filter((r) => pastCategory === '전체' || r.category === pastCategory)
    return ['전체', ...Array.from(new Set(rows.map((r) => r.categoryMid).filter(Boolean))).sort()]
  }, [pastRowsWithKey, pastCategory])
  const pastCategorySubOptions = useMemo(() => {
    const rows = pastRowsWithKey
      .filter((r) => pastCategory === '전체' || r.category === pastCategory)
      .filter((r) => pastCategoryMid === '전체' || r.categoryMid === pastCategoryMid)
    return ['전체', ...Array.from(new Set(rows.map((r) => r.categorySub).filter(Boolean))).sort()]
  }, [pastRowsWithKey, pastCategory, pastCategoryMid])
  const filteredPastRows = useMemo(() => {
    const rows = pastRowsWithKey
      .filter((r) => pastCategory === '전체' || r.category === pastCategory)
      .filter((r) => pastCategoryMid === '전체' || r.categoryMid === pastCategoryMid)
      .filter((r) => pastCategorySub === '전체' || r.categorySub === pastCategorySub)
      .filter((r) => !pastDateFrom || (r.releaseDate || '') >= pastDateFrom)
      .filter((r) => !pastDateTo || (r.releaseDate || '') <= pastDateTo)
      .filter((r) => {
        const q = pastQuery.trim().toLowerCase()
        if (!q) return true
        return (
          String(r.itemName || '').toLowerCase().includes(q) ||
          String(r.itemCode || '').toLowerCase().includes(q)
        )
      })
    const sorted = [...rows]
    if (pastSort === 'high_rate') sorted.sort((a, b) => Number(b.salesRate) - Number(a.salesRate))
    else if (pastSort === 'low_rate') sorted.sort((a, b) => Number(a.salesRate) - Number(b.salesRate))
    else if (pastSort === 'high_qty') sorted.sort((a, b) => Number(b.actualOrderQty) - Number(a.actualOrderQty))
    else sorted.sort((a, b) => (b.releaseDate || '').localeCompare(a.releaseDate || ''))
    return sorted
  }, [pastRowsWithKey, pastCategory, pastCategoryMid, pastCategorySub, pastDateFrom, pastDateTo, pastSort, pastQuery])

  useEffect(() => {
    const cats = pastCategoryOptions
    const mids = pastCategoryMidOptions
    const subs = pastCategorySubOptions
    if (!cats.includes(pastCategory)) setPastCategory('전체')
    if (!mids.includes(pastCategoryMid)) setPastCategoryMid('전체')
    if (!subs.includes(pastCategorySub)) setPastCategorySub('전체')
  }, [pastCategoryOptions, pastCategoryMidOptions, pastCategorySubOptions, pastCategory, pastCategoryMid, pastCategorySub])

  const filteredRows = useMemo(() => weeklyRows, [weeklyRows])

  useEffect(() => {
    if (!filteredRows.length) {
      setSelectedItemCode('')
      return
    }
    setQtyMap((prev) => {
      const next = { ...prev }
      for (const r of filteredRows) {
        if (next[r.rowKey] === undefined) {
          const ldu = Math.max(Number(r.lduEa || 1), 1)
          const recoEa = Number(r.mlRecommendQty || r.recommendQty || r.inputQty || 0)
          next[r.rowKey] = String(Math.round(recoEa / ldu))
        }
      }
      return next
    })
    if (selectedItemCode && !filteredRows.find((r) => r.rowKey === selectedItemCode)) {
      setSelectedItemCode('')
    }
  }, [filteredRows, selectedItemCode])

  const confirmedCount = Object.values(confirmedMap).filter(Boolean).length
  const newItemCount = new Set(weeklyRows.map((r) => r.itemCode)).size
  const avgSalesRate = weeklyRows.length
    ? (weeklyRows.reduce((acc, r) => acc + r.salesRate, 0) / weeklyRows.length).toFixed(1)
    : '0.0'
  const selectedDetail = data?.itemDetails?.[selectedItemCode]

  const buildLinePath = (points, width, height, pad, bounds = null) => {
    const max = bounds?.max ?? Math.max(...points.map((p) => p.qty), 1)
    const min = bounds?.min ?? Math.min(...points.map((p) => p.qty), 0)
    const range = Math.max(max - min, 1)
    const stepX = (width - pad * 2) / Math.max(points.length - 1, 1)
    return points
      .map((p, idx) => {
        const x = pad + stepX * idx
        const y = height - pad - ((p.qty - min) / range) * (height - pad * 2)
        return `${idx === 0 ? 'M' : 'L'} ${x} ${y}`
      })
      .join(' ')
  }
  const pointXY = (point, idx, points, width, height, pad, bounds = null) => {
    const max = bounds?.max ?? Math.max(...points.map((p) => p.qty), 1)
    const min = bounds?.min ?? Math.min(...points.map((p) => p.qty), 0)
    const range = Math.max(max - min, 1)
    const stepX = (width - pad * 2) / Math.max(points.length - 1, 1)
    const x = pad + stepX * idx
    const y = height - pad - ((point.qty - min) / range) * (height - pad * 2)
    return { x, y }
  }
  const buildAreaPath = (points, width, height, pad, bounds = null) => {
    if (!points.length) return ''
    const max = bounds?.max ?? Math.max(...points.map((p) => p.qty), 1)
    const min = bounds?.min ?? Math.min(...points.map((p) => p.qty), 0)
    const range = Math.max(max - min, 1)
    const stepX = (width - pad * 2) / Math.max(points.length - 1, 1)
    const toXY = (p, idx) => {
      const x = pad + stepX * idx
      const y = height - pad - ((p.qty - min) / range) * (height - pad * 2)
      return [x, y]
    }
    const first = toXY(points[0], 0)
    const last = toXY(points[points.length - 1], points.length - 1)
    const line = points
      .map((p, idx) => {
        const [x, y] = toXY(p, idx)
        return `${idx === 0 ? 'M' : 'L'} ${x} ${y}`
      })
      .join(' ')
    return `${line} L ${last[0]} ${height - pad} L ${first[0]} ${height - pad} Z`
  }
  const formatMd = (dateText) => {
    if (!dateText) return ''
    const parts = String(dateText).split('-')
    if (parts.length < 3) return dateText
    return `${parts[1]}/${parts[2]}`
  }
  const toEaFromBox = (boxQty, lduEa) => Math.round(Number(boxQty || 0) * Math.max(Number(lduEa || 1), 1))
  const mlRecommendEa = (row) => Number(row.mlRecommendQty || row.recommendQty || 0)
  const mlRecommendBox = (row) => Math.round(mlRecommendEa(row) / Math.max(Number(row.lduEa || 1), 1))
  const predictedOutflowEa = (row) => Number(row.predictedOutflow7d || 0)
  const currentInputEa = (row) => toEaFromBox(qtyMap[row.rowKey], row.lduEa)
  const currentInputBox = (row) => Number(qtyMap[row.rowKey] || 0)
  const qtyDeltaTone = (row) => {
    const input = currentInputBox(row)
    const reco = mlRecommendBox(row)
    if (reco <= 0) return ''
    const ratio = input / reco
    if (ratio > 1.1) return 'high'
    if (ratio < 0.9) return 'low'
    return 'ok'
  }
  const currentOutflowRate = (row) => {
    const recoEa = Math.max(mlRecommendEa(row), 1)
    const input = Math.max(currentInputEa(row), 1)
    return Math.max(0, Math.round((recoEa / input) * 1000) / 10)
  }
  const riskItemCount = filteredRows.filter((r) => {
    const rate = currentOutflowRate(r)
    return rate < 50 || rate > 100
  }).length
  const adjustedCenterDistribution = (row) => {
    const detail = data?.itemDetails?.[row.rowKey]
    const centers = detail?.centerDistribution || []
    if (!centers.length) return []

    const targetEa = Math.max(currentInputEa(row), 0)
    const baseTotalEa = centers.reduce((acc, c) => acc + Number(c.qty || 0), 0)
    if (targetEa <= 0 || baseTotalEa <= 0) {
      return centers.map((c) => ({ centerName: c.centerName, qty: 0 }))
    }

    const scaled = centers.map((c) => {
      const raw = (Number(c.qty || 0) / baseTotalEa) * targetEa
      const floor = Math.floor(raw)
      return { centerName: c.centerName, floor, frac: raw - floor }
    })
    let remain = targetEa - scaled.reduce((acc, c) => acc + c.floor, 0)
    scaled.sort((a, b) => b.frac - a.frac)
    for (let i = 0; i < scaled.length && remain > 0; i += 1, remain -= 1) scaled[i].floor += 1
    return scaled
      .sort((a, b) => a.centerName.localeCompare(b.centerName, 'ko'))
      .map((c) => ({ centerName: c.centerName, qty: c.floor }))
  }
  const defaultCenterWeights = (row) => {
    const detail = data?.itemDetails?.[row.rowKey]
    const centers = detail?.centerDistribution || []
    return Object.fromEntries(centers.map((c) => [c.centerName, Number(c.centerWeight || 1)]))
  }
  const weightedCentersByBox = (row) => {
    const detail = data?.itemDetails?.[row.rowKey]
    const centers = detail?.centerDistribution || []
    const targetBox = Math.max(currentInputBox(row), 0)
    if (!centers.length) return []
    const weights = centerWeightMap[row.rowKey] || defaultCenterWeights(row)
    const indexed = centers.map((c) => {
      const storeShare = Number(c.storeShare || 0)
      const w = Math.max(Number(weights[c.centerName] || 0), 0)
      return { ...c, index: storeShare * w }
    })
    const indexSum = indexed.reduce((acc, c) => acc + c.index, 0)
    if (indexSum <= 0) return centers.map((c) => ({ centerName: c.centerName, qty: 0 }))

    const scaled = indexed.map((c) => {
      const raw = (c.index / indexSum) * targetBox
      const floor = Math.floor(raw)
      return { centerName: c.centerName, floor, frac: raw - floor }
    })
    let remain = targetBox - scaled.reduce((acc, c) => acc + c.floor, 0)
    scaled.sort((a, b) => b.frac - a.frac)
    for (let i = 0; i < scaled.length && remain > 0; i += 1, remain -= 1) scaled[i].floor += 1
    return scaled
      .sort((a, b) => a.centerName.localeCompare(b.centerName, 'ko'))
      .map((c) => ({ centerName: c.centerName, qty: c.floor }))
  }
  const recommendedCentersByBox = (row) => {
    const detail = data?.itemDetails?.[row.rowKey]
    const centers = detail?.centerDistribution || []
    const targetBox = Math.max(mlRecommendBox(row), 0)
    if (!centers.length) return []
    const weights = centerWeightMap[row.rowKey] || defaultCenterWeights(row)
    const indexed = centers.map((c) => {
      const storeShare = Number(c.storeShare || 0)
      const w = Math.max(Number(weights[c.centerName] || 0), 0)
      return { ...c, index: storeShare * w }
    })
    const indexSum = indexed.reduce((acc, c) => acc + c.index, 0)
    if (indexSum <= 0) return centers.map((c) => ({ centerName: c.centerName, qty: 0 }))

    const scaled = indexed.map((c) => {
      const raw = (c.index / indexSum) * targetBox
      const floor = Math.floor(raw)
      return { centerName: c.centerName, floor, frac: raw - floor }
    })
    let remain = targetBox - scaled.reduce((acc, c) => acc + c.floor, 0)
    scaled.sort((a, b) => b.frac - a.frac)
    for (let i = 0; i < scaled.length && remain > 0; i += 1, remain -= 1) scaled[i].floor += 1
    return scaled
      .sort((a, b) => a.centerName.localeCompare(b.centerName, 'ko'))
      .map((c) => ({ centerName: c.centerName, qty: c.floor }))
  }
  const baseCenterBoxMap = (row) =>
    Object.fromEntries(
      recommendedCentersByBox(row).map((c) => [
        c.centerName,
        Number(c.qty || 0),
      ]),
    )

  const centerTone = (row, centerName, currentBox) => {
    const baseBox = Number(baseCenterBoxMap(row)[centerName] || 0)
    if (baseBox <= 0) return ''
    const ratio = Number(currentBox || 0) / baseBox
    if (ratio > 1.1) return 'high'
    if (ratio < 0.9) return 'low'
    return 'ok'
  }
  const centersForRow = (row) => {
    const manual = centerQtyMap[row.rowKey]
    if (manual) {
      return Object.entries(manual).map(([centerName, qty]) => ({
        centerName,
        qty: Number(qty || 0),
      }))
    }
    return weightedCentersByBox(row)
  }

  if (!data) return <div className="page"><main className="container">데이터 로딩 중...</main></div>

  return (
    <div className="page">
      <header className="topbar">
        <div className="brand">
          <div className="logo">7</div>
          <div>
            <p>세븐일레븐</p>
            <h1>MD 신상품 초도발주 시스템</h1>
          </div>
        </div>
        <div className="topmeta">{data.latestReleaseDate} · 최신 배치</div>
      </header>

      <main className="container">
        <div className="tabs">
          <button className={`tab ${activeTab === '금주+MD' ? 'active' : ''}`} onClick={() => setActiveTab('금주+MD')}>금일 신상품 작업 <span>{newItemCount}</span></button>
          <button className={`tab ${activeTab === '과거' ? 'active' : ''}`} onClick={() => setActiveTab('과거')}>과거 신상품 조회</button>
        </div>

        {activeTab === '금주+MD' ? (
          <>
            <section className="date-bar">
              <label htmlFor="release-date">현재 날짜 설정</label>
              <input
                id="release-date"
                type="date"
                value={currentDate}
                min={minDate}
                max={maxDate}
                onChange={(e) => {
                  setCurrentDate(e.target.value)
                  setConfirmedMap({})
                }}
              />
              {minDeadlineDate && maxDeadlineDate && (
                <span className="date-hint">
                  조회 가능 구간: {minDeadlineDate} ~ {maxDeadlineDate}
                </span>
              )}
            </section>
            <section className="alert">
              <p className="manual-label">사용 가이드</p>
              <h3 className="manual-title">금일 신상품 작업 메뉴얼</h3>
              <p className="manual-text">오늘 마감 대상 신상품의 권장 발주량과 예상 출고율을 확인하고 발주 수량을 입력/확정할 수 있습니다.</p>
              <p className="manual-text">사용 순서: 상품 선택 → 발주 수량 입력(박스) → 센터 분배/추세선 확인 → 발주 확정</p>
            </section>
            <section className="criteria-strip">
              <span className="kpi high">과발주: 출고율 &lt; 50%</span>
              <span className="kpi ok">정상발주: 50% ~ 100%</span>
              <span className="kpi low">과소발주(결품위험): 출고율 &gt; 100%</span>
            </section>

            <section className="cards">
              <article className="card"><h3>이번 주 신규 상품 수</h3><strong>{newItemCount}개</strong><p>입고 예정 상품</p></article>
              <article className="card"><h3>검토 필요 상품 수</h3><strong>{riskItemCount}개</strong><p>출고율 50% 미만 또는 100% 초과</p></article>
              <article className="card"><h3>발주 완료</h3><strong>{confirmedCount} / {newItemCount}개</strong><p>예약주문 4일 기준 발주 마감</p></article>
            </section>

            <section className="table-wrap">
              {weeklyRows.length === 0 && (
                <div className="empty-note">선택한 날짜 기준 예약주문 데이터가 있거나 마감이 유효한 상품이 없습니다. 날짜를 조정해 주세요.</div>
              )}
              <table>
                <thead>
                  <tr>
                    <th className="col-code">상품코드</th>
                    <th className="col-name">상품명</th>
                    <th className="col-cat">카테고리</th>
                    <th className="col-price">판매가</th>
                    <th className="col-rate">예상 출고율</th>
                    <th className="col-reco">권장 발주량</th>
                    <th className="col-input">발주 수량 입력</th>
                    <th className="col-act">처리</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredRows.map((r) => (
                    <Fragment key={r.rowKey}>
                      <tr
                        className={selectedItemCode === r.rowKey ? 'row-selected' : ''}
                        onClick={() =>
                          setSelectedItemCode((prev) => (prev === r.rowKey ? '' : r.rowKey))
                        }
                      >
                        <td className="col-code code">{r.itemCode}</td>
                        <td className="col-name">{r.itemName}</td>
                        <td className="col-cat"><span className="cat">{r.category}</span></td>
                        <td className="col-price">
                          <div className="price-cell">
                            <strong className="price">₩{r.price.toLocaleString()}</strong>
                          </div>
                        </td>
                        <td className="col-rate">
                          <div className="rate-inline">
                            <span className="rate-text">{currentOutflowRate(r)}%</span>
                            <div className="rate-track">
                              <div
                                className={`rate-fill ${pctColor(currentOutflowRate(r))}`}
                                style={{ width: `${Math.min(currentOutflowRate(r), 100)}%` }}
                              />
                            </div>
                          </div>
                          <p className={`qty-warn ${outflowBand(currentOutflowRate(r)) === 'over' ? 'high' : outflowBand(currentOutflowRate(r)) === 'shortage' ? 'low' : ''}`}>
                            {outflowBand(currentOutflowRate(r)) === 'over' ? '과발주' : outflowBand(currentOutflowRate(r)) === 'shortage' ? '결품위험' : '정상'}
                          </p>
                        </td>
                        <td className="col-reco qty">{mlRecommendBox(r).toLocaleString()}박스</td>
                        <td className="col-input">
                          <input
                            className={`qty-input ${qtyDeltaTone(r)}`}
                            value={qtyMap[r.rowKey] ?? ''}
                            placeholder="박스"
                            onClick={(e) => e.stopPropagation()}
                            onChange={(e) => {
                              const next = e.target.value.replace(/[^\d]/g, '')
                              setQtyMap((prev) => ({ ...prev, [r.rowKey]: next }))
                              setCenterQtyMap((prev) => ({ ...prev, [r.rowKey]: undefined }))
                              setConfirmedMap((prev) => ({ ...prev, [r.rowKey]: false }))
                            }}
                          />
                          <p className="qty-meta">
                            {Number(qtyMap[r.rowKey] || 0).toLocaleString()}박스 / EA {toEaFromBox(qtyMap[r.rowKey], r.lduEa).toLocaleString()}
                          </p>
                          {qtyDeltaTone(r) === 'high' && <p className="qty-warn high">권장 대비 과다 발주</p>}
                          {qtyDeltaTone(r) === 'low' && <p className="qty-warn low">권장 대비 과소 발주</p>}
                        </td>
                        <td className="col-act">
                          <button
                            className={`confirm ${confirmedMap[r.rowKey] ? 'done' : ''}`}
                            onClick={(e) => {
                              e.stopPropagation()
                              setConfirmedMap((prev) => ({ ...prev, [r.rowKey]: !prev[r.rowKey] }))
                            }}
                          >
                            {confirmedMap[r.rowKey] ? '확정 완료' : '발주 확정'}
                          </button>
                        </td>
                      </tr>
                      {selectedItemCode === r.rowKey && data?.itemDetails?.[r.rowKey] && (
                        <tr className="expand-row">
                          <td colSpan={8}>
                            <div className="inline-viz-grid">
                              <article className="viz-card">
                                <h3>예약주문 4일 추세선</h3>
                                <svg className="trend-line" viewBox="0 0 560 210" role="img" aria-label="4일 예약 주문 추세선">
                                  <path d={buildLinePath(data.itemDetails[r.rowKey].reservation4d, 560, 210, 24)} fill="none" stroke="#0c7a43" strokeWidth="3" />
                                  {data.itemDetails[r.rowKey].reservation4d.map((p, idx) => {
                                    const pts = data.itemDetails[r.rowKey].reservation4d
                                    const max = Math.max(...pts.map((x) => x.qty), 1)
                                    const min = Math.min(...pts.map((x) => x.qty), 0)
                                    const range = Math.max(max - min, 1)
                                    const stepX = (560 - 48) / Math.max(pts.length - 1, 1)
                                    const x = 24 + stepX * idx
                                    const y = 210 - 24 - ((p.qty - min) / range) * (210 - 48)
                                    return <circle key={p.date} cx={x} cy={y} r="4" fill="#0c7a43" />
                                  })}
                                </svg>
                                <div className="day-rows">
                                  {data.itemDetails[r.rowKey].reservation4d.map((p) => (
                                    <div key={p.date} className="day-row"><span>{p.date}</span><strong>{p.qty.toLocaleString()}</strong></div>
                                  ))}
                                </div>
                                <div className="trend-summary trend-summary-split">
                                  <div>
                                    <p>
                                      예약주문 4일 총합 = {data.itemDetails[r.rowKey].reservation4d.reduce((acc, p) => acc + Number(p.qty || 0), 0).toLocaleString()}
                                    </p>
                                    <p>
                                      권장 초도 발주 수량 = {mlRecommendEa(r).toLocaleString()}EA
                                    </p>
                                  </div>
                                  <div className="trend-summary-side">
                                    <button
                                      className="similar-toggle"
                                      onClick={(e) => {
                                        e.stopPropagation()
                                        setSimilarOpenMap((prev) => ({ ...prev, [r.rowKey]: !prev[r.rowKey] }))
                                      }}
                                    >
                                      유사상품 과거 발주량 조회
                                    </button>
                                  </div>
                                </div>
                                {similarOpenMap[r.rowKey] && (
                                  <div className="similar-history">
                                    {(pastRows || [])
                                      .filter((p) => p.category === r.category)
                                      .filter((p) => (p.releaseDate || '') < (selectedBaseDate || '9999-12-31'))
                                      .sort((a, b) => (b.releaseDate || '').localeCompare(a.releaseDate || ''))
                                      .slice(0, 8)
                                      .map((p) => (
                                      <div className="similar-row" key={`${r.rowKey}-${p.releaseDate}-${p.itemName}`}>
                                        <span>{p.releaseDate}</span>
                                        <span>{p.itemName}</span>
                                        <strong>
                                          {Number(p.actualOrderQty || 0).toLocaleString()}개
                                          <small> / {Math.round(Number(p.actualOrderQty || 0) / Math.max(Number(r.lduEa || 1), 1)).toLocaleString()}박스</small>
                                        </strong>
                                      </div>
                                    ))}
                                  </div>
                                )}
                                <article className="weight-summary-card">
                                  <h3 className="weight-title">센터 가중치 수정</h3>
                                  {(() => {
                                    const centers = data.itemDetails[r.rowKey].centerDistribution || []
                                    const weights = centerWeightMap[r.rowKey] || defaultCenterWeights(r)
                                    return (
                                      <div className="weight-editor-grid">
                                        {centers
                                          .slice()
                                          .sort((a, b) => a.centerName.localeCompare(b.centerName, 'ko'))
                                          .map((c) => (
                                            <div className="weight-row" key={c.centerName}>
                                              <span>{c.centerName}</span>
                                              <input
                                                type="number"
                                                min="0"
                                                step="0.01"
                                                value={Number(weights[c.centerName] || 0).toFixed(2)}
                                                onClick={(e) => e.stopPropagation()}
                                                onChange={(e) => {
                                                  const next = Number(e.target.value || 0)
                                                  setCenterWeightMap((prev) => ({
                                                    ...prev,
                                                    [r.rowKey]: {
                                                      ...(prev[r.rowKey] || defaultCenterWeights(r)),
                                                      [c.centerName]: Number.isFinite(next) ? next : 0,
                                                    },
                                                  }))
                                                  setCenterQtyMap((prev) => ({ ...prev, [r.rowKey]: undefined }))
                                                }}
                                              />
                                                  <small className="weight-meta">점포비중 {(Number(c.storeShare || 0) * 100).toFixed(1)}%</small>
                                                </div>
                                              ))}
                                      </div>
                                    )
                                  })()}
                                  <div className="weight-placeholder">
                                    <p className="weight-placeholder-main">여기에 뭐 넣을까요?</p>
                                    <p className="weight-placeholder-main">예상 출고율 고쳐야 함</p>
                                    <p className="weight-placeholder-note">현재 예상 출고율 로직이 권장 발주량에 맞추어져 있음</p>
                                  </div>
                                </article>
                              </article>

                              <article className="viz-card">
                                <h3>센터별 분배 수량</h3>
                                {(() => {
                                  const centers = centersForRow(r)
                                  const max = Math.max(...centers.map((x) => x.qty), 1)
                                  return (
                                    <div className="center-bars">
                                      {centers.map((c) => {
                                        const ldu = Math.max(Number(r.lduEa || 1), 1)
                                        const tone = centerTone(r, c.centerName, c.qty)
                                        const baseCenterBox = Number(baseCenterBoxMap(r)[c.centerName] || 0)
                                        return (
                                        <div key={c.centerName} className="center-row">
                                          <span>{c.centerName}</span>
                                          <div className="center-track">
                                            <div className={`center-fill ${tone}`} style={{ width: `${Math.round((c.qty / max) * 100)}%` }} />
                                          </div>
                                          <div className="center-edit">
                                            <input
                                              className={`center-qty-input ${tone}`}
                                              value={String(c.qty)}
                                              onClick={(e) => e.stopPropagation()}
                                              onChange={(e) => {
                                                const next = e.target.value.replace(/[^\d]/g, '')
                                                setCenterQtyMap((prev) => {
                                                  const current = prev[r.rowKey] || Object.fromEntries(centers.map((x) => [x.centerName, String(x.qty)]))
                                                  const updated = { ...current, [c.centerName]: next }
                                                  const totalBox = Object.values(updated).reduce((acc, v) => acc + Number(v || 0), 0)
                                                  setQtyMap((qm) => ({ ...qm, [r.rowKey]: String(totalBox) }))
                                                  return { ...prev, [r.rowKey]: updated }
                                                })
                                                setConfirmedMap((prev) => ({ ...prev, [r.rowKey]: false }))
                                              }}
                                            />
                                            <small>{Number(c.qty || 0).toLocaleString()}박스 / EA {Math.round(Number(c.qty || 0) * ldu).toLocaleString()}</small>
                                            <small>권장 발주량 {baseCenterBox.toLocaleString()}박스</small>
                                            {tone === 'high' && <small className="center-warn high">과발주 주의</small>}
                                            {tone === 'low' && <small className="center-warn low">결품 주의</small>}
                                          </div>
                                        </div>
                                      )})}
                                    </div>
                                  )
                                })()}
                              </article>
                            </div>
                          </td>
                        </tr>
                      )}
                    </Fragment>
                  ))}
                </tbody>
              </table>
            </section>

          </>
        ) : (
          <>
          <section className="date-bar">
            <label>날짜</label>
            <input type="date" value={pastDateFrom} onChange={(e) => setPastDateFrom(e.target.value)} />
            <span>~</span>
            <input type="date" value={pastDateTo} onChange={(e) => setPastDateTo(e.target.value)} />
            <label>대분류</label>
            <select value={pastCategory} onChange={(e) => setPastCategory(e.target.value)}>
              {pastCategoryOptions.map((c) => <option key={`cat-${c}`} value={c}>{c}</option>)}
            </select>
            <label>중분류</label>
            <select value={pastCategoryMid} onChange={(e) => setPastCategoryMid(e.target.value)}>
              {pastCategoryMidOptions.map((c) => <option key={`mid-${c}`} value={c}>{c}</option>)}
            </select>
            <label>소분류</label>
            <select value={pastCategorySub} onChange={(e) => setPastCategorySub(e.target.value)}>
              {pastCategorySubOptions.map((c) => <option key={`sub-${c}`} value={c}>{c}</option>)}
            </select>
            <label>정렬</label>
            <select value={pastSort} onChange={(e) => setPastSort(e.target.value)}>
              <option value="latest">최신순</option>
              <option value="high_rate">출고율 높은순</option>
              <option value="low_rate">출고율 낮은순</option>
              <option value="high_qty">발주량 높은순</option>
            </select>
            <label>검색</label>
            <input
              type="text"
              className="search"
              style={{ maxWidth: 220, padding: '8px 10px', fontSize: 14 }}
              placeholder="상품명/코드 검색"
              value={pastQuery}
              onChange={(e) => setPastQuery(e.target.value)}
            />
            <button
              className="ghost"
              onClick={() => {
                const headers = ['출시일', '상품코드', '상품명', '대분류', '중분류', '소분류', '발주량', '출고율', '사유']
                const lines = filteredPastRows.map((r) => [r.releaseDate, r.itemCode, r.itemName, r.category, r.categoryMid, r.categorySub, r.actualOrderQty, r.salesRate, r.actualDataReason || ''])
                const csv = [headers, ...lines].map((row) => row.map((v) => `"${String(v ?? '').replace(/"/g, '""')}"`).join(',')).join('\n')
                const blob = new Blob([`\uFEFF${csv}`], { type: 'text/csv;charset=utf-8;' })
                const url = URL.createObjectURL(blob)
                const a = document.createElement('a')
                a.href = url
                a.download = `past-items-${new Date().toISOString().slice(0, 10)}.csv`
                a.click()
                URL.revokeObjectURL(url)
              }}
            >
              엑셀 다운로드
            </button>
          </section>
          <section className="alert">
            <p className="manual-label">사용 가이드</p>
            <h3 className="manual-title">과거 신상품 조회 메뉴얼</h3>
            <p className="manual-text">과거 출시 상품의 발주/출고 성과를 조회하고, 상품 클릭 시 예약주문·센터분배·ML 대비 실제 차이를 확인할 수 있습니다.</p>
            <p className="manual-text">사용 순서: 날짜/분류/정렬/검색 필터 선택 → 행 클릭 상세 확인 → 과거 발주량·출고율·판정 비교</p>
          </section>
          <section className="criteria-strip">
            <span className="kpi high">과발주: 출고율 &lt; 50%</span>
            <span className="kpi ok">정상발주: 50% ~ 100%</span>
            <span className="kpi low">과소발주(결품위험): 출고율 &gt; 100%</span>
          </section>

          <section className="table-wrap">
            {filteredPastRows.length === 0 && (
              <div className="empty-note">선택한 필터에 해당하는 과거 상품이 없습니다. 필터를 전체로 변경해 보세요.</div>
            )}
            <table>
              <thead>
                <tr>
                  <th>상품코드</th><th>상품명</th><th>출시일</th><th>대분류</th><th>중분류</th><th>소분류</th><th>과거 발주량</th><th>출고율</th>
                </tr>
              </thead>
              <tbody>
                {filteredPastRows.map((row) => {
                  const pastDetail = data?.itemDetails?.[`${row.itemCode}_${row.releaseDate}`]
                  const reservation4d = pastDetail?.reservation4d || []
                  const reservationPre = pastDetail?.reservationPreRelease || reservation4d
                  const centerDist = pastDetail?.centerDistribution || []
                  const centerPerf = pastDetail?.centerPerformance7d || []
                  const postReleaseOutflow7d = pastDetail?.postReleaseOutflow7d || []
                  const centerMax = Math.max(...centerDist.map((c) => Number(c.qty || 0)), 1)
                  const reservationPreCumulative = reservationPre.reduce((acc, p, idx) => {
                    const prev = idx > 0 ? acc[idx - 1].qty : 0
                    acc.push({ date: p.date, qty: prev + Number(p.qty || 0) })
                    return acc
                  }, [])
                  const postReleaseOutflow7dCumulative = postReleaseOutflow7d.reduce((acc, p, idx) => {
                    const prev = idx > 0 ? acc[idx - 1].qty : 0
                    acc.push({ date: p.date, qty: prev + Number(p.qty || 0) })
                    return acc
                  }, [])
                  const pre4dSum = Number(pastDetail?.reservationPre4dSum ?? reservation4d.reduce((s, p) => s + Number(p.qty || 0), 0))
                  const preTotalSum = Number(pastDetail?.reservationPreTotalSum ?? reservationPre.reduce((s, p) => s + Number(p.qty || 0), 0))
                  const centerPerfMap = Object.fromEntries(centerPerf.map((c) => [c.centerName, Number(c.outflowRate7d || 0)]))
                  const unifiedSeries = [
                    ...reservationPre.map((x) => Number(x.qty || 0)),
                    ...reservationPreCumulative.map((x) => Number(x.qty || 0)),
                    ...postReleaseOutflow7d.map((x) => Number(x.qty || 0)),
                    ...postReleaseOutflow7dCumulative.map((x) => Number(x.qty || 0)),
                  ]
                  const unifiedBounds = {
                    min: 0,
                    max: Math.max(...unifiedSeries, 1),
                  }
                  const mlEa = Number(pastDetail?.formula?.totalRecommendQty || 0)
                  const actualEa = Number(row.actualOrderQty || 0)
                  const mlGap = actualEa - mlEa
                  const mlGapPct = mlEa > 0 ? Math.round((mlGap / mlEa) * 1000) / 10 : 0
                  const actualVsMlRatio = mlEa > 0 ? actualEa / mlEa : 0
                  const compareLabel = mlEa <= 0 ? '비교 불가' : actualVsMlRatio > 1.1 ? '과대 발주' : actualVsMlRatio < 0.9 ? '과소 발주' : '적정 발주'
                  const compareClass = compareLabel === '과대 발주' ? 'high' : compareLabel === '과소 발주' ? 'low' : compareLabel === '적정 발주' ? 'ok' : ''
                  const mlExpectedRate = mlEa > 0 ? Math.round((Number(row.actualOutflow7d || 0) / mlEa) * 1000) / 10 : 0
                  const outflow7d = Number(row.actualOutflow7d || 0)
                  const normalMinEa = outflow7d
                  const normalMaxEa = outflow7d * 2
                  const pastRateBand = outflowBand(Number(row.salesRate || 0))
                  const pastQtyTone = pastRateBand === 'over' ? 'high' : pastRateBand === 'shortage' ? 'low' : 'ok'
                  return (
                  <Fragment key={row.rowKey}>
                  <tr
                    className={Number(row.actualOrderQty || 0) <= 0 ? 'row-disabled' : ''}
                    onClick={() => {
                      if (Number(row.actualOrderQty || 0) <= 0) return
                      setPastExpandedKey((prev) => (prev === row.rowKey ? '' : row.rowKey))
                    }}
                    title={Number(row.actualOrderQty || 0) <= 0 ? '과거 발주량 0건은 상세 조회를 제공하지 않습니다.' : ''}
                  >
                    <td>{row.itemCode}</td>
                    <td>{row.itemName}</td>
                    <td>{row.releaseDate}</td>
                    <td><span className="cat">{row.category}</span></td>
                    <td>{row.categoryMid}</td>
                    <td>{row.categorySub}</td>
                    <td className="qty">
                      <span className={`past-order-value ${pastQtyTone}`}>{Number(row.actualOrderQty).toLocaleString()}개</span>
                      {row.actualDataReason ? <small className="cell-reason">{row.actualDataReason}</small> : null}
                    </td>
                    <td>
                      {row.salesRate}%
                      {row.actualDataReason ? <small className="cell-reason">{row.actualDataReason}</small> : null}
                    </td>
                  </tr>
                  {pastExpandedKey === row.rowKey && Number(row.actualOrderQty || 0) > 0 && (
                    <tr className="expand-row">
                      <td colSpan={8}>
                        <div className="inline-viz-grid past-detail-grid">
                          <article className="viz-card stacked-chart-card">
                            {reservationPre.length > 0 ? (
                              <>
                                <div className="chart-block">
                                  <h3>예약주문 수량 시각화</h3>
                                <div className="chart-meta-row">
                                  <p>예약주문 초기 4일 합: <strong>{pre4dSum.toLocaleString()}</strong></p>
                                  <p>예약주문 수량 합: <strong>{preTotalSum.toLocaleString()}</strong></p>
                                  <span className="chart-legend-inline">실선: 일자별 예약주문 · 점선: 누적합</span>
                                </div>
                                <svg className="trend-line" viewBox="0 0 560 210" preserveAspectRatio="none">
                                  <path d={buildAreaPath(reservationPreCumulative, 560, 210, 24, unifiedBounds)} fill="#dcfce7" opacity="0.7" />
                                  <path d={buildLinePath(reservationPreCumulative, 560, 210, 24, unifiedBounds)} fill="none" stroke="#16a34a" strokeWidth="2" strokeDasharray="5 4" />
                                  <path d={buildLinePath(reservationPre, 560, 210, 24, unifiedBounds)} fill="none" stroke="#0c7a43" strokeWidth="3" />
                                  {reservationPre.map((p, idx) => {
                                    const { x, y } = pointXY(p, idx, reservationPre, 560, 210, 24, unifiedBounds)
                                    return (
                                      <g key={p.date}>
                                        <circle cx={x} cy={y} r="4.5" fill="#0c7a43" />
                                        <text x={x} y={Math.max(14, y - 8)} textAnchor="middle" fontSize="10" fill="#14532d">
                                          {Number(p.qty).toLocaleString()}
                                        </text>
                                      </g>
                                    )
                                  })}
                                  {reservationPreCumulative.length > 0 && (() => {
                                    const lastIdx = reservationPreCumulative.length - 1
                                    const last = reservationPreCumulative[lastIdx]
                                    const { x, y } = pointXY(last, lastIdx, reservationPreCumulative, 560, 210, 24, unifiedBounds)
                                    return (
                                      <text x={x - 6} y={Math.max(14, y - 10)} textAnchor="end" fontSize="10" fill="#166534">
                                        누적 {Number(last.qty).toLocaleString()}
                                      </text>
                                    )
                                  })()}
                                  {reservationPre.map((p, idx) => {
                                    const { x } = pointXY(p, idx, reservationPre, 560, 210, 24, unifiedBounds)
                                    return (
                                      <text key={`x-pre-${p.date}`} x={x} y={206} textAnchor="middle" fontSize="10" fill="#64748b">
                                        {formatMd(p.date)}
                                      </text>
                                    )
                                  })}
                                </svg>
                                </div>
                                {postReleaseOutflow7d.length > 0 && (
                                  <div className="chart-block">
                                    <h3 className="subchart-title">출시 후 7일 출고 흐름</h3>
                                    <div className="chart-meta-row">
                                      <p>출시 후 센터 7일 출고 합: <strong>{postReleaseOutflow7d.reduce((s, p) => s + Number(p.qty || 0), 0).toLocaleString()}</strong></p>
                                      <span className="chart-legend-inline">실선: 일자별 출고 · 점선: 누적합</span>
                                    </div>
                                    <svg className="trend-line" viewBox="0 0 560 210" preserveAspectRatio="none">
                                      <path d={buildAreaPath(postReleaseOutflow7dCumulative, 560, 210, 24, unifiedBounds)} fill="#dbeafe" opacity="0.75" />
                                      <path d={buildLinePath(postReleaseOutflow7dCumulative, 560, 210, 24, unifiedBounds)} fill="none" stroke="#1d4ed8" strokeWidth="2" strokeDasharray="5 4" />
                                      <path d={buildLinePath(postReleaseOutflow7d, 560, 210, 24, unifiedBounds)} fill="none" stroke="#2563eb" strokeWidth="3" />
                                      {postReleaseOutflow7d.map((p, idx) => {
                                        const { x, y } = pointXY(p, idx, postReleaseOutflow7d, 560, 210, 24, unifiedBounds)
                                        return (
                                          <g key={`post-${p.date}`}>
                                            <circle cx={x} cy={y} r="4" fill="#2563eb" />
                                            <text x={x} y={Math.max(12, y - 8)} textAnchor="middle" fontSize="10" fill="#1e3a8a">
                                              {Number(p.qty).toLocaleString()}
                                            </text>
                                          </g>
                                        )
                                      })}
                                      {postReleaseOutflow7dCumulative.length > 0 && (() => {
                                        const lastIdx = postReleaseOutflow7dCumulative.length - 1
                                        const last = postReleaseOutflow7dCumulative[lastIdx]
                                        const { x, y } = pointXY(last, lastIdx, postReleaseOutflow7dCumulative, 560, 210, 24, unifiedBounds)
                                        return (
                                          <text x={x - 6} y={Math.max(14, y - 10)} textAnchor="end" fontSize="10" fill="#1e3a8a">
                                            누적 {Number(last.qty).toLocaleString()}
                                          </text>
                                        )
                                      })()}
                                      {postReleaseOutflow7d.map((p, idx) => {
                                        const { x } = pointXY(p, idx, postReleaseOutflow7d, 560, 210, 24, unifiedBounds)
                                        return (
                                          <text key={`x-post-${p.date}`} x={x} y={206} textAnchor="middle" fontSize="10" fill="#64748b">
                                            {formatMd(p.date)}
                                          </text>
                                        )
                                      })}
                                    </svg>
                                  </div>
                                )}
                              </>
                            ) : (
                              <p className="formula-note">예약주문 데이터가 없습니다.</p>
                            )}
                          </article>
                          <article className="viz-card center-map-card">
                            <h3>실제 센터 분배량 · 성과 맵</h3>
                            <div className="center-legend">
                              <span className="kpi high">과발주 &lt; 50%</span>
                              <span className="kpi ok">정상발주 50~100%</span>
                              <span className="kpi low">과소발주 &gt; 100%</span>
                            </div>
                            {centerDist.length > 0 ? (
                              <div className="center-bars">
                                {centerDist.map((c) => (
                                  (() => {
                                    const rate = centerPerfMap[c.centerName] ?? 0
                                    const outflowQty = (centerPerf.find((p) => p.centerName === c.centerName)?.outflow7d ?? 0)
                                    const band = outflowBand(rate)
                                    const tone = band === 'over' ? 'high' : band === 'shortage' ? 'low' : 'ok'
                                    const statusLabel = band === 'over' ? '과발주' : band === 'shortage' ? '과소발주' : '정상발주'

                                    return (
                                      <div
                                        key={c.centerName}
                                        className="center-row"
                                        data-tooltip={`7일 소화 물량: ${Number(outflowQty || 0).toLocaleString()}개`}
                                      >
                                        <span>{c.centerName}</span>
                                        <div className="center-track-wrap">
                                          <div className="center-track">
                                            <div className="center-fill base" style={{ width: `${Math.round((Number(c.qty || 0) / centerMax) * 100)}%` }} />
                                            <div
                                              className={`center-fill ${tone}`}
                                              style={{
                                                width: `${Math.round((Number(c.qty || 0) / centerMax) * (Math.min(rate, 100) / 100) * 100)}%`,
                                                opacity: 0.95,
                                              }}
                                            />
                                          </div>
                                          <small className={`center-status ${tone}`}>{statusLabel}</small>
                                        </div>
                                        <div className="center-edit">
                                          <strong>{Number(c.qty || 0).toLocaleString()}개</strong>
                                          <small>7일 소화율 {Number(rate).toFixed(1)}%</small>
                                        </div>
                                      </div>
                                    )
                                  })()
                                ))}
                              </div>
                            ) : (
                              <p className="formula-note">센터 분배 데이터가 없습니다.</p>
                            )}
                          </article>
                          <article className="viz-card">
                            <h3>ML 기반 예측 비교</h3>
                            <div className="ml-compare-grid">
                              <div className="ml-headline">
                                <p className="ml-line">
                                  비교 상태:
                                  <span className={`kpi ${compareClass}`} style={{ marginLeft: 8 }}>{compareLabel}</span>
                                </p>
                                <p className="ml-line">
                                  정상 발주량 범주(7일): <strong>{normalMinEa.toLocaleString()}EA ~ {normalMaxEa.toLocaleString()}EA</strong>
                                </p>
                              </div>
                              <div className="ml-metrics-grid">
                                <div className="ml-metric-card">
                                  <small>ML 권장 초도</small>
                                  <strong>{mlEa.toLocaleString()}EA</strong>
                                </div>
                                <div className="ml-metric-card">
                                  <small>실제 초도</small>
                                  <strong>{actualEa.toLocaleString()}EA</strong>
                                </div>
                                <div className="ml-metric-card">
                                  <small>편차</small>
                                  <strong>{mlGap >= 0 ? '+' : ''}{mlGap.toLocaleString()}EA</strong>
                                  <span className="summary-sub">({mlGapPct >= 0 ? '+' : ''}{mlGapPct}%)</span>
                                </div>
                                <div className="ml-metric-card">
                                  <small>실제 출고율</small>
                                  <strong>{row.salesRate}%</strong>
                                </div>
                                <div className="ml-metric-card">
                                  <small>ML 기준 기대 출고율</small>
                                  <strong>{mlExpectedRate}%</strong>
                                </div>
                              </div>
                            </div>
                          </article>
                        </div>
                      </td>
                    </tr>
                  )}
                  </Fragment>
                )})}
              </tbody>
            </table>
          </section>
          </>
        )}
      </main>
    </div>
  )
}

export default App

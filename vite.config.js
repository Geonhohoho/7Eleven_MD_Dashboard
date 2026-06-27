import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

const cleanGeminiText = (value) => String(value ?? '')
  .replace(/\*\*/g, '')
  .replace(/\*/g, '')
  .replace(/^\s*[-•]\s*/gm, '')
  .replace(/\b(Key Centers?|Recommendation|Rationale|Action|Summary|Overall|Reason|Execution|Risk|Next Steps?)\s*:\s*/gi, '')
  .replace(/\n{3,}/g, '\n\n')
  .trim()
const isUsableGeminiText = (text) => {
  const value = String(text || '').trim()
  return value.length >= 120 && value.includes('판단:') && value.includes('이유:') && value.includes('주의:') && value.includes('다음 행동:')
}
const geminiModels = ['gemini-2.5-flash', 'gemini-2.0-flash', 'gemini-flash-lite-latest']

const buildGeminiPrompt = (item = {}) => {
  const centers = (item.centers || [])
    .slice(0, 6)
    .map((c) => `- ${c.centerName}: 권장 ${c.recommendedBox ?? 0}박스, 입력 ${c.inputBox ?? 0}박스, 점포비중 ${c.storeSharePct ?? 0}%, 가중치 ${c.centerWeight ?? 1}`)
    .join('\n')
  const similarProducts = (item.similarProducts || [])
    .slice(0, 4)
    .map((p) => `- ${p.itemName}: 초도 ${p.actualOrderQty ?? 0}EA, 초도/적정 ${p.adequacyRate ?? 0}%`)
    .join('\n')

  return `
너는 세븐일레븐 MD가 신상품 초도발주를 검토할 때 쓰는 검토 코멘트를 작성한다.
반드시 한국어로만 작성한다. 영어 제목, 영어 단어 중심 문장, 마크다운 굵게 표시, 별표(*)를 절대 쓰지 않는다.
새로운 발주량/수요량을 계산하지 말고, 아래 제공된 수치와 룰베이스 신호만 해석한다.
확정 표현보다 "가능성이 있습니다", "확인할 필요가 있습니다", "검토 대상입니다"처럼 MD 검토형 문장을 쓴다.
독자는 데이터 분석을 모르는 MD다. 피처, 가중치, 분포, 모델 같은 분석 용어를 쓰지 말고 업무 언어로 쉽게 풀어쓴다.
수치만 나열하지 말고 "그래서 발주를 어떻게 봐야 하는지"를 설명한다.

상품명: ${item.itemName}
카테고리: ${item.categoryPath}
목표도입률: ${item.goalIntroRate ?? 0}%
운영 추천 초도 발주량: ${item.recommendedEa ?? 0}EA (${item.recommendedBox ?? 0}박스)
입력 발주량: ${item.inputEa ?? 0}EA (${item.inputBox ?? 0}박스)
예약주문 총량: ${item.reservationSum ?? 0}EA
초기 예약 집중도: ${item.frontloadRatio ?? 0}%
예약 수요 등급: ${item.demandSignal}
유사상품 평균 초도: ${item.similarAvgOrder ?? 0}EA
유사상품 초도/적정: ${item.similarAvgRate ?? 0}%
유사상품 판정: ${item.similarAdequacySignal}
주요 유사상품:
${similarProducts || '- 없음'}
수요 높음 예상 센터:
${centers || '- 없음'}
센터 검토 신호: ${item.centerSignal}

기본 요약 카드의 문장을 반복하지 말고, 아래 한국어 형식으로만 작성한다. 각 항목은 1문장, 전체는 520자 이내.
판단: 이 상품을 지금 추천량대로 확정해도 되는지, 또는 늘리거나 줄여 검토해야 하는지 쉽게 말한다.
이유: 예약주문 흐름과 비슷한 과거 상품 사례를 연결해서 왜 그런 판단인지 설명한다.
주의: 과발주 또는 결품위험이 생길 수 있는 지점을 MD가 이해하기 쉬운 말로 짚는다.
다음 행동: 발주 확정 전 MD가 실제로 눌러보거나 확인할 일을 1~2개 제안한다.
`
}

const localGeminiApi = (apiKey) => ({
  name: 'local-gemini-md-reason-api',
  configureServer(server) {
    server.middlewares.use('/api/md-reason', async (req, res) => {
      if (req.method !== 'POST') {
        res.statusCode = 405
        res.end(JSON.stringify({ error: 'POST only' }))
        return
      }
      if (!apiKey) {
        res.statusCode = 500
        res.end(JSON.stringify({ error: 'GEMINI_API_KEY is not configured' }))
        return
      }

      const chunks = []
      req.on('data', (chunk) => chunks.push(chunk))
      req.on('end', async () => {
        try {
          const body = JSON.parse(Buffer.concat(chunks).toString('utf8') || '{}')
          let text = ''
          let lastError = ''
          for (const model of geminiModels) {
            const response = await fetch(
              `https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent`,
              {
                method: 'POST',
                headers: {
                  'Content-Type': 'application/json',
                  'X-goog-api-key': apiKey,
                },
                body: JSON.stringify({
                  contents: [{ role: 'user', parts: [{ text: buildGeminiPrompt(body.item || {}) }] }],
                  generationConfig: { temperature: 0.25, topP: 0.8, maxOutputTokens: 520 },
                }),
              },
            )
            if (response.ok) {
              const json = await response.json()
              const candidateText = cleanGeminiText(json?.candidates?.[0]?.content?.parts?.map((p) => p.text || '').join('\n'))
              if (isUsableGeminiText(candidateText)) {
                text = candidateText
                break
              }
              lastError = `Gemini returned incomplete text from ${model}`
              continue
            }
            lastError = await response.text()
          }
          if (!text) throw new Error(lastError || 'Gemini request failed')
          res.setHeader('Content-Type', 'application/json')
          res.end(JSON.stringify({ text: text || '' }))
        } catch (error) {
          res.statusCode = 500
          res.setHeader('Content-Type', 'application/json')
          res.end(JSON.stringify({ error: error?.message || 'AI summary failed' }))
        }
      })
    })
  },
})

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  return {
    plugins: [react(), localGeminiApi(env.GEMINI_API_KEY)],
  }
})

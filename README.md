# 7-Eleven MD 신상품 초도발주 대시보드

React + Vite 기반의 MD 신상품 초도발주 의사결정 대시보드입니다.

## 실행 방법

```bash
npm install
npm run dev
```

로컬 접속 주소는 터미널에 표시되는 `http://127.0.0.1:포트번호/`를 사용합니다.

## 배포 방법

Vercel은 GitHub 저장소의 `main` 브랜치 변경사항을 감지해 자동 배포합니다.

```bash
npm run build
git add .
git commit -m "Update dashboard"
git push origin main
```

## 주요 화면

- 금일 신상품 작업: 2025-12-26 기준 출시 5일 전 확정 대상 상품의 예약수요, 모델 추천량, 도입률, 센터별 분배 수량을 확인하고 발주 확정까지 진행합니다.
- 과거 신상품 조회: 과거 과자 신상품의 초도물량, 센터 출고, 점포 판매, 목표/예측 도입률을 비교합니다.
- 수요 네트워크/제품 생애주기 정보: 금일 상품 상세 탭 안에서 보조 모델 정보로 확인합니다.

## 대시보드 핵심 데이터

배포에 필요한 정적 데이터는 `public/data` 아래에 있습니다.

- `dashboard-data.json`: 화면에서 직접 읽는 메인 통합 데이터
- `final_preorder.csv`: 신상품 예약주문 및 센터별 초도 발주 원천
- `A4_final_CENTER_STK.csv`: 센터 재고 기반 초도/출고 계산 원천
- `ml_predictions_for_dashboard.csv`: 최종 모델 추천량
- `gnn-network.json`: GNN 기반 수요 네트워크 데이터
- `lifecycle-data.json`: 제품 생애주기 보조 모델 데이터
- `store_sales_item_center_date_cache.csv`: 점포 판매 수량 집계 캐시
- `store_sales_item_date_coverage.csv`: 점포 판매 데이터 커버리지 점검용

## 데이터 재생성

원천 CSV가 바뀌면 아래 스크립트로 `public/data/dashboard-data.json`을 다시 생성합니다.

```bash
python3 scripts/build_dashboard_data.py
```

## 보안 메모

`.env.local`과 API 키는 GitHub/Vercel에 직접 커밋하지 않습니다. Vercel 환경변수에서 별도로 설정합니다.

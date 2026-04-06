# SCM Risk Intelligence Platform — 프로젝트 기술 문서

> 메가프로젝트 EPC(Engineering, Procurement, Construction) 기업을 위한 공급망 리스크 관리 플랫폼

---

## 1. 프로젝트 개요

### 1.1 배경 및 문제 정의

EPC 메가프로젝트(정유, 석유화학, 발전 플랜트 등)는 수백~수천 개의 장비를 전 세계 공급업체로부터 조달하고, 복잡한 해상/육상 운송 경로를 통해 현장에 배송합니다. 이 과정에서 **지정학적 리스크**(호르무즈 해협 봉쇄, 수에즈 운하 차단), **자연재해**(일본 지진), **무역 규제**(중국 관세, 러시아 제재) 등이 발생하면 프로젝트 일정과 비용에 치명적인 영향을 미칩니다.

**핵심 문제:**
- 공급망 구성요소 간의 **복잡한 의존관계**를 파악하기 어려움
- 특정 이벤트가 전체 공급망에 미치는 **파급효과(Cascade Impact)** 를 실시간으로 분석하기 어려움
- 대안 경로·대체 공급업체·긴급 항공 운송 등 **완화 전략의 비용-효과 분석**이 수작업으로 진행됨

### 1.2 솔루션

**Neo4j 지식 그래프** 기반으로 프로젝트-장비-공급업체-운송경로-항구-지정학적 위험지대의 관계를 모델링하고, **AI 에이전트 오케스트레이션**을 통해 교란 시나리오의 영향 분석, 대안 탐색, TCO(Total Cost of Ownership) 비교를 자동화합니다.

### 1.3 핵심 기능

| 기능 | 설명 |
|------|------|
| **실시간 대시보드** | 포트폴리오 KPI, 리스크 매트릭스, 알림 피드 |
| **지식 그래프 시각화** | D3.js 기반 Neo4j 그래프 탐색 |
| **지도 기반 모니터링** | Leaflet 지도 위에 운송 경로, 교란 영역, 장비 위치 표시 |
| **교란 시뮬레이션** | 사전 정의된 5개 시나리오 + 커스텀 이벤트 주입 |
| **AI 채팅 분석** | 자연어로 질의하면 AI 에이전트가 그래프를 분석하여 응답 |
| **헤징 리포트** | TCO 기반 완화 전략 비교 및 의사결정 지원 |

---

## 2. 기술 스택 및 아키텍처

### 2.1 전체 아키텍처

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (Next.js 14)                     │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │Dashboard │ │  MapView │ │ ChatPanel│ │ Hedging  │  ...       │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘           │
│       │             │            │             │                  │
│  ┌────┴─────────────┴────────────┴─────────────┴─────┐          │
│  │              Zustand State Management              │          │
│  │  (disruptionStore / projectStore / mapStore)        │          │
│  └────────────────────────┬──────────────────────────┘          │
│                           │ REST API + WebSocket                 │
└───────────────────────────┼──────────────────────────────────────┘
                            │
┌───────────────────────────┼──────────────────────────────────────┐
│                   Backend (FastAPI + Uvicorn)                     │
│                           │                                       │
│  ┌────────────────────────┴──────────────────────────┐           │
│  │                   Router Layer                     │           │
│  │  chat / disruptions / projects / equipment /       │           │
│  │  suppliers / routes / analytics / hedging / feeds   │           │
│  └────────────────────────┬──────────────────────────┘           │
│                           │                                       │
│  ┌────────────────────────┴──────────────────────────┐           │
│  │                  Service Layer                     │           │
│  │  ImpactService / CostService / HedgingService /    │           │
│  │  ScenarioService / SupplierService / RoutingService │           │
│  └────────────────────────┬──────────────────────────┘           │
│                           │                                       │
│  ┌────────────────────────┴──────────────────────────┐           │
│  │              AI Agent Orchestrator                 │           │
│  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐     │           │
│  │  │Impact  │ │Supplier│ │ Route  │ │  Cost  │     │           │
│  │  │Agent   │ │Agent   │ │Agent   │ │Agent   │     │           │
│  │  └────┬───┘ └────┬───┘ └────┬───┘ └────┬───┘     │           │
│  │       └──────────┴──────────┴──────────┘          │           │
│  │                Agent Tools (Neo4j queries,         │           │
│  │                scoring, optimization)              │           │
│  └───────────────────────────────────────────────────┘           │
│                           │                                       │
│  ┌────────────────────────┴──────────────────────────┐           │
│  │               Database Layer                       │           │
│  │  Neo4j Client (Singleton) │ Redis Client │ PostgreSQL         │
│  └───────────────────────────────────────────────────┘           │
└──────────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
   ┌────┴────┐        ┌────┴────┐        ┌────┴────┐
   │ Neo4j   │        │  Redis  │        │PostgreSQL│
   │ (Graph) │        │ (Cache) │        │ (RDBMS)  │
   └─────────┘        └─────────┘        └──────────┘
```

### 2.2 기술 스택 상세

| 영역 | 기술 | 선택 이유 |
|------|------|----------|
| **Backend Framework** | FastAPI + Uvicorn | 비동기 네이티브, 자동 API 문서, Pydantic 검증 |
| **Graph Database** | Neo4j 5.17 | 공급망의 복잡한 관계를 자연스럽게 모델링, Cypher 쿼리로 N-hop 탐색 가능 |
| **Relational DB** | PostgreSQL 16 | 감사 로그, 트랜잭션 데이터, Alembic 마이그레이션 |
| **Cache/Pub-Sub** | Redis 7 | 분석 결과 캐싱, WebSocket 브로드캐스트용 Pub/Sub |
| **AI Engine** | Anthropic Claude API | 자연어 질의 → 구조화된 분석, Streaming 응답 |
| **Frontend** | Next.js 14 + TypeScript | App Router, SSR/CSR 하이브리드 |
| **State Management** | Zustand | 경량, 보일러플레이트 최소, React 외부에서도 접근 가능 |
| **Visualization** | D3.js + Leaflet + Recharts | 지식그래프, 지도, 차트 각각에 최적화된 라이브러리 |
| **Infrastructure** | Docker Compose + GCP Cloud Run | 로컬 개발 → 프로덕션 배포 일관성 |

---

## 3. 데이터 모델 — Neo4j 지식 그래프

### 3.1 그래프 스키마

공급망의 실제 물리적·비즈니스 관계를 그래프로 표현합니다:

```
                    ┌─────────┐
                    │ Project │
                    └────┬────┘
                         │ HAS_EQUIPMENT
                    ┌────┴────┐
                    │Equipment│
                    └┬──┬──┬──┘
          SUPPLIED_BY│  │  │SHIPPED_VIA      HAS_SUBSTITUTE
       ┌─────────────┘  │  └──────────────┐       ↕
  ┌────┴────┐    ORDERED_VIA         ┌────┴──────┐
  │Supplier │           │            │ShippingRoute│
  └──┬──┬───┘    ┌──────┴──────┐     └┬─────┬────┘
     │  │        │PurchaseOrder│      │     │
     │  │        └─────────────┘      │     │PASSES_THROUGH
     │  │LOCATED_NEAR  DEPARTS_FROM───┘     │
     │  └──────┐  ARRIVES_AT──────────┘┌────┴──────────┐
     │    ┌────┴──┐                    │GeopoliticalZone│
     │    │ Port  │                    └───────────────┘
     │    └───────┘
     │HAS_ALTERNATIVE
     └──→ (Supplier)
```

### 3.2 노드 유형 및 속성

| 노드 | 주요 속성 | 설명 |
|------|----------|------|
| **Project** | projectId, name, client, country, totalValue, completionPct, criticalPathDeadline, riskTolerance | EPC 메가프로젝트 |
| **Equipment** | equipmentId, name, category, criticality, weight, requiredOnSiteDate | 조달 대상 장비 |
| **Supplier** | supplierId, name, country, onTimeDeliveryRate, qualityRejectRate, riskFlags | 장비 제조사/공급업체 |
| **PurchaseOrder** | poId, issueDate, value, expectedDeliveryDate | 조달 발주서 |
| **ShippingRoute** | routeId, name, currentStatus, estimatedTransitDays, shippingCost | 해상/육상 운송 경로 |
| **Port** | portId, name, country, currentStatus, congestionLevel | 출발/도착 항구 |
| **GeopoliticalZone** | zoneId, name, type, riskLevel(1-10), currentStatus | 지정학적 위험 지대 |

### 3.3 왜 Graph Database인가?

**관계형 DB 대비 이점:**

1. **N-hop 관계 탐색의 효율성**: "호르무즈 해협이 봉쇄되면 어떤 프로젝트가 영향받는가?"
   ```cypher
   MATCH (z:GeopoliticalZone {name: "Strait of Hormuz"})
         <-[:PASSES_THROUGH]-(r:ShippingRoute)
         <-[:SHIPPED_VIA]-(e:Equipment)
         <-[:HAS_EQUIPMENT]-(p:Project)
   RETURN p.name, collect(e.name)
   ```
   → 관계형 DB에서는 3~4개의 JOIN이 필요하지만, Neo4j는 패턴 매칭으로 직관적으로 표현

2. **동적 관계 추가**: `HAS_ALTERNATIVE`, `HAS_SUBSTITUTE` 같은 대안 관계를 스키마 변경 없이 추가

3. **경로 탐색**: 대안 경로 찾기가 그래프 알고리즘으로 자연스럽게 해결

---

## 4. AI 에이전트 오케스트레이션

### 4.1 아키텍처

```
사용자 질의: "호르무즈 해협 봉쇄 시 NEOM 프로젝트 영향은?"
                    │
            ┌───────┴────────┐
            │  Orchestrator  │ ← Intent Classification
            │  (총괄 조율자)   │   (키워드 기반 의도 분류)
            └───────┬────────┘
                    │
    ┌───────────────┼───────────────┐
    │               │               │
┌───┴───┐     ┌────┴────┐    ┌────┴────┐
│Impact │     │Supplier │    │  Route  │
│Agent  │     │Agent    │    │ Agent   │
│(영향분석)│  │(대안공급)│    │(대안경로)│
└───┬───┘     └────┬────┘    └────┬────┘
    │              │              │
    └──────────────┴──────────────┘
                   │
           ┌───────┴────────┐
           │  Claude API    │ ← 에이전트 결과를 자연어로 종합
           │  (응답 합성)    │   (Streaming, 8000 토큰 제한)
           └───────┬────────┘
                   │
           최종 응답 (Streaming)
```

### 4.2 에이전트 상세

| 에이전트 | 역할 | 핵심 알고리즘 |
|---------|------|-------------|
| **ImpactAgent** | 교란 이벤트의 파급효과 분석 | 그래프 탐색으로 영향받는 장비·경로·프로젝트 집계, 리스크 스코어(0-1) 계산 |
| **SupplierAgent** | 대안 공급업체 탐색 및 랭킹 | 지리적 제외, 제재 필터링, 인증 검증 후 다기준 스코어링(납기율, 품질, 비용) |
| **RouteAgent** | 대안 운송 경로 탐색 | 멀티모달 평가(해상, 희망봉 우회, 육상 철도, 항공) + 비용-시간 트레이드오프 |
| **CostAgent** | TCO 시나리오 비교 분석 | 기준선(무조치) vs 완화 전략의 총비용 비교, BCR(Benefit-Cost Ratio) 랭킹 |
| **NewsAgent** | 뉴스/외부 신호 감지 | 지정학적 리스크 시그널 모니터링 (시뮬레이션) |
| **DisruptionAgent** | 교란 이벤트 생성 및 관리 | 이벤트 레코드 생성, 영향 분석 트리거, 자동 에스컬레이션 |

### 4.3 Intent Classification (의도 분류)

Claude API에 의존하지 않고 **키워드 매칭 기반**으로 의도를 분류합니다:

```python
INTENT_KEYWORDS = {
    "impact_analysis": ["impact", "affect", "disruption", "damage", "risk"],
    "find_alternatives": ["alternative", "substitute", "backup", "reroute"],
    "cost_analysis": ["cost", "price", "roi", "savings", "penalty"],
    "status_query": ["status", "overview", "dashboard", "show me"],
    "disruption_detection": ["detect", "news", "scenario", "what if"],
}
```

**설계 결정**: ML 기반 분류 대신 키워드 매칭을 선택한 이유:
- **속도**: 추가 API 호출 없이 즉시 분류
- **해석 가능성**: 어떤 키워드가 매칭되었는지 추적 가능
- **안정성**: 외부 서비스 장애와 무관하게 작동

### 4.4 Graceful Degradation (우아한 퇴화)

```
Claude API 가용 → AI가 에이전트 결과를 자연어로 합성
Claude API 불가 → Rule-based 요약 생성 (구조화된 텍스트)
Backend 불가   → Frontend Mock 데이터로 동작
Neo4j 불가    → 연결 실패를 허용, 빈 결과 반환 (앱 전체가 크래시하지 않음)
```

---

## 5. TCO (Total Cost of Ownership) 분석 엔진

### 5.1 비용 계산 구조

```
TCO = 기준선 비용 (무조치 시)
    = 지연 일수 × (
        Liquidated Damages (주간 프로젝트 가치의 %, 최대 10%까지)
      + 현장 오버헤드 ($50,000/일)
      + 유휴 인력 ($25,000/일)
      + 장비 보관 비용 (무게 × 중요도 기반)
    )
```

### 5.2 완화 시나리오 비교

| 시나리오 | 비용 요소 | 특징 |
|---------|----------|------|
| **경로 변경** | 운송비 차액 + 잔여 지연 페널티 | 가장 일반적, 중간 비용 |
| **공급업체 전환** | 자격 검증 비용 + 리드타임 차이 | 시간 소요 큼, 장기적 효과 |
| **항공 운송** | 무게 기반 ($8/kg) + 보험 | 5톤 미만만 가능, 최단 시간(3일) |
| **지연 수용** | 기준선 비용 그대로 | 비교 기준선 |

**최종 의사결정**: BCR(Benefit-Cost Ratio)로 랭킹하여 최적 전략 추천

---

## 6. 프론트엔드 아키텍처

### 6.1 뷰 구성

```
┌─ Sidebar ──────────────────────────────────────────┐
│  ┌──────────┐                                       │
│  │Dashboard │ → KPICards + AlertFeed + ProjectHealth │
│  │RiskMatrix│ → Severity × Probability 매트릭스       │
│  │Projects  │ → 프로젝트 포트폴리오 + 상세            │
│  │Map       │ → Leaflet 지도 + 다중 레이어            │
│  │Ontology  │ → D3.js 지식 그래프 탐색기              │
│  │Impact    │ → Sankey 다이어그램 + 비용 비교          │
│  │Scenario  │ → 교란 시뮬레이터 + 이벤트 주입기        │
│  │Hedging   │ → TCO 분석 리포트 + 의사결정 매트릭스    │
│  └──────────┘                                       │
└────────────────────────────────────────────────────┘
```

### 6.2 상태 관리 — Zustand

**선택 이유:**
- Redux 대비 보일러플레이트 90% 감소
- React 컴포넌트 외부에서도 상태 접근 가능 (WebSocket 핸들러에서 직접 업데이트)
- 경량 (~1KB gzip)

**주요 스토어:**

```typescript
// DisruptionStore — 교란 상태 관리
interface DisruptionState {
  activeDisruptions: DisruptionEvent[];
  affectedEquipmentIds: string[];
  affectedRouteIds: string[];
  impactAnalysis: ImpactAnalysis | null;
  recommendations: SupplierRecommendation[];
  routeAlternatives: RouteAlternative[];
}

// ProjectStore — 프로젝트 포트폴리오
// MapStore — 지도 레이어 가시성
```

### 6.3 실시간 업데이트 — WebSocket

```
Frontend                    Backend                    Redis
   │                           │                         │
   │── WebSocket Connect ─────→│                         │
   │                           │                         │
   │   (교란 이벤트 발생)         │                         │
   │                           │── Publish ──────────────→│
   │                           │←── Subscribe ───────────│
   │←── disruption_alert ─────│                         │
   │←── agent_status ─────────│ (분석 진행 중...)         │
   │←── impact_update ────────│ (분석 완료)               │
   │                           │                         │
   │   Zustand Store 자동 업데이트                         │
```

### 6.4 Mock Fallback 시스템

프론트엔드는 백엔드가 불가용할 때 **Mock 데이터로 전체 UI가 동작**합니다:
- 5개 교란 시나리오에 대한 Mock 프로필 내장
- Mock TCO 엔진이 백엔드 CostAgent와 동일한 계산 로직 구현
- API 호출 실패 시 자동으로 Mock으로 전환

---

## 7. 인프라 및 배포

### 7.1 로컬 개발 환경

```yaml
# docker-compose.yml
services:
  neo4j:    # 5.17.0 — APOC 플러그인 활성화, 헬스체크
  postgres: # 16 — Alembic 마이그레이션 관리
  redis:    # 7 — 캐싱 + Pub/Sub
```

- 모든 서비스에 **헬스체크** 설정 (10초 간격, 5회 재시도)
- Named Volume으로 데이터 영속성 보장
- `scripts/setup.sh`로 원클릭 환경 구성

### 7.2 GCP 프로덕션 배포

```
                    ┌────────────────────┐
                    │   Cloud Load       │
                    │   Balancer         │
                    │   + SSL 인증서      │
                    └─────────┬──────────┘
                              │
                    ┌─────────┴──────────┐
                    │   Cloudflare DNS   │
                    │   (vints.ai)       │
                    └─────────┬──────────┘
              ┌───────────────┼───────────────┐
              │               │               │
     ┌────────┴───────┐ ┌────┴────┐          │
     │  Cloud Run     │ │Cloud Run│          │
     │  (Frontend)    │ │(Backend)│          │
     │  Port 3000     │ │Port 8000│          │
     │  0-3 인스턴스   │ │0-3 인스턴스│        │
     └────────────────┘ └────┬────┘          │
                             │               │
              ┌──────────────┼──────────┐    │
              │              │          │    │
     ┌────────┴──┐  ┌───────┴───┐ ┌────┴────┐
     │ Cloud SQL │  │Memorystore│ │Neo4j    │
     │(PostgreSQL)│ │  (Redis)  │ │(Aura/VM)│
     └───────────┘  └───────────┘ └─────────┘
```

**보안:**
- Secret Manager로 DB 비밀번호, API 키 관리
- Cloud SQL Connector로 안전한 DB 접속
- Artifact Registry에 Docker 이미지 저장

---

## 8. 교란 시나리오 시스템

### 8.1 사전 정의 시나리오

| 시나리오 | 심각도 | 영향 범위 | 예상 비용 영향 |
|---------|--------|----------|--------------|
| 호르무즈 해협 봉쇄 | 5/5 | 7개 경로, 89개 장비, 최대 120일 지연 | $47M |
| 수에즈 운하 차단 | 4/5 | 3개 경로, ~35개 장비, 7-14일 지연 | — |
| 일본 지진 (요코하마) | 4/5 | 3개 공급업체, ~20개 장비, 항구 용량 60% 감소 | — |
| 중국 관세 (25%) | 3/5 | 회전/정적 장비, 2개 프로젝트 | 장비 비용 프리미엄 |
| 러시아 제재 (철강) | 3/5 | 1개 공급업체 차단, 고합금 압력 용기 | — |

### 8.2 시뮬레이션 플로우

```
1. 사용자가 시나리오 선택 (또는 커스텀 이벤트 주입)
2. DisruptionAgent가 교란 이벤트 레코드 생성
3. ImpactAgent가 그래프 탐색으로 파급효과 분석
4. SupplierAgent + RouteAgent가 대안 탐색
5. CostAgent가 TCO 시나리오 비교
6. WebSocket으로 실시간 진행상황 브로드캐스트
7. 결과를 대시보드, 지도, 헤징 리포트에 표시
```

---

## 9. 핵심 설계 패턴

### 9.1 Singleton Pattern — 데이터베이스 클라이언트

```python
class Neo4jClient:
    _instance: Optional["Neo4jClient"] = None
    _lock: asyncio.Lock = asyncio.Lock()

    @classmethod
    async def get_instance(cls) -> "Neo4jClient":
        async with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance
```

**왜?** 비동기 환경에서 커넥션 풀 고갈을 방지하고, 모든 요청이 동일한 드라이버 인스턴스를 공유하도록 보장

### 9.2 Service Layer Pattern

```
Router (HTTP 처리) → Service (비즈니스 로직) → Agent (알고리즘) → Tools (DB 쿼리)
```

각 레이어가 명확한 책임을 가지며, 테스트와 교체가 용이

### 9.3 Agent Orchestration Pattern

오케스트레이터가 의도를 분류하고, 전문화된 에이전트에 작업을 위임한 뒤, 결과를 종합:
- 에이전트들은 **독립적으로 실행** 가능 (병렬화 가능)
- 오케스트레이터가 **결과 합성**을 담당
- Claude API가 최종 **자연어 변환**을 수행

### 9.4 Graceful Degradation

모든 서브시스템이 독립적으로 실패 가능:
- DB 연결 실패 → 앱 시작은 성공, 해당 기능만 비활성화
- Claude API 불가 → Rule-based 응답 생성
- 백엔드 불가 → 프론트엔드 Mock 데이터로 동작

### 9.5 Event-Driven Architecture

- Redis Pub/Sub로 서비스 간 이벤트 전파
- WebSocket으로 클라이언트에 실시간 업데이트
- 교란 → 영향분석 → 알림의 비동기 파이프라인

---

## 10. 데이터 플로우 상세

### 10.1 교란 영향 분석 플로우

```
사용자: "호르무즈 해협 봉쇄 시 영향은?"
  │
  ├─ Frontend: POST /api/agents/chat { message, context }
  │
  ├─ chat.py Router: _build_context() → 관련 엔티티 조회
  │
  ├─ Orchestrator.run()
  │   ├─ _classify_intent() → "impact_analysis"
  │   ├─ ImpactAgent.run(disruption_event)
  │   │   ├─ find_affected_equipment(zone_id) → Cypher 그래프 탐색
  │   │   ├─ 영향받는 경로, 프로젝트, 공급업체 집계
  │   │   └─ 리스크 스코어 계산 (0-1)
  │   └─ _synthesize_response()
  │       ├─ Claude API → 자연어 합성 (Streaming)
  │       └─ 또는 Rule-based 요약 생성
  │
  ├─ WebSocket: impact_update 브로드캐스트
  │
  └─ Frontend: 대시보드 + 지도 업데이트
```

### 10.2 헤징 의사결정 플로우

```
사용자: 영향 분석 결과 확인 → "대안 분석" 클릭
  │
  ├─ Frontend: GET /api/hedging/report/{disruption_id}?delay_days=30
  │
  ├─ HedgingService → CostAgent.run()
  │   ├─ 기준선 계산: $2.5M (지연 30일 × 일일 비용)
  │   ├─ 시나리오 A: 경로 변경 → $1.8M (BCR 2.1x)
  │   ├─ 시나리오 B: 공급업체 전환 → $1.2M (BCR 1.5x)
  │   └─ 시나리오 C: 항공 운송 → $0.9M (BCR 0.8x, 5톤 미만만)
  │
  ├─ 결과: BCR 기준 랭킹 → 최적 전략 추천
  │
  └─ Frontend: 시나리오 비교 차트 + 의사결정 매트릭스
```

---

## 11. 면접 포인트

### 11.1 기술적 의사결정 설명

**Q: 왜 Neo4j(그래프 DB)를 선택했는가?**
> 공급망은 본질적으로 그래프 구조입니다. 프로젝트→장비→공급업체→운송경로→항구→위험지대의 다단계 관계를 탐색할 때, 관계형 DB의 다중 JOIN은 비효율적이고 쿼리가 복잡해집니다. Neo4j의 Cypher는 "호르무즈 해협을 통과하는 경로로 운송되는 장비를 보유한 프로젝트"를 패턴 매칭 한 줄로 표현할 수 있고, 관계 탐색 성능이 O(1)에 가깝습니다.

**Q: AI 에이전트 오케스트레이션의 설계 원칙은?**
> 단일 LLM에 모든 것을 맡기지 않고, 각 문제 영역(영향분석, 공급업체 탐색, 비용 분석)에 특화된 에이전트를 두었습니다. 오케스트레이터가 의도를 분류하고 적절한 에이전트에 작업을 위임하면, 각 에이전트가 Neo4j에서 필요한 데이터를 직접 조회하여 구조화된 결과를 반환합니다. Claude API는 이 결과들을 사람이 읽을 수 있는 자연어로 합성하는 마지막 단계에서만 사용됩니다.

**Q: Graceful Degradation은 어떻게 구현했는가?**
> 세 단계의 폴백을 설계했습니다. (1) Claude API가 불가하면 Rule-based 텍스트 생성으로 전환, (2) 백엔드가 불가하면 프론트엔드에 내장된 Mock 데이터로 UI가 완전히 동작, (3) 개별 DB 연결 실패 시 앱 전체가 아닌 해당 기능만 비활성화됩니다. 이를 통해 부분 장애 상황에서도 사용자 경험이 유지됩니다.

**Q: 상태 관리로 Redux 대신 Zustand를 선택한 이유는?**
> 세 가지 이유입니다. (1) 보일러플레이트가 Redux 대비 90% 적어 개발 속도가 빠름, (2) React 컴포넌트 외부(WebSocket 핸들러)에서 직접 상태를 업데이트할 수 있어 실시간 이벤트 처리에 적합, (3) 번들 크기가 ~1KB로 경량입니다.

### 11.2 아키텍처적 강점

1. **계층 분리**: Router → Service → Agent → Tools의 명확한 책임 분리로 테스트·유지보수 용이
2. **비동기 전체 적용**: FastAPI + async Neo4j/Redis/PostgreSQL 드라이버로 높은 동시성 지원
3. **지식 그래프 기반**: 공급망의 복잡한 관계를 자연스럽게 모델링하고 효율적으로 탐색
4. **다중 에이전트 협업**: 전문화된 에이전트가 독립적으로 분석하고 오케스트레이터가 종합
5. **실시간 아키텍처**: WebSocket + Redis Pub/Sub로 교란 발생 → 분석 → 알림의 실시간 파이프라인

### 11.3 확장성 고려사항

- Cloud Run 오토스케일링 (0-3 인스턴스, 부하 기반)
- Neo4j 인덱싱 전략 (projectId, equipmentId, zoneId)
- Redis 캐싱으로 반복 분석 결과 저장
- 데이터베이스 커넥션 풀링 (Singleton 패턴)
- Batch 시딩 (UNWIND 사용)

---

## 12. 프로젝트 규모

| 항목 | 수치 |
|------|------|
| 백엔드 Python 파일 | ~40개 |
| 프론트엔드 TypeScript/TSX 파일 | ~60개 |
| Neo4j 노드 유형 | 7개 |
| 관계 유형 | 12개+ |
| API 엔드포인트 | 40개+ |
| AI 에이전트 | 6개 특화 + 1개 오케스트레이터 |
| 교란 시나리오 템플릿 | 5개 |
| Docker 서비스 | 3개 (Neo4j, PostgreSQL, Redis) |
| GCP 클라우드 서비스 | 5개 |
| Git 커밋 수 | 31개 |

---

## 13. 기술 스택 전체 요약

```
Frontend:  Next.js 14 · React 18 · TypeScript · Tailwind CSS · Zustand
           D3.js · Leaflet · Recharts · Radix UI · Socket.io-client

Backend:   Python 3.11+ · FastAPI · Uvicorn · Pydantic
           Anthropic Claude API · LangChain

Database:  Neo4j 5.17 (Graph) · PostgreSQL 16 (RDBMS) · Redis 7 (Cache)
           Alembic (Migration) · SQLAlchemy (ORM)

Infra:     Docker Compose · GCP Cloud Run · Cloud SQL · Memorystore
           Artifact Registry · Secret Manager · Cloud Load Balancer
           Cloudflare DNS
```

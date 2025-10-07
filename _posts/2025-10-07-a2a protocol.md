---
title: "A2A Protocol 서버/클라이언트 만들기(1)"
excerpt: "A2A Protocol의 이해"

categories:
    - study
header:
  teaser: "/assets/images/a2a_img.png"
last_modified_at: 2025-10-07
---

A2A 프로토콜을 사용하여 통신하는 클라이언트/서버를 만드는 것을 목표로 한다. <br/>

Python SDK를 사용하여 개발하고 Code Run을 통해 배포하는 예제는 아래에서 학습할 수 있다. <br />
https://codelabs.developers.google.com/intro-a2a-purchasing-concierge?hl=ko#1


나는 Go를 사용해 클라이언트/서버를 만들었고 OpenAI를 통해 자연어 처리를 하도록 구성하였다.
배송 요금/라벨 발급을 하는 서비스이며, 고객이 박스 사이즈/무게/발송지/도착지를 보내면, 컨시어지가 여러 택배사 에이전트에게 견적/ETA/라벨 발급 가능 여부를 질의해서 최적의 선택을 반환한다.<br/>
이번 포스팅에서 택배사 에이전트는 AI 에이전트가 아니며 A2A Protocol을 통한 통신을 주 목적으로 한다<br/>
세부 코드는 아래에서 확인할 수 있다.<br/>

https://github.com/KIMMUSIC/a2a-protocol

<hr>

## [프로젝트 구조]

```css
pkg/a2a/                 # A2A 공통 계약(타입/서명/미들웨어)
services/
  concierge-go/          # 오케스트레이터(팬아웃/팬인)
  agent-a-go/            # 캐리어 A (동기 QUOTE/SHIP)
  agent-b-go/            # 캐리어 B (QUOTE, 비동기 SHIP)
  interpreter-go/        # LLM 기반 자연어 → QUOTE.input 구조화

```

### [A2A Contract Type]

공통 A2A 타입을 정의하는 부분이다.

```go
package a2a

import "encoding/json"

const ContractVersion = "1.0"

// ---- Task lifecycle ---------------------------------------------------------

type TaskStatus string

const (
	StatusPending   TaskStatus = "PENDING"
	StatusRunning   TaskStatus = "RUNNING"
	StatusSucceeded TaskStatus = "SUCCEEDED"
	StatusFailed    TaskStatus = "FAILED"
)

// CreateTask: 다른 에이전트에게 작업을 위임할 때 사용하는 표준 입력
type CreateTask struct {
	TaskType       string          `json:"task_type"`                 // e.g. QUOTE | SHIP | RANK | INTERPRET
	Input          json.RawMessage `json:"input"`                     // 도메인별 입력(JSON blob)
	ReplyURL       string          `json:"reply_url,omitempty"`       // 콜백 받을 URL(옵션)
	IdempotencyKey string          `json:"idempotency_key,omitempty"` // 멱등 처리용
	Meta           map[string]any  `json:"meta,omitempty"`            // 추가 컨텍스트(옵션)
}

// Task: 작업의 현재 상태/결과/오류를 나타내는 표준 출력
type Task struct {
	TaskID string          `json:"task_id"`
	Status TaskStatus      `json:"status"`
	Result json.RawMessage `json:"result,omitempty"` // 도메인별 결과(JSON blob)
	Error  *ErrorPayload   `json:"error,omitempty"`
}

// ---- Agent discovery ---------------------------------------------------------

type AgentMeta struct {
	AgentID      string            `json:"agent_id"`
	Name         string            `json:"name"`
	Version      string            `json:"version"`          // 구현체 버전
	ContractVer  string            `json:"contract_version"` // A2A 계약 버전 (1.0)
	Capabilities []AgentCapability `json:"capabilities"`
	Auth         *AuthSpec         `json:"auth,omitempty"`
}

type AgentCapability struct {
	TaskType     string `json:"task_type"`     // e.g. QUOTE
	InputSchema  string `json:"input_schema"`  // 문서/스키마 식별자(설명 또는 URL 가능)
	OutputSchema string `json:"output_schema"` // 문서/스키마 식별자
}

type AuthSpec struct {
	Required bool   `json:"required"`
	Scheme   string `json:"scheme"` // "HMAC" | "mTLS" | "None"
}

// ---- Task events (async callbacks) ------------------------------------------

type Event struct {
	Event   string          `json:"event"` // e.g. TASK_COMPLETED | TASK_FAILED | TASK_PROGRESS
	TaskID  string          `json:"task_id"`
	Payload json.RawMessage `json:"payload,omitempty"` // 결과/중간상태
}
```

### [concierge-go]

클라이언트에 해당하는 컨시어지 main 함수의 코드를 살펴보자

```go
func discover(base string) {
	resp, err := http.Get(base + "/.well-known/agent.json")
	if err != nil {
		log.Println("discovery error:", base, err)
		return
	}
	defer resp.Body.Close()
	var meta a2a.AgentMeta
	json.NewDecoder(resp.Body).Decode(&meta)
	log.Printf("discovered: %s capabilities=%v\n", meta.AgentID, meta.Capabilities)
}
```

agent로 요청을 보내 에이전트 카드를 얻어오는 부분이다.

각 에이전트는 아래와 같은 에이전트 카드를 응답한다.

### [interpreter]
```go
	// Discovery
	r.Get("/.well-known/agent.json", func(w http.ResponseWriter, _ *http.Request) {
		meta := a2a.AgentMeta{
			AgentID:     agentID,
			Name:        "Interpreter (Go LLM)",
			Version:     "0.2.0",
			ContractVer: a2a.ContractVersion,
			Capabilities: []a2a.AgentCapability{
				{TaskType: "INTERPRET", InputSchema: "Utterance", OutputSchema: "QuoteRequest"},
			},
			Auth: &a2a.AuthSpec{Required: false, Scheme: "HMAC"},
		}
		_ = json.NewEncoder(w).Encode(meta)
	})
```

### [agent-a/agent-b]
```go
    	r.Get("/.well-known/agent.json", func(w http.ResponseWriter, _ *http.Request) {
		meta := a2a.AgentMeta{
			AgentID: agentID, Name: "Agent-A (Go)", Version: "0.1.0",
			ContractVer: a2a.ContractVersion,
			Capabilities: []a2a.AgentCapability{
				{TaskType: "QUOTE", InputSchema: "QuoteRequest", OutputSchema: "QuoteResult"},
				{TaskType: "SHIP", InputSchema: "ShipRequest", OutputSchema: "ShipResult"},
			},
			Auth: &a2a.AuthSpec{Required: false, Scheme: "HMAC"},
		}
		json.NewEncoder(w).Encode(meta)
	})
```

agent-a는 동기로 응답하며 agent-b는 비동기 + 콜백으로 응답한다.

### [agent-a]

```go
r.Post("/tasks", func(w http.ResponseWriter, r *http.Request) {
		var ct a2a.CreateTask
		if err := json.NewDecoder(r.Body).Decode(&ct); err != nil {
			w.WriteHeader(400)
			json.NewEncoder(w).Encode(a2a.Task{Error: a2a.NewError(a2a.ErrValidationFailed, err.Error())})
			return
		}
		if err := a2a.ValidateCreateTask(&ct); err != nil {
			w.WriteHeader(400)
			json.NewEncoder(w).Encode(a2a.Task{Error: a2a.NewError(a2a.ErrValidationFailed, err.Error())})
			return
		}
		taskID := "t_" + RandID()
		t := &a2a.Task{TaskID: taskID, Status: a2a.StatusSucceeded} // QUOTE/SHIP 동기 처리(Agent-A는 동기)
		switch ct.TaskType {
		case "QUOTE":
			result := map[string]any{"carrier": "AgentA", "service": "EXPRESS", "price": 7000 + 1500*2, "eta_days": 2}
			b, _ := json.Marshal(result)
			t.Result = b
		case "SHIP":
			result := map[string]any{"status": "READY", "tracking_id": "A-" + RandID(), "label_url": "https://cdn.local/A.png"}
			b, _ := json.Marshal(result)
			t.Result = b
		default:
			t.Status = a2a.StatusFailed
			t.Error = a2a.NewError(a2a.ErrValidationFailed, "unsupported task_type")
		}
		st.mu.Lock()
		st.m[taskID] = t
		st.mu.Unlock()
		json.NewEncoder(w).Encode(map[string]any{"task_id": taskID, "status": t.Status})
	})
```

### [agent-b]

```go
// services/agent-b-go/main.go (핵심만)
tid := "t_" + RandID()
switch ct.TaskType {
case "SHIP":
  saveTask(tid, a2a.StatusPending, nil)   // 1) 먼저 PENDING
  go func(tid string, input json.RawMessage, reply string) {
    time.Sleep(3*time.Second)             // 처리 지연 시뮬
    res := map[string]any{"status":"READY","tracking_id":"B-"+RandID(),"label_url":"https://cdn/B.png"}
    saveTask(tid, a2a.StatusSucceeded, mustJSON(res))
    // 2) A2A 이벤트 콜백 (Concierge의 /tasks/{id}/events)
    http.Post(replyOrDefault(reply, conciergeBase)+"/tasks/"+tid+"/events",
      "application/json",
      bytes.NewReader(mustJSON(map[string]any{"event":"TASK_COMPLETED","task_id":tid,"payload":res})))
  }(tid, ct.Input, ct.ReplyURL)
  _ = json.NewEncoder(w).Encode(map[string]any{"task_id":tid,"status":a2a.StatusPending})
}

```

agent-b는 PENDING 영수증만 먼저 반환,
백그라운드에서 처리 후 Concierge 이벤트 엔드포인트로 TASK_COMPLETED 전송 → Concierge가 자기 Task 상태를 SUCCEEDED로 바꾼다.

### [concierge]

클라이언트에서 자연어해석 -> 팬아웃 -> 팬인 집계를 처리하는 부분의 코드이다.

```go
// services/concierge-go/main.go (핵심)
var agentA = env("AGENT_A_URL","http://localhost:8081")
var agentB = env("AGENT_B_URL","http://localhost:8082")

// 1) 자연어면 Interpreter 먼저
quoteInput := ct.Input
if needsInterpret(ct.Input) {
  structured, err := postInterpret(interpreterURL, ct.Input)
  if err != nil { /* 400 처리 */ }
  quoteInput = dropMeta(structured) // _meta 제거(있다면)
}

// 2) fan-out
ctx, cancel := context.WithTimeout(r.Context(), 2*time.Second)
defer cancel()

type qres struct{ ok bool; data map[string]any; err error }
ch := make(chan qres, 2)

go func(){ q,err:=postTask(agentA,"QUOTE",quoteInput); ch<-qres{err==nil,q,err} }()
go func(){ q,err:=postTask(agentB,"QUOTE",quoteInput); ch<-qres{err==nil,q,err} }()

// 3) fan-in
var quotes []map[string]any
var partial []any
for i:=0;i<2;i++{
  select {
    case r := <-ch:
      if r.ok { quotes=append(quotes,r.data) } else { partial=append(partial,r.err.Error()) }
    case <-ctx.Done():
      partial=append(partial,"timeout"); i=2
  }
}

// 4) 집계 결과 저장
saveTask(taskID, a2a.StatusSucceeded, mustJSON(map[string]any{
  "quotes": quotes, "partial_failures": partial,
}))

```


### [요청과 응답]

```
Mac ~ % curl -s localhost:8083/tasks -H 'Content-Type: application/json' \
  -d '{"task_type":"INTERPRET","input":{"utterance":"서울에서 일본으로 5kg 빠르게"}}' | python3 -m json.tool
{
    "status": "SUCCEEDED",
    "task_id": "t_interp_015421"
}

Mac ~ % curl -s localhost:8083/tasks/t_interp_015421                      
  
{"task_id":"t_interp_015421","status":"SUCCEEDED","result":{"from":{"country":"KR"},"to":{"country":"JP"},"parcel":{"h_cm":15,"l_cm":30,"w_cm":20,"weight_kg":5},"options":{"priority":true},"currency":"KRW","max_wait_ms":1200}}
```

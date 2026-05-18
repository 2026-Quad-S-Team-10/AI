# POST /ai/news/generate API 테스트 정리

## 테스트 대상

- Swagger URL: http://localhost:8000/docs
- Method: `POST`
- Path: `/ai/news/generate`
- Content-Type: `application/json`

이 API는 경제 용어 `term`과 퀴즈 난이도 `difficulty`를 받아 대표 뉴스를 찾고, 뉴스 요약, 경제 용어 설명, 퀴즈를 생성해 반환한다.

## Swagger 테스트 방법

1. 로컬 서버 실행

```bash
uvicorn app.main:app --reload
```

2. 브라우저에서 http://localhost:8000/docs 접속
3. `AI News` 섹션의 `POST /ai/news/generate` 선택
4. `Try it out` 클릭
5. 요청 body 입력
6. `Execute` 클릭
7. 응답 코드와 JSON 필드 확인

실제 200 응답 테스트에는 `.env` 또는 환경변수에 `OPENAI_API_KEY`가 설정되어 있어야 한다. API Key는 문서나 코드에 직접 작성하지 않는다.

## 정상 요청 예시

### term만 전달

```json
{
  "term": "수요",
  "difficulty": "BEGINNER"
}
```

기대 결과:

- `200 OK`
- `term`이 `"수요"`로 반환된다.
- `newsTitle`, `newsUrl`, `source`, `pubDate`가 포함된다.
- `summary`는 문자열 3개를 가진 배열이다.
- `keywordExplanation`은 비어 있지 않은 문자열이다.
- `quiz`는 배열이며 각 문제에 `type`, `question`, `answer`, `explanation`이 포함된다.
- `MULTIPLE_CHOICE` 문제에는 `options` 4개가 포함되고 `answer`는 options 중 하나와 정확히 일치한다.

### category 포함

```json
{
  "term": "수요",
  "difficulty": "BEGINNER",
  "category": "국내"
}
```

기대 결과:

- `200 OK`
- `category`가 `"국내"`인 대표 뉴스가 사용된다.
- 응답의 `category` 필드가 `"국내"`로 반환된다.

## 정상 응답 예시

```json
{
  "term": "수요",
  "category": "국내",
  "newsTitle": "KB국민은행, 중진공 손잡고 생산적금융 6조원 지원…중소기업 자금 부담...",
  "newsSummary": "KB국민은행은 중진공과의 협력을 기반으로 지역 단위 금융 수요에도 대응할 계획이다.",
  "newsUrl": "https://www.seoultimes.news/news/article.html?no=2000095062",
  "source": "seoultimes.news",
  "pubDate": "Sun, 12 Apr 2026 13:18:00 +0900",
  "summary": [
    "KB국민은행은 중소기업의 자금 부담을 줄이기 위해 정책자금 이용 기업을 지원합니다.",
    "이번 지원은 금리 우대와 보증 혜택을 통해 기업이 필요한 자금을 더 쉽게 마련하도록 돕는 내용입니다.",
    "이 뉴스에서 수요는 중소기업이 자금을 필요로 하는 상황과 연결됩니다."
  ],
  "keywordExplanation": "수요는 사람들이 어떤 상품이나 서비스를 필요로 하거나 사고자 하는 정도를 뜻합니다. 이 기사에서는 중소기업이 자금을 필요로 하는 상황이 금융 수요와 연결됩니다.",
  "quiz": [
    {
      "type": "OX",
      "question": "수요는 사람들이 상품이나 서비스를 필요로 하는 정도를 의미한다.",
      "answer": "O",
      "explanation": "수요는 어떤 것을 필요로 하거나 구매하려는 의사를 뜻합니다."
    },
    {
      "type": "MULTIPLE_CHOICE",
      "question": "기사에서 중소기업의 자금 수요와 가장 관련 있는 내용은?",
      "options": [
        "자금 조달 부담을 줄이기 위한 금융 지원",
        "소비자의 구매 감소",
        "세금 폐지",
        "수출의 완전 중단"
      ],
      "answer": "자금 조달 부담을 줄이기 위한 금융 지원",
      "explanation": "기사에서는 중소기업의 자금 부담을 낮추기 위한 지원 프로그램을 설명합니다."
    }
  ]
}
```

## 예외 요청 및 응답 예시

### 존재하지 않는 term

요청:

```json
{
  "term": "없는용어",
  "difficulty": "BEGINNER"
}
```

기대 응답:

```json
{
  "detail": "No news found for term: 없는용어"
}
```

상태 코드:

- `404 Not Found`

### 잘못된 difficulty

요청:

```json
{
  "term": "수요",
  "difficulty": "EASY"
}
```

기대 응답:

```json
{
  "detail": [
    {
      "type": "literal_error",
      "loc": ["body", "difficulty"],
      "msg": "Input should be 'BEGINNER', 'INTERMEDIATE' or 'ADVANCED'"
    }
  ]
}
```

상태 코드:

- `422 Unprocessable Entity`

### 빈 term

요청:

```json
{
  "term": "   ",
  "difficulty": "BEGINNER"
}
```

기대 결과:

- `422 Unprocessable Entity`
- `term must not be empty.` 메시지 확인

### content가 비어 있는 경우

기대 결과:

- 대표 뉴스 선택 시 content가 빈 행은 CSV 로딩/조회 단계에서 제외된다.
- 특정 term의 모든 뉴스 content가 비어 있으면 `400 Bad Request` 또는 명확한 content 관련 에러를 반환해야 한다.

예상 응답:

```json
{
  "detail": "news content must not be empty."
}
```

### OpenAI API Key 누락 또는 GPT 호출 실패

기대 결과:

- `500 Internal Server Error`
- API Key 누락 시 예시:

```json
{
  "detail": "OPENAI_API_KEY environment variable is not set."
}
```

### GPT 응답 JSON 파싱 실패

기대 결과:

- `500 Internal Server Error`
- 예시:

```json
{
  "detail": "Failed to parse quiz response as JSON: ..."
}
```

## 백엔드 전달용 API 명세 요약

### Request

```ts
type NewsGenerateRequest = {
  term: string;
  difficulty?: "BEGINNER" | "INTERMEDIATE" | "ADVANCED";
  category?: string | null;
};
```

### Response

```ts
type NewsGenerateResponse = {
  term: string;
  category: string | null;
  newsTitle: string;
  newsSummary: string | null;
  newsUrl: string | null;
  source: string | null;
  pubDate: string | null;
  summary: string[];
  keywordExplanation: string;
  quiz: Array<{
    type: "OX" | "MULTIPLE_CHOICE";
    question: string;
    answer: string;
    explanation: string;
    options?: string[];
  }>;
};
```

### Status Codes

- `200`: 생성 성공
- `404`: 해당 term/category 조건에 맞는 뉴스 없음
- `422`: 요청 validation 실패
- `500`: OpenAI 호출 실패 또는 GPT 응답 파싱 실패

## 최종 확인 체크리스트

- [ ] `/docs`에서 `POST /ai/news/generate`가 보인다.
- [ ] 정상 요청 시 `200 OK`가 반환된다.
- [ ] `summary` 배열 길이가 3이다.
- [ ] `keywordExplanation`이 비어 있지 않다.
- [ ] `quiz` 배열에 OX와 객관식 문제가 포함된다.
- [ ] 객관식 `answer`가 `options` 중 하나와 정확히 일치한다.
- [ ] 없는 term 요청 시 404가 반환된다.
- [ ] 잘못된 difficulty 요청 시 422가 반환된다.
- [ ] OpenAI API Key 누락 시 명확한 500 에러가 반환된다.

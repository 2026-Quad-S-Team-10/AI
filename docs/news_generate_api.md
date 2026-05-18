# 뉴스 요약 및 퀴즈 생성 API 명세

## 1. API 개요

- 기능명: 뉴스 요약 및 퀴즈 생성 API
- 설명: 경제 용어 `term`과 난이도 `difficulty`를 입력받아 CSV 뉴스 데이터에서 관련 대표 뉴스를 찾고, GPT 기반 뉴스 요약, 경제 용어 설명, 학습용 퀴즈를 생성해 반환한다.
- 기준 URL: `http://localhost:8000`
- Swagger URL: `http://localhost:8000/docs`

## 2. API Endpoint

```http
POST /ai/news/generate
```

Content-Type:

```http
application/json
```

## 3. Request Body

| 필드 | 타입 | 필수 여부 | 설명 |
| --- | --- | --- | --- |
| `term` | `string` | 필수 | 조회할 경제 용어. 빈 문자열은 허용하지 않는다. |
| `difficulty` | `string` | 선택 | 퀴즈 난이도. 기본값은 `BEGINNER`이다. |
| `category` | `string \| null` | 선택 | 뉴스 카테고리 필터. 전달하지 않으면 term 기준으로만 조회한다. |

`difficulty` 허용값:

- `BEGINNER`: 용어 뜻과 기사 핵심을 쉽게 묻는 난이도
- `INTERMEDIATE`: 기사 속 원인과 결과 관계를 묻는 난이도
- `ADVANCED`: 경제 용어가 실제 경제 상황에 적용되는 방식을 묻는 난이도

`category` 예시:

- `국내`
- `국제`
- `주식`
- `부동산`
- 그 외 CSV `category` 컬럼에 존재하는 값

요청 예시:

```json
{
  "term": "수요",
  "difficulty": "BEGINNER",
  "category": "국내"
}
```

`category` 없이 요청하는 예시:

```json
{
  "term": "수요",
  "difficulty": "BEGINNER"
}
```

## 4. Response Body

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `term` | `string` | 요청한 경제 용어 또는 대표 뉴스의 term |
| `category` | `string \| null` | 대표 뉴스의 카테고리 |
| `newsTitle` | `string` | 대표 뉴스 제목 |
| `newsSummary` | `string \| null` | CSV에 저장된 기존 뉴스 요약 |
| `newsUrl` | `string \| null` | 뉴스 원문 URL |
| `source` | `string \| null` | 뉴스 출처 |
| `pubDate` | `string \| null` | 뉴스 발행일 |
| `summary` | `string[]` | GPT가 생성한 3줄 요약. 정확히 3개 문장을 기대한다. |
| `keywordExplanation` | `string` | 경제 용어가 뉴스에서 어떻게 쓰였는지에 대한 쉬운 설명 |
| `quiz` | `object[]` | 학습용 퀴즈 배열 |

`quiz` 항목 공통 필드:

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `type` | `"OX" \| "MULTIPLE_CHOICE"` | 퀴즈 유형 |
| `question` | `string` | 문제 |
| `answer` | `string` | 정답 |
| `explanation` | `string` | 해설 |

`MULTIPLE_CHOICE` 추가 필드:

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `options` | `string[]` | 객관식 보기. 4개 항목을 기대한다. |

응답 예시:

```json
{
  "term": "수요",
  "category": "국내",
  "newsTitle": "뉴스 제목",
  "newsSummary": "CSV에 있던 기존 요약",
  "newsUrl": "https://example.com/news",
  "source": "예시뉴스",
  "pubDate": "Sun, 12 Apr 2026 13:18:00 +0900",
  "summary": [
    "첫 번째 요약 문장",
    "두 번째 요약 문장",
    "세 번째 요약 문장"
  ],
  "keywordExplanation": "경제 용어가 뉴스에서 어떻게 쓰였는지 쉬운 설명",
  "quiz": [
    {
      "type": "OX",
      "question": "수요는 사람들이 상품이나 서비스를 사고자 하는 욕구를 의미한다.",
      "answer": "O",
      "explanation": "수요는 구매하고자 하는 의사와 필요를 뜻합니다."
    },
    {
      "type": "MULTIPLE_CHOICE",
      "question": "기사에서 수요와 가장 관련 있는 내용은 무엇인가요?",
      "options": [
        "자금이 필요한 기업이 늘어난 상황",
        "가격이 완전히 사라진 상황",
        "소비자가 없는 상황",
        "시장이 폐쇄된 상황"
      ],
      "answer": "자금이 필요한 기업이 늘어난 상황",
      "explanation": "기사에서는 중소기업의 자금 필요가 늘어난 상황을 설명하고 있습니다."
    }
  ]
}
```

## 5. Error Response

에러 응답은 FastAPI 기본 형식에 따라 `detail` 필드를 포함한다.

| 상태 코드 | 상황 | 설명 |
| --- | --- | --- |
| `400` | 잘못된 요청 또는 빈 뉴스 content | 뉴스 본문이 비어 있거나 처리할 수 없는 요청 값인 경우 |
| `404` | 뉴스 없음 | 요청한 `term` 또는 `term/category` 조건에 해당하는 뉴스가 없는 경우 |
| `422` | 요청 body 검증 실패 | `term`이 비어 있거나 `difficulty`가 허용값이 아닌 경우 |
| `500` | OpenAI 호출 실패 또는 GPT 응답 파싱 실패 | API Key 누락, OpenAI 호출 오류, GPT 응답 JSON 형식 오류 등 |

존재하지 않는 term 예시:

```json
{
  "detail": "No news found for term: 없는용어"
}
```

잘못된 difficulty 예시:

```json
{
  "detail": [
    {
      "type": "literal_error",
      "loc": ["body", "difficulty"],
      "msg": "Input should be 'BEGINNER', 'INTERMEDIATE' or 'ADVANCED'",
      "input": "EASY"
    }
  ]
}
```

OpenAI API Key 누락 예시:

```json
{
  "detail": "OPENAI_API_KEY environment variable is not set."
}
```

## 6. CSV 컬럼 구조

CSV 파일 위치:

```text
app/data/news.csv
```

필수 컬럼:

| 컬럼 | 설명 |
| --- | --- |
| `term` | 경제 용어 |
| `category` | 뉴스 분야 |
| `title` | 뉴스 제목 |
| `summary` | CSV에 저장된 기존 뉴스 요약 |
| `content` | 뉴스 본문 |
| `source` | 출처 |
| `url` | 뉴스 원문 URL |
| `pubDate` | 발행일 |

대표 뉴스 선택 기준:

- `term`이 요청값과 일치하는 뉴스만 조회한다.
- `category`가 전달되면 해당 category까지 함께 필터링한다.
- `content`가 비어 있는 뉴스는 제외한다.
- `pubDate`를 기준으로 최신순 정렬한 뒤 첫 번째 뉴스를 대표 뉴스로 사용한다.

## 7. 백엔드 연동 흐름

```text
프론트
  -> 백엔드에 오늘의 학습/퀴즈 요청
  -> 백엔드가 AI 서버에 term, difficulty, category 전달
  -> AI 서버가 CSV에서 대표 뉴스 조회
  -> AI 서버가 뉴스 본문 전처리
  -> AI 서버가 GPT로 3줄 요약 생성
  -> AI 서버가 GPT로 경제 용어 설명 생성
  -> AI 서버가 GPT로 OX/객관식 퀴즈 생성
  -> AI 서버가 JSON 반환
  -> 백엔드가 결과 저장 또는 프론트에 전달
```

백엔드 요청 예시:

```bash
curl -X POST "http://localhost:8000/ai/news/generate" \
  -H "Content-Type: application/json" \
  -d '{"term":"수요","difficulty":"BEGINNER","category":"국내"}'
```

## 8. Swagger 테스트 방법

1. 서버 실행

```bash
uvicorn app.main:app --reload
```

2. 브라우저에서 `http://localhost:8000/docs` 접속
3. `AI News` 섹션 확인
4. `POST /ai/news/generate` 선택
5. `Try it out` 클릭
6. 요청 JSON 입력

```json
{
  "term": "수요",
  "difficulty": "BEGINNER",
  "category": "국내"
}
```

7. `Execute` 클릭
8. 응답 코드와 JSON 필드 확인

Swagger 캡처가 필요하다면 이 화면에서 요청 body와 response body 영역을 캡처하면 된다.

## 9. 백엔드 전달 시 참고사항

- `OPENAI_API_KEY`는 AI 서버 실행 환경변수 또는 `.env`에 설정해야 한다.
- 실제 API Key는 문서, 코드, Git 저장소에 작성하지 않는다.
- AI 서버 응답 생성에는 GPT 호출 시간이 포함되므로 일반 조회 API보다 응답 시간이 길 수 있다.
- `category`는 선택값이다. 백엔드가 전달하지 않으면 AI 서버는 `term` 기준으로만 대표 뉴스를 찾는다.
- `difficulty`는 생략 가능하며 기본값은 `BEGINNER`이다.
- `quiz` 배열에는 `OX`와 `MULTIPLE_CHOICE` 문제가 포함될 수 있다.
- 프론트에서 객관식 문제를 렌더링할 때는 `type === "MULTIPLE_CHOICE"`인 경우에만 `options`를 사용한다.
- `summary`는 3개 문장 배열로 내려오므로 프론트에서는 줄 단위 리스트로 표시하기 좋다.
- `newsSummary`는 CSV에 있던 기존 요약이고, `summary`는 GPT가 새로 생성한 3줄 요약이다.

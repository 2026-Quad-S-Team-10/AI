# QuadS AI Server

뉴스 기반 경제 학습 콘텐츠를 생성하는 FastAPI 서버입니다. 경제 용어와 난이도를 입력하면 `app/data/news.csv`에서 관련 뉴스를 찾고, OpenAI API를 사용해 3줄 요약, 쉬운 용어 설명, OX 퀴즈 3문항을 반환합니다.

## 주요 기능

- 경제 용어별 대표 뉴스 조회
- 선택한 카테고리 기준 뉴스 필터링
- 뉴스 본문 기반 3줄 요약 생성
- 뉴스 맥락에 맞는 경제 용어 설명 생성
- 난이도별 OX 퀴즈 3문항 생성
- Swagger 문서를 통한 API 테스트
- Render Python Web Service 배포 설정

## 프로젝트 구조

```text
.
├── app/
│   ├── data/
│   │   └── news.csv
│   ├── main.py
│   ├── routers/
│   │   └── news_generate_router.py
│   ├── schemas/
│   │   └── news_generate_schema.py
│   └── services/
│       ├── news_generate_service.py
│       ├── news_csv_service.py
│       ├── news_preprocess_service.py
│       ├── news_summary_service.py
│       ├── keyword_explanation_service.py
│       ├── news_quiz_service.py
│       └── openai_service.py
├── docs/
│   ├── news_generate_api.md
│   ├── news_generate_api_test.md
│   └── render_deploy.md
├── tests/
│   └── test_news_generate_api.py
├── .env.example
├── render.yaml
├── requirements.txt
└── README.md
```

## 실행 환경

- Python 3.11 이상 권장
- OpenAI API Key
- `app/data/news.csv` 파일

## 설치 및 실행

1. 가상환경을 생성하고 활성화합니다.

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. 의존성을 설치합니다.

```bash
pip install -r requirements.txt
```

3. 환경변수를 설정합니다.

```bash
cp .env.example .env
```

생성된 `.env` 파일에 실제 API Key를 입력합니다.

```env
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-5.2
```

`OPENAI_MODEL`은 선택값입니다. 설정하지 않으면 코드의 기본 모델인 `gpt-5.2`를 사용합니다.

4. 서버를 실행합니다.

```bash
uvicorn app.main:app --reload
```

5. 브라우저에서 Swagger 문서를 확인합니다.

```text
http://localhost:8000/docs
```

## API 사용법

### Health Check

```http
GET /health
```

응답 예시:

```json
{
  "status": "ok"
}
```

### 뉴스 학습 콘텐츠 생성

```http
POST /ai/news/generate
```

요청 예시:

```bash
curl -X POST "http://localhost:8000/ai/news/generate" \
  -H "Content-Type: application/json" \
  -d '{"term":"수요","difficulty":"BEGINNER","category":"국내"}'
```

요청 Body:

| 필드 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `term` | `string` | 필수 | 조회할 경제 용어 |
| `difficulty` | `string` | 선택 | `BEGINNER`, `INTERMEDIATE`, `ADVANCED` 중 하나. 기본값은 `BEGINNER` |
| `category` | `string` 또는 `null` | 선택 | 뉴스 카테고리 필터 |

응답 주요 필드:

| 필드 | 설명 |
| --- | --- |
| `term` | 요청한 경제 용어 |
| `category` | 대표 뉴스 카테고리 |
| `newsTitle` | 대표 뉴스 제목 |
| `newsSummary` | CSV에 저장된 기존 뉴스 요약 |
| `newsUrl` | 뉴스 원문 URL |
| `source` | 뉴스 출처 |
| `pubDate` | 뉴스 발행일 |
| `summary` | GPT가 생성한 3줄 요약 |
| `keywordExplanation` | 뉴스 맥락에 맞춘 경제 용어 설명 |
| `quiz` | OX 퀴즈 3문항 |

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
    }
  ]
}
```

실제 응답의 `quiz` 배열에는 OX 문제가 3개 포함됩니다.

## 뉴스 CSV 형식

뉴스 데이터는 아래 위치에 있어야 합니다.

```text
app/data/news.csv
```

필수 컬럼:

| 컬럼 | 설명 |
| --- | --- |
| `term` | 경제 용어 |
| `category` | 뉴스 분야 |
| `title` | 뉴스 제목 |
| `summary` | CSV에 저장된 기존 요약 |
| `content` | 뉴스 본문 |
| `source` | 출처 |
| `url` | 뉴스 원문 URL |
| `pubDate` | 발행일 |

대표 뉴스는 `term`과 선택 `category`가 일치하는 데이터 중 `content`가 비어 있지 않은 최신 뉴스로 선택됩니다.

## 테스트

```bash
pytest
```

테스트는 API 응답 형식, 요청 검증, 퀴즈 파싱 로직 등을 확인합니다. 실제 OpenAI API 호출이 필요한 부분은 테스트에서 대체 함수로 처리합니다.

## Render 배포

이 프로젝트는 Docker가 아니라 Render의 `Python 3` Web Service로 배포합니다.

Render 설정 요약:

| 항목 | 값 |
| --- | --- |
| Runtime | `Python 3` |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| Health Check Path | `/health` |
| Required Env | `OPENAI_API_KEY` |
| Optional Env | `OPENAI_MODEL` |

저장소의 `render.yaml`을 사용하면 위 설정을 Blueprint로 관리할 수 있습니다.

배포 후 확인 경로:

```text
https://your-service-name.onrender.com/health
https://your-service-name.onrender.com/docs
https://your-service-name.onrender.com/ai/news/generate
```

자세한 배포 방법은 [docs/render_deploy.md](docs/render_deploy.md)를 참고하세요.

## 참고 문서

- [뉴스 생성 API 명세](docs/news_generate_api.md)
- [뉴스 생성 API 테스트 문서](docs/news_generate_api_test.md)
- [Render 배포 가이드](docs/render_deploy.md)

## 주의사항

- 실제 OpenAI API Key는 코드, 문서, Git 저장소에 커밋하지 않습니다.
- `.env` 파일은 로컬 실행용으로만 사용합니다.
- OpenAI API 호출이 포함되어 응답까지 시간이 걸릴 수 있습니다.
- `newsSummary`는 CSV에 저장된 기존 요약이고, `summary`는 GPT가 새로 생성한 3줄 요약입니다.

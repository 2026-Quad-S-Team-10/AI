# Render 배포 가이드

## 배포 방식

이 프로젝트는 Docker 기반 배포가 아니라 Render의 일반 `Python 3` Web Service로 배포한다.

현재 오류:

```text
failed to read dockerfile: open Dockerfile: no such file or directory
```

이 오류는 Render 서비스가 Docker runtime으로 설정되어 있는데 저장소에 `Dockerfile`이 없을 때 발생한다. 이 프로젝트에서는 `Dockerfile`을 만들지 않는다. Render에서 서비스 runtime을 `Python 3`로 선택하거나, 저장소의 `render.yaml` Blueprint를 사용해 Python Web Service로 생성해야 한다.

## Render 서비스 생성 방법

### 방법 1: Dashboard에서 직접 생성

1. Render Dashboard 접속
2. `New` -> `Web Service` 선택
3. GitHub 저장소 연결
4. Runtime 또는 Language를 `Python 3`로 선택
5. 아래 Build Command와 Start Command 입력
6. 환경변수 설정
7. Deploy 실행

### 방법 2: Blueprint 사용

저장소 루트의 `render.yaml`을 사용하면 Python Web Service 설정을 코드로 관리할 수 있다.

주의:

- 기존 Render 서비스가 Docker로 생성되어 있다면 새 Python Web Service로 다시 만들거나 runtime 설정을 Python으로 바꿔야 한다.
- Docker 배포를 선택하지 않는다.

## Build Command

```bash
pip install -r requirements.txt
```

## Start Command

이 프로젝트의 FastAPI 앱은 `app/main.py`에 있으므로 Render Start Command는 아래 값을 사용한다.

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Render는 실행 시 `PORT` 환경변수를 제공한다. 반드시 `$PORT`로 바인딩해야 외부 트래픽을 받을 수 있다.

## 필요한 환경변수

| Key | Required | Description |
| --- | --- | --- |
| `OPENAI_API_KEY` | Yes | OpenAI API 호출에 필요한 키 |
| `OPENAI_MODEL` | No | 사용할 OpenAI 모델. 기본값은 코드에서 `gpt-5.2`로 설정되어 있다. |

환경변수 설정 방법:

1. Render 서비스 상세 페이지 접속
2. `Environment` 메뉴 선택
3. `OPENAI_API_KEY` 추가
4. 값을 저장한 뒤 redeploy

실제 API Key는 코드, 문서, Git 저장소에 작성하지 않는다. 로컬 `.env` 파일도 Git에 커밋하지 않는다.

## requirements.txt 확인

현재 배포에 필요한 주요 패키지:

```text
fastapi
uvicorn
pandas
openai
python-dotenv
pydantic
```

`pytest`는 배포 실행에는 필요하지 않지만 테스트 실행을 위해 포함되어 있다.

## CSV 파일 경로

CSV 파일은 아래 경로에 포함되어 있어야 한다.

```text
app/data/news.csv
```

CSV 로딩 코드는 `pathlib.Path(__file__).resolve()` 기반으로 `app/data/news.csv`를 찾기 때문에 Render 배포 환경에서도 현재 프로젝트 구조가 유지되면 정상 동작한다.

필수 CSV 컬럼:

- `term`
- `category`
- `title`
- `summary`
- `content`
- `source`
- `url`
- `pubDate`

## Health Check

Render Health Check Path:

```text
/health
```

정상 응답:

```json
{
  "status": "ok"
}
```

## Swagger 확인

배포 후 Render에서 제공하는 URL이 아래라고 가정한다.

```text
https://your-service-name.onrender.com
```

확인 경로:

- Swagger: `https://your-service-name.onrender.com/docs`
- Health Check: `https://your-service-name.onrender.com/health`
- API Endpoint: `https://your-service-name.onrender.com/ai/news/generate`

## 배포 테스트 방법

### 1. Health Check

```bash
curl https://your-service-name.onrender.com/health
```

기대 응답:

```json
{"status":"ok"}
```

### 2. Swagger 접속

브라우저에서 아래 경로에 접속한다.

```text
https://your-service-name.onrender.com/docs
```

`POST /ai/news/generate`가 보이면 FastAPI 앱과 라우터 등록은 정상이다.

### 3. 뉴스 생성 API 테스트

```bash
curl -X POST "https://your-service-name.onrender.com/ai/news/generate" \
  -H "Content-Type: application/json" \
  -d '{"term":"수요","difficulty":"BEGINNER","category":"국내"}'
```

기대 결과:

- `200 OK`
- `term`, `newsTitle`, `newsUrl`, `summary`, `keywordExplanation`, `quiz` 포함
- `summary`는 3개 문장 배열
- `quiz`에는 OX 문제가 정확히 3개 포함됨

OpenAI API 호출이 포함되므로 응답까지 시간이 걸릴 수 있다.

## 자주 발생하는 배포 오류

### Dockerfile 오류

```text
failed to read dockerfile: open Dockerfile: no such file or directory
```

원인:

- Render 서비스가 Docker runtime으로 설정되어 있음
- 이 프로젝트에는 Dockerfile이 없고 Docker 배포를 사용하지 않음

해결:

- Render 서비스 runtime을 `Python 3`로 선택
- Build Command를 `pip install -r requirements.txt`로 설정
- Start Command를 `uvicorn app.main:app --host 0.0.0.0 --port $PORT`로 설정
- 또는 `render.yaml` Blueprint로 새 Python Web Service 생성

### OPENAI_API_KEY 누락

예상 응답:

```json
{
  "detail": "OPENAI_API_KEY environment variable is not set."
}
```

해결:

- Render Environment에 `OPENAI_API_KEY` 추가
- 저장 후 redeploy

### CSV 파일 없음

예상 응답:

```json
{
  "detail": "News CSV file was not found at ... Place the CSV file at app/data/news.csv."
}
```

해결:

- `app/data/news.csv`가 Git에 포함되어 배포되는지 확인
- 파일 경로와 대소문자 확인

## 최종 Render 설정 요약

| 항목 | 값 |
| --- | --- |
| Runtime | `Python 3` |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| Health Check Path | `/health` |
| Required Env | `OPENAI_API_KEY` |
| Swagger | `/docs` |
| Main API | `/ai/news/generate` |

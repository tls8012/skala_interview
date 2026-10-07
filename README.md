# 면접 리뷰 누적

교육생이 면접 피드백과 준비 팁을 한 곳에 모으는 작은 공유 공간입니다. 한 시즌에는 **면접 정보**와 **잡담** 두 목록이 있습니다. 글은 최신순으로 보이며, 기존 글은 일반 사용자가 수정하거나 삭제할 수 없습니다.

운영 사이트: [skala-interview.vercel.app](https://skala-interview.vercel.app/)

## 로컬 실행

외부 SaaS 계정 없이 Docker의 PostgreSQL로 실행할 수 있습니다. Node.js 20 이상, Python 3.11 이상, Docker Compose가 필요합니다.

```bash
docker compose up -d db
cp .env.example .env
python3 scripts/hash_password.py
```

마지막 명령의 출력을 `.env`의 `APP_PASSWORD_HASH` 값에 붙여 넣으세요. `SESSION_SECRET`도 긴 임의 문자열로 바꾸세요. `.env`의 값을 작은따옴표로 감싼 상태를 유지해야 `$`가 포함된 해시가 셸에서 변형되지 않습니다.

터미널 하나에서 API를 실행합니다.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
set -a
source .env
set +a
.venv/bin/uvicorn api.index:app --host 127.0.0.1 --port 8000
```

다른 터미널에서 화면을 실행합니다.

```bash
npm install
npm run dev
```

브라우저에서 `http://localhost:5173`을 엽니다. 처음 DB 볼륨을 만들 때 `db/migrations/001_initial.sql`과 로컬용 권한 설정이 자동으로 적용됩니다. 이미 생성한 볼륨에는 초기화 SQL이 다시 적용되지 않으므로, 이후 마이그레이션은 별도로 실행해야 합니다.

## 사용 방식

- 한국 시간 1월 1일과 7월 1일에 새 시즌으로 자동 전환합니다. `2026-H1`은 1~6월, `2026-H2`는 7~12월입니다.
- 과거 시즌은 읽기 전용입니다. 전체 시즌에서 검색할 수 있습니다.
- 글 번호는 전역 `bigint`이며, 본문의 `#123`은 해당 글로 이동하는 링크가 됩니다.
- 글은 50개씩 가져오고, 이후 글은 **이전 글 더 보기**로 불러옵니다.
- 빠른 연속 작성, 같은 내용 반복, 허니팟 입력, URL 과다 등은 자동 격리됩니다. 격리된 글은 일반 화면에 나타나지 않습니다.
- 일반 사용자가 기존 글을 고치는 API는 없습니다.

## Neon 연결

이 프로젝트의 운영 DB는 **Neon PostgreSQL**을 기준으로 합니다. 앱은 제한된 `app_user` 계정의 **pooled 연결**을 쓰고, 스키마 변경과 백업은 관리자 계정의 **direct 연결**을 씁니다. Neon의 Connection Details에서 두 연결의 차이를 확인할 수 있습니다. pooled 호스트에는 보통 `-pooler`가 붙습니다. [Neon 연결 풀 안내](https://neon.com/docs/connect/connection-pooling)

1. [Neon Console](https://console.neon.tech/)에서 프로젝트와 DB를 만듭니다. Vercel 함수와 가까운 지역을 선택합니다.
2. Connection Details에서 기본 관리자 역할의 **direct connection string**을 복사하여 로컬 터미널의 `ADMIN_DATABASE_URL`로만 사용합니다. 주소에 `sslmode=require`를 유지합니다.
3. 관리자 연결로 스키마를 적용합니다.

   ```bash
   psql "$ADMIN_DATABASE_URL" -v ON_ERROR_STOP=1 -f db/migrations/001_initial.sql
   ```

4. Neon SQL Editor에서 다음 SQL을 실행해 앱 전용 역할을 만듭니다. `긴_임의_비밀번호`는 실제 무작위 비밀번호로 바꿉니다. 이 역할에 관리자 역할을 부여하지 않습니다.

   ```sql
   CREATE ROLE app_user LOGIN PASSWORD '긴_임의_비밀번호';
   ```

5. 관리자 연결로 제한 권한을 적용합니다.

   ```bash
   psql "$ADMIN_DATABASE_URL" -v ON_ERROR_STOP=1 -f db/permissions.sql
   ```

6. Connection Details에서 역할을 `app_user`로 고르고 **Pooled connection**을 켜서 앱용 URL을 얻습니다. 이것이 Vercel의 `DATABASE_URL`입니다. `app_user`로 접속해 `SELECT`와 `INSERT`는 되고 `UPDATE`와 `DELETE` 권한은 없는지 확인합니다. [Neon 역할 안내](https://neon.com/docs/manage/roles)

`ADMIN_DATABASE_URL`은 로컬 관리자 작업에만 사용합니다. **Vercel 환경변수에 넣거나 Git에 저장하지 마세요.**

## Vercel 연결

1. 이 폴더를 Git 저장소로 만들어 GitHub 등에 올린 뒤 [Vercel에서 새 프로젝트](https://vercel.com/new)로 가져옵니다. Root Directory는 저장소 루트, Framework Preset은 **Vite**, Build Command는 `npm run build`, Output Directory는 `dist`입니다. `vercel.json`은 `/api/*`를 FastAPI 함수로 보냅니다. [Vercel Python/FastAPI 안내](https://vercel.com/docs/functions/runtimes/python)
2. Vercel 프로젝트의 **Settings → Environment Variables**에서 Production 환경에 다음 값을 추가합니다. 비밀번호와 연결 문자열은 **Secret** 유형으로 저장합니다. [Vercel Secret 안내](https://vercel.com/changelog/environment-variables-now-use-config-and-secret-types)

   | 이름 | 값 |
   |---|---|
   | `DATABASE_URL` | 위에서 만든 `app_user`의 Neon **pooled** URL |
   | `APP_PASSWORD_HASH` | `python3 scripts/hash_password.py` 출력 |
   | `SESSION_SECRET` | 길고 무작위인 별도 문자열 |
   | `APP_ORIGIN` | 실제 사이트의 정확한 HTTPS origin, 예: `https://example.vercel.app` |

3. Production으로 배포합니다. 배포 주소를 처음 알게 된 경우 `APP_ORIGIN`을 그 주소로 설정한 뒤 **다시 배포**합니다. 환경변수 변경은 이미 만들어진 배포에 소급 적용되지 않습니다. Preview 배포에서 로그인을 시험할 때는 해당 Preview 주소에 맞는 `APP_ORIGIN`이 필요합니다. [Vercel 환경변수 안내](https://vercel.com/docs/environment-variables)
4. 배포 후 로그인, 글 작성, 검색, 로그아웃을 확인합니다. 비로그인 상태의 `/api/notes`가 401을 돌려주는 것도 확인합니다. 실패하면 Vercel Functions 로그와 Neon 연결 상태를 확인합니다.

Python 함수는 `api/index.py`에서 시작하고 실제 라우트는 `api/auth.py`, `api/notes.py`에 있습니다. `api/db.py`는 Neon pooled 연결을 짧게 열고 닫습니다. 정적 화면 코드는 `src/components/`에 나뉘어 있습니다. 현재 운영 구성은 Vercel의 `skalalal/skala-interview` 프로젝트와 Neon의 `skala-interview` 프로젝트(`withered-fog-71863334`)입니다. 운영 비밀값은 Vercel 환경변수에만 보관합니다.

## 관리자 작업

Neon Console의 Tables에서 `notes`를 관리합니다. 잘못된 글은 `status = hidden`, 스팸으로 격리된 글 중 정상 글은 `status = visible`로 바꿉니다. `UPDATE`와 `DELETE` 전 데이터는 `notes_audit`에 기록됩니다. 개인정보를 완전히 제거해야 할 때는 감사 테이블과 백업에도 해당 내용이 남을 수 있다는 점을 확인해야 합니다.

백업 예시:

```bash
pg_dump "$ADMIN_DATABASE_URL" --format=custom --file backup.dump
```

덤프와 `.env`는 Git에 넣지 마세요. 스키마 SQL과 정기적인 DB 덤프를 함께 보관하면 다른 PostgreSQL로 옮길 수 있습니다.

공동 비밀번호가 유출되면 새 해시로 `APP_PASSWORD_HASH`를 바꾸고 `SESSION_SECRET`도 함께 바꾸세요. 후자를 바꾸면 기존 로그인 쿠키가 모두 무효화됩니다.

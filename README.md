# Telegram Keyword News Forwarder

**원하는 기능 구현**
- 연결한 소스 채널들의 새 글을 **10분마다** 확인
- **키워드에 부합하는 글만** 내가 만든 목적지 채널로 전달
- 각 소스별 **마지막 처리 메시지 ID**를 DB에 저장해서 이후 글만 가져오기
- 새 글이 없으면 아무 것도 보내지 않음
- 기본은 **포워드 모드**(미디어/포맷 유지). 권한 문제 시 `FORWARD_MODE=copy`로 텍스트 복사 전송.

## 환경 변수(.env 예시)

```
API_ID=123456
API_HASH=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
BOT_TOKEN=123456:yyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy

# @username 또는 -100... 채널 ID 가능, 콤마로 구분
SOURCE_CHANNELS=@news_source1,@news_source2,-1001234567890

# 내가 만든 채널(봇을 admin으로 추가해야 읽기/쓰기 가능)
TARGET_CHANNEL=@my_target_channel

# 포함 키워드(소문자/대문자 구분 없음), 콤마/줄바꿈 모두 가능
KEYWORDS=EV, 전해액, 동화, SK On

# 선택값
POLL_INTERVAL=600
DB_PATH=/app/data/state.sqlite
FORWARD_MODE=forward   # forward | copy
ADD_HEADER=true        # copy 모드에서 헤더 표시
```

> **중요:** 소스/타겟 채널 모두에 **봇을 초대하고 관리자 권한**을 주세요. 대부분의 채널은 봇이 admin이 아니면 읽기/포워드가 제한됩니다.

## 로컬 실행

```bash
pip install -r requirements.txt
export $(grep -v '^#' .env | xargs)  # 또는 python-dotenv 사용
python -m app.main
```

## Docker

```bash
docker build -t keyword-forwarder .
docker run -it --rm --env-file .env keyword-forwarder
```

Railway/Render/Heroku에서도 동일하게 `.env` 값만 지정하면 됩니다.

## 로그

- 새 글이 없으면: `no new matching posts.`
- 처리 후 체크포인트: `updated last_id -> ...`
- 권한 문제: `Bot needs to be admin/member...`

## 동작 요약

1. 각 소스 채널 별 DB에서 `last_id` 읽기
2. `min_id=last_id`로 **그 이후** 메시지 가져오기
3. `KEYWORDS` 포함 여부로 필터(본문/캡션 기준)
4. 일치하는 것만 `TARGET_CHANNEL`로 **포워드**(또는 **복사**)
5. 처리한 최대 메시지 ID를 저장 → 다음 사이클에서 **그 이후만** 처리
6. 10분마다 반복
```


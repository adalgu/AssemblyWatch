# Assembly Watch

Assembly Watch는 국회 영상을 실시간으로 모니터링하고, 트랜스크립트를 생성한 후 요약 리포트를 제공하는 Python 프로젝트입니다.

## 주요 기능

1. **실시간 국회 영상 모니터링 (assembly_watch.py)**

   - 생방송 및 녹화방송 모니터링
   - 자동 자막 추출 및 저장
   - 키워드 알림 기능

2. **트랜스크립트 요약 및 리포트 생성 (report_generator.py)**
   - LangChain과 OpenAI를 이용한 RAG(Retrieval-Augmented Generation) 기반 요약
   - 회의 내용 요약 및 잠재적 리스크 평가

## 설치 방법

1. 이 저장소를 클론합니다:

   ```
   git clone https://github.com/your-username/assembly-watch.git
   cd assembly-watch
   ```

2. 필요한 패키지를 설치합니다:

   ```
   pip install -r requirements.txt
   ```

3. `.env` 파일을 생성하고 필요한 환경 변수를 설정합니다:
   ```
   NOTION_API_KEY=your_notion_api_key
   NOTION_PAGE_ID=your_notion_page_id
   SLACK_ALERT_WEBHOOK=your_slack_webhook_url
   SLACK_TOKEN=your_slack_token
   SLACK_CHANNEL_ID=your_slack_channel_id
   OPENAI_API_KEY=your_openai_api_key
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token
   TELEGRAM_CHAT_ID=your_telegram_chat_id
   ```

## 사용 방법

### 1. 국회 영상 모니터링 (assembly_watch.py)

1. 다음 명령어로 스크립트를 실행합니다:

   ```
   python assembly_watch.py
   ```

2. 생방송 또는 녹화방송을 선택합니다.

3. 알림을 받을 키워드를 설정합니다.

4. 모니터링이 시작되며, 자동으로 자막이 추출되어 저장됩니다.

### 2. 요약 리포트 생성 (report_generator.py)

1. 다음 명령어로 스크립트를 실행합니다:

   ```
   python report_generator.py
   ```

2. 데이터베이스에서 세션을 선택하거나, 트랜스크립트 파일을 선택합니다.

3. 요약 리포트가 생성되어 'reports' 폴더에 저장됩니다.

## 주의사항

- 이 프로젝트는 교육 및 연구 목적으로만 사용해야 합니다.
- 저작권 및 개인정보 보호와 관련된 법규를 준수해야 합니다.
- API 키와 토큰은 안전하게 관리하세요.

## 기여 방법

1. 이 저장소를 포크합니다.
2. 새 브랜치를 생성합니다 (`git checkout -b feature/AmazingFeature`).
3. 변경사항을 커밋합니다 (`git commit -m 'Add some AmazingFeature'`).
4. 브랜치에 푸시합니다 (`git push origin feature/AmazingFeature`).
5. Pull Request를 생성합니다.

## 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 `LICENSE` 파일을 참조하세요.

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

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

## 향후 개발 방향

Assembly Watch 프로젝트는 계속해서 발전하고 있으며, 다음과 같은 영역에서 개선과 확장을 계획하고 있습니다:

1. **음성 인식 정확도 향상**

   - 다양한 음성 인식 API 및 모델 비교 평가
   - 한국어 특화 음성 인식 모델 도입 검토

2. **실시간 분석 기능 강화**

   - 키워드 기반 알림 외에도 감정 분석, 주제 모델링 등 고급 분석 기능 추가
   - 실시간 대시보드를 통한 회의 동향 시각화

3. **다국어 지원**

   - 영어, 중국어 등 주요 외국어 지원으로 국제 회의 모니터링 가능

4. **AI 기반 요약 개선**

   - 최신 언어 모델 및 요약 알고리즘 적용
   - 사용자 피드백을 반영한 요약 품질 개선 시스템 구축

5. **사용자 인터페이스 개발**

   - 웹 기반 대시보드 구현으로 사용 편의성 향상
   - 모바일 앱 개발을 통한 접근성 개선

6. **데이터 저장 및 검색 고도화**

   - 효율적인 데이터베이스 구조 설계로 검색 속도 개선
   - 전문 검색 엔진 도입으로 복잡한 쿼리 처리 가능

7. **보안 강화**

   - 엔드투엔드 암호화 적용으로 데이터 보안 강화
   - 사용자 인증 및 권한 관리 시스템 구축

8. **확장성 개선**

   - 마이크로서비스 아키텍처 도입 검토
   - 클라우드 네이티브 환경으로의 마이그레이션 계획

9. **커뮤니티 기여 활성화**

   - 오픈소스 기여 가이드라인 개선
   - 정기적인 컨트리뷰터 미팅 및 해커톤 개최 계획

10. **법적 검토 및 준수**
    - 저작권 및 개인정보 보호 관련 법률 검토
    - 필요시 관련 기관과의 협력 체계 구축

이러한 향후 개발 방향은 프로젝트의 발전과 함께 지속적으로 업데이트될 예정입니다. 여러분의 아이디어와 제안을 환영합니다!

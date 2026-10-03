# Parser 실행 및 연결

이 패키지는 실행 가능한 Python Playwright parser와 선택적 stdio MCP 서버 소스를 포함한다. 계정에 저장하는 것만으로 서버가 실행되거나 ChatGPT MCP 연결이 생성되지는 않는다. 실제 연결이 없는 상태에서 연결 완료라고 보고하지 않는다.

실행 환경에서 `python -m pip install playwright mcp`, `python -m playwright install chromium`을 실행한다. CLI는 `python scripts/parser.py <URL>`, stdio MCP 서버는 `python scripts/parser.py --mcp`이다. 경로는 이 스킬 디렉터리 기준이며 설치 위치에 맞게 절대 경로로 해석한다.

공개 채용페이지의 렌더링 DOM, 최대 20개 iframe, JSON-LD, 긴 이미지와 PDF 링크를 반환한다. 자동 OCR 및 PDF 본문 추출은 포함하지 않는다. 반환된 이미지/PDF를 사용 가능한 시각/PDF 도구로 읽고 미확인 자료가 있으면 PARTIAL을 유지한다. COMPLETE는 모델이 실제 본문의 각 영역과 공고 동일성을 검증한 뒤에만 부여한다.

사이트별 인증·CAPTCHA를 우회하지 않는다. 로그인 세션을 복사하거나 지원하기 버튼을 누르지 않는다. 원문 네트워크 정책 때문에 차단되면 FAILED 또는 PARTIAL로 보고하고 기존 검색 폴백을 사용한다.

원격 MCP로 서비스하려면 별도의 브라우저 실행 서버, 인증, 요청 제한, 격리 및 네트워크 계층의 사설 주소 차단이 필요하다. 이 stdio 구현을 인증 없는 공개 HTTP 서버로 그대로 노출하지 않는다. Sites Worker에는 이 Playwright 프로세스를 그대로 배포할 수 없다. 실제 endpoint가 준비되기 전에는 mcp.json에 임의 URL을 넣지 않는다.

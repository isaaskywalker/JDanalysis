# 회사별 이력서 DOCX 생성

fit 평가 후 사용자가 이력서 수정을 요청하거나, 분석과 수정본 생성을 함께 요청했으면 이 절차를 수행한다. 공고 분석만 요청했으면 결과 뒤에 DOCX 생성 여부를 제안한다. 이 대화에서 생성까지 이미 요청했으면 다시 확인하지 않는다.

## 실행 계약

1. 기준 이력서를 직접 읽고 텍스트를 `results/<회사>/<실행일>/source.txt`로 추출한다. PDF의 표·페이지와 스캔 자료도 확인한다. `source.txt`에 JD나 추정 사실을 섞지 않는다.
2. JD를 COMPLETE로 확보하고 fit 비교를 먼저 수행한다. 필수 미충족 사항을 문구 수정으로 감추지 않는다. 이력서가 읽히지 않거나 JD가 PARTIAL/FAILED이면 최종 수정본 생성은 보류한다.
3. 검증된 원문 범위에서 회사 용어로 표현을 바꾼다. 숫자·기간·도구·책임·성과·경력은 추가하거나 부풀리지 않는다. 필요한 사실은 검증 질문으로 남기고 DOCX 본문에 미확인 주장을 넣지 않는다.
4. 아래 계약으로 `plan.json`을 작성한다. 새 경력 도입과 원문 항목 삭제는 명시적 요청이 없으면 하지 않는다. rebuild에서는 모든 원문 섹션을 반영하고 생략이 있다면 변경내역 review_notes에 이유를 밝힌다.
5. 운영체제에 맞는 가상환경 Python으로 `scripts/resume_docx.py --plan <plan.json> --source-text <source.txt> --output-dir <새 결과 폴더>`를 실행한다. 이미 결과가 있으면 새 폴더를 사용한다.
6. 생성 DOCX를 다시 읽고 원문·JD와 대조한다. 자동 근거·숫자 검사는 의미 검증을 대신하지 않으므로 책임 범위, 누락, 인과 표현도 직접 확인한다.
7. 문서 렌더링 도구가 있으면 페이지 이미지로 변환해 모든 페이지의 글자 깨짐·넘침·표·페이지 나눔을 확인한다. 없으면 시각 검증 미완료를 사용자에게 알리고 Word에서 열어 확인할 것을 안내한다. read-back만으로 시각 검증 완료라고 주장하지 않는다.
8. DOCX와 변경내역의 실제 로컬 경로를 제공한다. 원본은 유지하고 연락처나 상세 이력을 Git에 커밋하지 않는다. source.txt와 plan.json도 results/ 안에만 저장한다.

## 모드

- `patch`: DOCX 원본의 문단·표·페이지 설정을 유지한다. 수정 대상 문단을 exact before로 지정한다. 동일 문단이 여러 곳이면 중단한다. 하이퍼링크·그림·필드가 있는 문단은 자동 수정하지 않는다. 첫 run 서식으로 문구를 치환하므로 혼합 서식과 페이지 나눔은 별도 검토한다. 경험 순서 재배치는 지원하지 않는다.
- `rebuild`: 원문 내용을 Letter 세로 DOCX로 재구성한다. 기본 글꼴은 Windows Malgun Gothic, macOS Apple SD Gothic Neo, Linux Noto Sans CJK KR이며 설치 환경에 따라 대체될 수 있다. 섹션·항목 순서는 계획에 따른다. PDF·이미지 디자인을 복제하지 않는다. DOCX 원본에서도 큰 구조 변경이 필요하면 이 모드와 디자인 재구성 사실을 알린다.

## 계획 구조

공통 필드: company, position, jd_url, jd_status(COMPLETE), source_resume(실제 절대 경로), mode, review_notes(배열).

rebuild에는 candidate_name, contact(원문에 존재하는 연락처 줄 배열), sections(heading, items)를 넣는다. 각 item에는 text, evidence(원문에 정확히 존재하는 인용 배열), source_ref(페이지·섹션), reason, bullet(선택)을 넣는다.

patch에는 edits 배열을 넣는다. 각 edit에는 before(기존 문단 전체), after, evidence, source_ref, reason을 넣는다. 빈 문자열·근거 미일치·근거에 없는 숫자는 거부된다.

```json
{
  "company": "예시 회사",
  "position": "AI PM",
  "jd_url": "https://example.com/job",
  "jd_status": "COMPLETE",
  "source_resume": "/absolute/path/resume.docx",
  "mode": "patch",
  "edits": [{
    "before": "LLM 모델 비교와 평가 기준 설계",
    "after": "LLM 평가 기준 설계 및 모델 비교",
    "evidence": ["LLM 모델 비교와 평가 기준 설계"],
    "source_ref": "1쪽 프로젝트",
    "reason": "공고에서 강조한 평가 기준 설계를 먼저 표현"
  }],
  "review_notes": []
}
```

새 숫자는 보수적으로 차단한다. 기간으로부터 연차를 계산하는 등 원문 숫자의 변환이 필요하면 스크립트에서 우회하지 말고 근거와 계산을 확인한 뒤 지원자에게 검토를 요청한다.

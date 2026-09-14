# clipboard_watcher — 클립보드 감시 및 자동 저장

## 개요

사용자가 종료할 때까지 백그라운드에서 클립보드를 감시하다가, 클립보드 내용의
**1행 1열이 JSON 메타데이터**이면 나머지 내용(쿼리 결과 / 텍스트)을 지정된
방식으로 파일에 저장한다.

주 사용 시나리오: DB 쿼리 툴(Oracle)에서 SQL 실행 → 결과를 클립보드로 복사 →
본 스크립트가 자동으로 감지해서 txt 또는 xlsx로 저장.

---

## JSON 메타데이터 스키마

Oracle alias(식별자) 길이 제한(구버전 30바이트) 안에서도 안전하도록 키를 축약한다.
저장 폴더는 `.env`(`OUTPUT_DIR`)에 고정해두고, `rf`에는 **파일명만** 넣어 alias 길이를 최소화한다.

| 축약 키 | 원래 의미 | 설명 |
|---|---|---|
| `fn` | function | 저장 형식. `"save_text"` \| `"save_excel"` (3단계용 값은 추후 정의) |
| `md` | mode | 중복 처리 방식. `"save"`(기본값, 생략 가능) \| `"update"` \| `"delete"` |
| `rf` | result_file_name | 결과 파일의 **파일명만** (경로/확장자 제외). `.env`의 `OUTPUT_DIR`과 조합 |
| `of` | origin_file_name | (3단계 전용, 현재 미사용) 서식 복사용 샘플 파일 경로 |
| `ft` | file_type | 파일 확장자. `"txt"` \| `"xlsx"` — 저장 방식 분기 기준이자 확장자로 그대로 사용 |

최종 저장 경로 = `OUTPUT_DIR + "/" + rf + "." + ft`

예시:
```json
{"fn":"save_excel","rf":"q1","ft":"xlsx"}
```
→ 약 42자, `md` 생략 시 `"save"`로 동작. Oracle 30바이트 alias 제한에도 여유 있음.

### `md`(중복 처리 모드) 동작
| 값 | 파일이 이미 존재할 때 | 파일이 없을 때 |
|---|---|---|
| `save` (기본값) | **저장하지 않고 스킵** (로그만 남김) | 새로 저장 |
| `update` | 덮어쓰기 | 새로 저장 |
| `delete` | 해당 경로 파일 삭제 (데이터 본문은 무시) | 삭제할 파일 없음 → 로그만 남기고 스킵 |

---

## 클립보드 파싱 규칙 (1·2단계 공통)

1. 클립보드 텍스트를 줄바꿈(`\n`) 기준으로 분리
2. 1번째 줄을 탭(`\t`) 기준으로 분리, 첫 번째 필드를 `json.loads()` 시도
3. 파싱 성공 + `fn`/`ft` 키 존재 → 트리거 발동
4. 파싱 실패 → 무시하고 계속 감시 (에러 로그 없음, 일반 클립보드 복사와 구분 안 되므로 조용히 스킵)

### 1단계 (txt) 클립보드 예시
```
{"fn":"save_text","rf":"C:/out/query1","of":"","ft":"txt"}
SELECT * FROM table
WHERE ...
```
- 1행 전체 = 메타 JSON
- 2행부터 끝까지 = 저장할 텍스트 원본 그대로

### 2단계 (xlsx) 클립보드 예시 (Oracle 쿼리 툴에서 "헤더 포함 복사")
```
{"fn":"save_excel","rf":"C:/out/q1","of":"","ft":"xlsx"}\tNAME\tAGE
Alice\t30
Bob\t25
```
SQL 예시:
```sql
SELECT '{"fn":"save_excel","rf":"C:/out/q1","of":"","ft":"xlsx"}' AS "..meta",
       NAME, AGE
FROM some_table;
```
- 1행 1열 = 메타 JSON (alias 자리)
- 1행 2열부터 = 실제 엑셀 헤더로 사용 (NAME, AGE)
- 2행부터 = 실제 데이터, **단 1열(meta 자리)은 버리고 2열부터 저장**

---

## 모듈 구조

`모듈별로 나눠서 구현` 요청에 따라 기능 단위로 파일을 분리한다 (클래스/불필요한 추상화 없이 함수 단위로만 분리).

```
scripts/clipboard_watcher/
├── watcher.py       # 클립보드 폴링 루프, 진입점 (if __name__ == "__main__")
├── parser.py        # 클립보드 텍스트 → (meta dict, data) 분리
├── savers.py        # save_text(), save_excel() — fn 값에 따라 분기 호출
└── excel_style.py   # 엑셀 기본 서식 전용 (savers.py와 분리)
```

> **개발/실행 환경 차이**: 코드는 Linux에서 작성하지만 실제 실행은 Windows에서 한다.
> `pathlib.Path`로 경로를 다뤄 OS 경로 구분자 문제를 피하고, `pyperclip`은 Windows에서는
> 별도 설정 없이 동작하지만 Linux 개발 환경에서는 `xclip`/`xsel`이 없으면 클립보드 접근이
> 안 될 수 있어 `parser.py`/`savers.py` 단위 테스트는 실제 클립보드 대신 문자열을 직접
> 넣어서 검증한다.

- **watcher.py**: `pyperclip`으로 `POLL_INTERVAL`(기본 3초) 간격 폴링, 이전 값과 다르면 `parser.py` 호출 → 트리거되면 `savers.py` 호출. 부하를 낮게 유지하기 위해 짧은 간격 사용하지 않음. Ctrl+C로 종료.
- **parser.py**: 위 "클립보드 파싱 규칙"을 함수 1~2개로 구현 (`parse_clipboard(text) -> (meta, data) | None`)
- **savers.py**: `fn` 값(`save_text` / `save_excel`)으로 형식을 분기하고, `md` 값(`save`/`update`/`delete`)으로 중복 처리를 분기해서 저장/삭제 함수 호출. `save_excel`은 `openpyxl` 사용, 기본 셀 서식(스타일링 없음) 그대로 저장.
- **logger 처리**: 별도 모듈 없이 `watcher.py`에서 액션 완료 시 한 줄 콘솔 로그 출력 (`[시각] MODE 경로 lines=N` 형식)

---

## 단계별 구현 계획

### 1단계 — 텍스트 저장 (`save_text`)
- [x] `.env` 로드 처리 (`OUTPUT_DIR`, `POLL_INTERVAL`), `python-dotenv` 사용
- [x] `parser.py`: 클립보드 1행 1열 JSON 파싱 + 나머지 텍스트 추출
- [x] `savers.py`: `save_text(meta, data)` — `OUTPUT_DIR + rf + "." + ft` 경로 기준으로 `md`(save/update/delete)에 따라 저장·덮어쓰기·삭제·스킵 처리, 처리 결과(경로, 라인 수) 반환
- [x] `watcher.py`: 폴링 루프(기본 3초) + 트리거 시 `save_text` 호출 + 결과 한 줄 로그 출력
- [x] 직접 실행 테스트: 임의의 텍스트로 save/update/delete/스킵 각각 확인 (scratchpad에서 함수 직접 호출로 검증 완료)

### 2단계 — 엑셀 저장 (`save_excel`)
- [x] `parser.py` 확장: 1행 2열부터를 헤더로, 2행부터 1열 제외 나머지를 데이터로 분리
- [x] `savers.py`: `save_excel(meta, headers, rows)` — `openpyxl`로 헤더 1행 + 데이터 작성. `md`에 따른 저장/덮어쓰기/삭제/스킵은 1단계와 동일 로직 공유
- [x] `excel_style.py`: 기본 서식 전용 모듈 — 전체 셀 텍스트 서식(`number_format='@'`) 적용 + 컬럼 폭을 해당 컬럼 값 길이에 맞춰 자동 조정. `savers.py`가 저장 직후 호출
- [x] 임의의 xlsx 테스트 케이스로 직접 실행 검증 (텍스트 서식 유지 확인: `"007"`이 숫자로 안 바뀜, 컬럼 폭 값 길이에 맞게 자동 조정 확인)

> **참고**: Linux 개발 환경에는 `xclip`/`xsel`이 없어 `pyperclip.paste()`로 실제 클립보드를
> 읽는 통합 테스트는 이 환경에서 불가능했다. 대신 `parser.parse_clipboard()` /
> `savers.save()`를 문자열 입력으로 직접 호출해서 검증했다. Windows 실행 환경에서는
> `pyperclip`이 별도 패키지 설치 없이 클립보드에 바로 접근 가능하므로 실사용 시
> 문제 없음. 실제 Oracle 쿼리 툴에서의 "헤더 포함 복사" 동작은 Windows 환경에서
> 별도로 확인 필요.

### 3단계 — 샘플 파일 기반 양식 채우기 (TODO, 현재 미구현)
- [ ] `of`(origin_file_name)로 지정된 샘플 파일을 복사
- [ ] 쿼리 결과 값을 읽어서 시트/행/열을 찾아 해당 위치에 값 채우기
- [ ] 시트/행/열을 어떻게 지정할지(추가 메타 키 필요 여부) 별도 설계 필요 — **지금은 설계하지 않음**

### 남은 TODO (다음 작업 시작점)
- [ ] **3단계 구현**: 위 항목대로 설계 먼저 진행 (승인 대기) 후 구현
- [ ] **코드 품질 검토**: 1·2단계 구현 코드(`parser.py`/`savers.py`/`excel_style.py`/`watcher.py`) 대상으로 테스트를 진행하며 코드 품질 검토 (`/code-review` 등 활용). 지금까지는 scratchpad에서 함수 직접 호출로만 검증했고, 정식 테스트 코드나 리뷰는 아직 안 함

---

## 실행 방식

- Anaconda `web` 환경에서 `python scripts/clipboard_watcher/watcher.py` 로 직접 실행
- 종료: 터미널에서 Ctrl+C
- 에러 핸들링은 최소화: JSON 파싱 실패/파일 쓰기 실패 시 콘솔에 한 줄 로그만 출력하고 계속 감시
- 처리 완료 시 콘솔에 한 줄 로그 출력, 형식: `[YYYY-MM-DD HH:MM:SS] {SAVE|UPDATE|DELETE|SKIP} {경로} lines={N}`

---

## `.env` 설정

```
OUTPUT_DIR=C:/reports/2026
POLL_INTERVAL=3
```
- `OUTPUT_DIR`: 결과 파일이 저장될 고정 폴더
- `POLL_INTERVAL`: 클립보드 폴링 간격(초), 기본 3초. 자주 쓰는 기능이 아니므로 낮은 부하 우선, 필요 시 조정

---

## requirements.txt 추가 필요 패키지
- `pyperclip`
- `openpyxl`
- `python-dotenv`

---

## 확정된 사항 (기록용)
1. `fn` 값: `save_text` / `save_excel` 그대로 확정
2. `md` 생략 시 기본값 `"save"` 동작 확정

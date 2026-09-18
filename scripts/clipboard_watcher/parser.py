"""클립보드 텍스트를 메타(JSON) + 데이터로 분리하는 모듈."""

import json

# DB 그리드에서 '헤더 포함 복사'를 했을 때 1행 1열에 들어오는 컬럼명
HEADER_MARKER = "header"


def parse_clipboard(text: str):
    """클립보드 텍스트의 1행 1열이 JSON 메타데이터인지 확인하고 분리한다.

    트리거 조건(JSON 파싱 성공 + fn/ft 키 존재)을 만족하지 않으면 None 반환.
    '!'로 시작하거나, 2행 이후에 값이 없으면(delete 제외) None 반환.

    단, 1행 1열이 'header'면 DB의 '헤더 포함 복사'로 컬럼명 행이 앞에 붙은
    것으로 보고 해당 행을 버린 뒤 2행부터 기존 형식으로 처리한다(save_excel 전용).

    반환: (meta: dict, payload: dict)
    """
    if not text:
        return None

    lines = text.split("\n")

    header_row_skipped = lines[0].rstrip("\r").split("\t")[0].strip().lower() == HEADER_MARKER
    if header_row_skipped:
        lines = lines[1:]
        if not lines:
            return None

    first_line = lines[0].rstrip("\r")
    if first_line.startswith("!"):
        return None

    fields = first_line.split("\t")

    try:
        meta = json.loads(fields[0])
    except ValueError:
        return None

    # JSON이지만 dict가 아닌 값(숫자·문자열·배열 등)이 올 수 있다
    if not isinstance(meta, dict):
        return None

    if "fn" not in meta or "ft" not in meta:
        return None

    fn = meta["fn"]

    # 헤더 행을 건너뛴 형식은 save_excel에서만 허용
    if header_row_skipped and fn != "save_excel":
        return None

    # delete는 데이터가 필요 없으므로 빈 데이터 검사에서 제외
    if meta.get("md") != "delete" and "".join(lines[1:]).strip() == "":
        return None

    if fn == "save_text":
        data = "\n".join(line.rstrip("\r") for line in lines[1:])
        return meta, {"data": data}

    if fn == "save_excel":
        headers = fields[1:]
        rows = []
        for line in lines[1:]:
            line = line.rstrip("\r")
            if line == "":
                continue
            cols = line.split("\t")
            rows.append(cols[1:])  # 1열(meta 자리)은 제외
        return meta, {"headers": headers, "rows": rows}

    return None

"""클립보드 텍스트를 메타(JSON) + 데이터로 분리하는 모듈."""

import json


def parse_clipboard(text: str):
    """클립보드 텍스트의 1행 1열이 JSON 메타데이터인지 확인하고 분리한다.

    트리거 조건(JSON 파싱 성공 + fn/ft 키 존재)을 만족하지 않으면 None 반환.
    반환: (meta: dict, payload: dict)
    """
    if not text:
        return None

    lines = text.split("\n")
    first_line = lines[0].rstrip("\r")
    fields = first_line.split("\t")

    try:
        meta = json.loads(fields[0])
    except json.JSONDecodeError:
        return None

    if "fn" not in meta or "ft" not in meta:
        return None

    fn = meta["fn"]

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

"""fn/md 값에 따라 실제 저장(txt/xlsx)·덮어쓰기·삭제·스킵을 처리하는 모듈."""

from pathlib import Path

import openpyxl

from excel_style import apply_default_style


def resolve_path(meta: dict, output_dir: str) -> Path:
    return Path(output_dir) / f"{meta['rf']}.{meta['ft']}"


def save_text(meta: dict, payload: dict, output_dir: str):
    path = resolve_path(meta, output_dir)
    md = meta.get("md", "save")

    if md == "delete":
        if path.exists():
            path.unlink()
            return "DELETE", path, 0
        return "SKIP", path, 0

    if md == "save" and path.exists():
        return "SKIP", path, 0

    data = payload["data"]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(data, encoding="utf-8")
    lines = len(data.splitlines())
    action = "UPDATE" if md == "update" else "SAVE"
    return action, path, lines


def save_excel(meta: dict, payload: dict, output_dir: str):
    path = resolve_path(meta, output_dir)
    md = meta.get("md", "save")

    if md == "delete":
        if path.exists():
            path.unlink()
            return "DELETE", path, 0
        return "SKIP", path, 0

    if md == "save" and path.exists():
        return "SKIP", path, 0

    headers = payload["headers"]
    rows = payload["rows"]

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(headers)
    for row in rows:
        ws.append(row)
    apply_default_style(ws)

    path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(path)
    action = "UPDATE" if md == "update" else "SAVE"
    return action, path, len(rows)


def save(meta: dict, payload: dict, output_dir: str):
    """fn 값에 따라 save_text / save_excel로 분기."""
    fn = meta.get("fn")
    if fn == "save_text":
        return save_text(meta, payload, output_dir)
    if fn == "save_excel":
        return save_excel(meta, payload, output_dir)
    return None

"""엑셀 기본 서식 전용 모듈 (savers.py와 분리)."""


def apply_default_style(ws):
    """전체 셀을 텍스트 서식으로 지정하고, 컬럼 폭을 값 길이에 맞춰 조정한다."""
    for row in ws.iter_rows():
        for cell in row:
            cell.number_format = "@"

    for col_cells in ws.columns:
        col_letter = col_cells[0].column_letter
        max_len = 0
        for cell in col_cells:
            value_len = len(str(cell.value)) if cell.value is not None else 0
            max_len = max(max_len, value_len)
        ws.column_dimensions[col_letter].width = max_len + 2

# test/test_llm_flow.py

import os
from openpyxl import Workbook
from app.main_processor import process_file_and_map

def create_sample_xlsx(file_path: str, rows: int = 10):
    """
    rows行の簡易XLSXを生成 (シート1枚)。
    1行目は見出しっぽく "顧客名" など入れる例。
    """
    wb = Workbook()
    ws = wb.active
    ws.title = "SingleSheet"

    # 1行目 (見出しっぽい)
    ws.append(["顧客名", "住所", "電話番号"])

    # 残りの行
    for i in range(rows - 1):
        ws.append([f"Company{i}", f"Address{i}", f"Tel{i}"])

    wb.save(file_path)

def test_flow_basic():
    """
    シンプルな10行程度のファイルを生成し、ヘッダー判定→マッピングを行う。
    結果をプリントし、成功かどうか確認する。
    """
    test_file = "test/data/test_sample.xlsx"
    create_sample_xlsx(test_file, rows=10)

    result = process_file_and_map(test_file)
    print("[test_flow_basic] result =", result)

    if result["status"] == "success":
        print("  => PASSED (assuming LLM responded with valid JSON)")
    else:
        print("  => FAILED or partially failed")

def test_flow_no_header():
    """
    ヘッダーらしき行が無いケースをテストする。
    先頭行にも数値などを入れ、LLMがどう判定するか試す。
    """
    test_file = "test/data/test_no_header.xlsx"
    wb = Workbook()
    ws = wb.active
    ws.title = "SingleSheet"

    for i in range(10):
        ws.append([i, f"Data{i}", f"Value{i}"])

    wb.save(test_file)

    result = process_file_and_map(test_file)
    print("[test_flow_no_header] result =", result)

    if result["status"] == "success":
        print("  => PASSED")
    else:
        print("  => FAILED")

def run_all_tests():
    print("===== Start LLM Flow Tests =====")
    test_flow_basic()
    test_flow_no_header()
    print("===== End LLM Flow Tests =====")

if __name__ == "__main__":
    run_all_tests()

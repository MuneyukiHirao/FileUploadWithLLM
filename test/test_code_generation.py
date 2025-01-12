# test/test_code_generation.py
import os
import json
from pathlib import Path
from openpyxl import Workbook
from app.code_generation import generate_and_run_code

def test_flow_code_generation():
    """
    1) テスト用のマッピング情報とrow_dataを用意。
    2) 変換前のデータを XLSX に保存 (before_transform.xlsx)。
    3) app.code_generation.generate_and_run_code() を呼び出し、戻り値をJSONファイルに保存。
    """
    # テスト用マッピング情報（必須項目が全部揃っている例）
    mapping_info = [
        {"columnIndex": 0, "columnName": "顧客コード", "matchedField": "distributorCode", "confidence": 0.9},
        {"columnIndex": 1, "columnName": "顧客名", "matchedField": "CustomerName", "confidence": 0.95},
        {"columnIndex": 2, "columnName": "アカウント番号", "matchedField": "AccountNumber", "confidence": 0.88},
        {"columnIndex": 3, "columnName": "ランク", "matchedField": "Rank", "confidence": 0.5},
    ]

    # テスト用rowData
    row_data = [
        ["D001", "株式会社ABC", "AC123", "A"],
        ["D002", "株式会社XYZ", "AC999", "B"],
    ]

    # (1) 変換前のデータを XLSXに保存
    output_xlsx_path = Path("test/data/before_transform.xlsx")
    output_xlsx_path.parent.mkdir(parents=True, exist_ok=True)
    wb = Workbook()
    ws = wb.active
    
    # 適宜、ヘッダーを入れるならここで追加してもOK
    # 例: ws.append(["顧客コード", "顧客名", "アカウント番号", "ランク"])
    
    for row in row_data:
        ws.append(row)
    wb.save(output_xlsx_path)
    print(f"[test_flow_code_generation] Saved before_transform file => {output_xlsx_path}")

    # (2) generate_and_run_code を呼び出して変換実施
    result = generate_and_run_code(mapping_info, row_data)

    # 結果を表示
    print("[test_flow_code_generation] result =", result)

    # (3) 戻り値を test/data/transformed_data.json に保存
    output_json_path = Path("test/data/transformed_data.json")
    output_json_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"[test_flow_code_generation] Saved transformed data => {output_json_path}")

    # テスト用の簡易判定
    if result.get("status") == "success":
        print("  => PASSED")
    else:
        print("  => FAILED")


if __name__ == "__main__":
    test_flow_code_generation()


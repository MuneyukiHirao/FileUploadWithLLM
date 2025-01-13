# app/main_processor.py

from app.file_to_json import convert_xlsx_to_json
from app.llm_api import call_header_detection, call_mapping

def process_file_and_map(file_path: str) -> dict:
    """
    1. XLSX/CSV/JSONファイルを100行まで読み込み
    2. ChatGPTでヘッダー判定
    3. ChatGPTでマッピング提案
    4. 結果を返す
    """
 
    result = convert_xlsx_to_json(file_path, limit_rows=True)
    if result["status"] != "success":
        return result
    
    rowData = result.get("rowData", [])
    fileType = result.get("fileType", "unknown")

    # ヘッダー判定
    header_response = call_header_detection({"fileType": fileType, "rowData": rowData})
    if header_response.get("status") == "error":
        return {
            "status": "error",
            "message": "ヘッダー判定に失敗しました",
            "details": header_response
        }

    header_info = header_response.get("headerDetection", {})
    header_index = header_info.get("headerRowIndex", -1)

    mapping_response = call_mapping({
        "fileType": fileType,
        "headerRowIndex": header_index,
        "rowData": rowData
    })
    if mapping_response.get("status") == "error":
        return {
            "status": "error",
            "message": "マッピング提案に失敗しました",
            "details": mapping_response
        }

    # 先頭3行をサンプルデータとして返す (ヘッダー行も含む)
    sample_rows = rowData[:3]

    return {
        "status": "success",
        "headerResponse": header_response,
        "mappingResponse": mapping_response,
        "rowData": rowData  # ★ ここでrowDataを含める
    }


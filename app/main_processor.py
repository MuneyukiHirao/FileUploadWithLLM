# app/main_processor.py

from app.file_to_json import convert_xlsx_to_json
from app.llm_api import call_header_detection, call_mapping

def process_file_and_map(file_path: str) -> dict:
    """
    1. XLSXファイルを先頭100行だけJSON化
    2. ChatGPTにヘッダー判定してもらう
    3. ChatGPTにマッピング提案してもらう
    4. 結果をまとめて返す
    """

    # (1) XLSXファイルをJSON化
    result = convert_xlsx_to_json(file_path)
    if result["status"] != "success":
        return result  # エラー情報をそのまま返す

    rowData = result.get("rowData", [])
    fileType = result.get("fileType", "unknown")

    # (2) ヘッダー判定 (LLM)
    header_request = {
        "fileType": fileType,
        "rowData": rowData
    }
    header_response = call_header_detection(header_request)
    if header_response.get("status") == "error":
        return {
            "status": "error",
            "message": "ヘッダー判定に失敗しました",
            "details": header_response
        }

    header_info = header_response.get("headerDetection", {})
    is_header = header_info.get("isHeaderPresent", False)
    header_index = header_info.get("headerRowIndex", -1)
    reason = header_info.get("reason", "")

    # (3) マッピング (LLM)
    mapping_request = {
        "fileType": fileType,
        "headerRowIndex": header_index,
        "rowData": rowData
    }
    mapping_response = call_mapping(mapping_request)

    if mapping_response.get("status") == "error":
        return {
            "status": "error",
            "message": "マッピング提案に失敗しました",
            "details": mapping_response
        }

    # (4) 最終結果をまとめる
    return {
        "status": "success",
        "headerResponse": header_response,
        "mappingResponse": mapping_response
    }
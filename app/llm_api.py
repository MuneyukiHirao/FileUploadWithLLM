# app/llm_api.py
# (openai>=1.0.0 対応)

import os
import json
from openai import (
    OpenAI,
    APIConnectionError,
    APIStatusError,
    RateLimitError,
    APIError
)

# Python-dotenv 等でOPENAI_API_KEYを管理する場合は以下のように取得する
# openai_api_key = os.getenv("OPENAI_API_KEY", "YOUR_FALLBACK_API_KEY")

# ここでは直接環境変数を読み取る例にしています
openai_api_key = os.environ.get("OPENAI_API_KEY")
print("[DEBUG] OPENAI_API_KEY (first 8 chars):", (openai_api_key or "")[:8], "...")

if not openai_api_key:
    # ここでキーが取得できない場合のエラー処理
    # 必要に応じて例外を投げるか、ログ出力してください
    print("[WARN ] No OPENAI_API_KEY found in environment variables.")

client = OpenAI(api_key=openai_api_key)

def call_header_detection(request_data: dict) -> dict:
    """
    system_prompt_header_detection.md を読み込み、
    ChatGPT API (openai>=1.0.0) に問い合わせてヘッダー判定を行う。
    """
    # システムプロンプトを読み込む
    try:
        with open("system_prompt_header_detection.md", "r", encoding="utf-8") as f:
            system_prompt = f.read()
    except Exception as e:
        print("[DEBUG] Failed to load system_prompt_header_detection.md:", e)
        return {
            "status": "error",
            "message": f"Failed to load system_prompt_header_detection.md: {str(e)}"
        }


    print("[DEBUG] system prompt length =", len(system_prompt))
    # ユーザープロンプト (rowData を埋め込む)
    user_prompt = f"Here is the JSON data:\n{json.dumps(request_data, ensure_ascii=False)}"
    print("[DEBUG] call_header_detection -> user_prompt length =", len(user_prompt))
    print("[DEBUG] OPENAI_API_KEY (first 8 chars):", (openai_api_key or "")[:8], "...")

    try:
        # ChatCompletion呼び出し (新しいOpenAIクライアント)
        chat_completion = client.chat.completions.create(
            model="gpt-4o",  # 必要に応じて "gpt-4" などに変更
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.0
        )
    except APIConnectionError as e:
        print("[ERROR] Could not connect to the API:", e)
        return {
            "status": "error",
            "message": f"Could not connect to the API: {str(e)}"
        }
    except RateLimitError as e:
        print("[ERROR] Rate limit error:", e)
        return {
            "status": "error",
            "message": f"Rate limit error: {str(e)}"
        }
    except APIStatusError as e:
        print("[ERROR] API returned error status =", e.status_code, "; response =", e.response)
        return {
            "status": "error",
            "message": f"API returned error (status={e.status_code}): {e.response}"
        }
    except APIError as e:
        print("[ERROR] OpenAI API Error:", e)
        return {
            "status": "error",
            "message": f"OpenAI API Error: {str(e)}"
        }
    except Exception as e:
        print("[ERROR] Unexpected error:", e)
        return {
            "status": "error",
            "message": f"Unexpected error: {str(e)}"
        }

    # chat_completion から結果テキストを取り出し、JSONパース
    try:
        assistant_content = chat_completion.choices[0].message.content
        print("[DEBUG] assistant_content =", assistant_content)  # ★ ここで出力
        parsed_json = json.loads(assistant_content)
        return parsed_json
    except Exception as e:
        print("[ERROR] JSON parse failed:", e)
        return {
            "status": "error",
            "message": f"Failed to parse JSON from LLM: {str(e)}",
            "rawResponse": str(chat_completion)
        }

def call_mapping(request_data: dict) -> dict:
    """
    system_prompt_mapping.md を読み込み、
    ChatGPT API (openai>=1.0.0) に問い合わせてマッピング提案を行う。
    """
    try:
        with open("system_prompt_mapping.md", "r", encoding="utf-8") as f:
            system_prompt = f.read()
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to load system_prompt_mapping.md: {str(e)}"
        }

    user_prompt = f"Here is the JSON data:\n{json.dumps(request_data, ensure_ascii=False)}"

    try:
        chat_completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.0
        )
    except APIConnectionError as e:
        return {
            "status": "error",
            "message": f"Could not connect to the API: {str(e)}"
        }
    except RateLimitError as e:
        return {
            "status": "error",
            "message": f"Rate limit error: {str(e)}"
        }
    except APIStatusError as e:
        return {
            "status": "error",
            "message": f"API returned error (status={e.status_code}): {e.response}"
        }
    except APIError as e:
        return {
            "status": "error",
            "message": f"OpenAI API Error: {str(e)}"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Unexpected error: {str(e)}"
        }

    try:
        assistant_content = chat_completion.choices[0].message.content
        parsed_json = json.loads(assistant_content)
        return parsed_json
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to parse JSON from LLM: {str(e)}",
            "rawResponse": str(chat_completion)
        }

def call_mapping_refine(original_mapping: dict, user_instruction: str) -> dict:
    """
    既存マッピングと自然言語指示をLLMに渡し、修正後のマッピングを生成してもらう。
    戻り値は call_mapping() と同様の {"status": ..., "mapping": [...], "missingRequiredFields": [...], "additionalNotes": ""} の形を期待。
    """
    system_prompt = ""
    try:
        with open("system_prompt_mapping.md", "r", encoding="utf-8") as f:
            system_prompt = f.read()
    except Exception as e:
        raise RuntimeError(f"Failed to load system_prompt_mapping.md: {str(e)}")

    # ユーザープロンプトを組み立て
    # 既存マッピングとユーザ指示を JSON で渡す
    user_prompt_content = {
        "originalMapping": original_mapping,
        "userInstruction": user_instruction
    }
    user_prompt = json.dumps(user_prompt_content, ensure_ascii=False)

    try:
        chat_completion = client.chat.completions.create(
            model="gpt-4o",  # 任意のモデル名
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.0
        )
    except Exception as e:
        raise RuntimeError(f"LLM API call failed: {str(e)}")

    # レスポンスをJSONパース
    try:
        assistant_content = chat_completion.choices[0].message.content
        parsed_json = json.loads(assistant_content)
        return parsed_json
    except Exception as e:
        raise RuntimeError(f"Failed to parse JSON from LLM: {str(e)}")

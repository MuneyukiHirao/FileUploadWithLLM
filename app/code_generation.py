# app/code_generation.py
import os
import json
import traceback
from openai import OpenAI

REQUIRED_FIELDS = ["distributorCode", "CustomerName", "AccountNumber"]

def generate_and_run_code(mapping_info, row_data, system_prompt_path="system_prompt_code_generation.md", model_name="o1-mini"):
    """
    1) mapping_info, row_data が受け取れる。
    2) 必須項目がすべてマッピングできているか確認し、できていない場合は処理を中断して戻り値にエラーを返す。
    3) 必須項目すべてがマッピング成功していればユーザに確認(OK/Yes か、Noか)。
       - OK/Yes => LLMへコード生成リクエストを実施。
       - No     => 「ユーザがNoと回答したので中断」等を返して終了。
    4) 生成されたコードをファイルに保存 (例: generated_transform.py)。
    5) 生成されたコードを実行し、transform_data(mapping_info, row_data) の結果を返す。
    6) 途中でエラーがあれば、その情報を返す。

    デバッグ用に、生成したコードやエラー内容を出力する。
    """
    # --------------------------
    # (1) 必須項目がすべてマッピングされているかを確認
    mapped_fields = [m["matchedField"] for m in mapping_info if m["matchedField"]]
    missing = [f for f in REQUIRED_FIELDS if f not in mapped_fields]

    if missing:
        return {
            "status": "error",
            "message": f"必須項目がマッピングされていません: {missing}"
        }

    print("必須項目すべてのマッピングが成功しました。")

    # --------------------------
    # (2) ユーザへの確認 (端末入力を想定)
    user_input = input("Pythonコードの作成に進みますか？進む場合はOKまたはYes、マッピングを見直す場合はNoと答えてください。")
    if user_input.lower() not in ["ok", "yes"]:
        return {
            "status": "cancelled",
            "message": "ユーザがNoまたは想定外の入力をしたため、処理を中断しました。"
        }

    # --------------------------
    # (3) system prompt 読み込み
    try:
        with open(system_prompt_path, "r", encoding="utf-8") as f:
            system_prompt = f.read()
    except Exception as e:
        return {
            "status": "error",
            "message": f"システムプロンプトの読み込みに失敗しました: {str(e)}"
        }

    # --------------------------
    # (4) LLMを呼び出してコード生成
    openai_api_key = os.getenv("OPENAI_API_KEY", "YOUR_API_KEY")
    client = OpenAI(api_key=openai_api_key)

    user_prompt = {
        "mapping": mapping_info,
        "rowData": row_data
    }

    try:
        completion = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "user", "content": system_prompt},
                {"role": "user", "content": json.dumps(user_prompt, ensure_ascii=False)},
            ]
        )
        generated_code = completion.choices[0].message.content
        # --- 追加: コードブロックの除去 ---
        # 先頭・末尾を含め、```python や ``` があったら除去
        generated_code = generated_code.replace("```python", "")
        generated_code = generated_code.replace("```", "")

    except Exception as e:
        # 生成リクエスト時点で何か起きた
        return {
            "status": "error",
            "message": f"コード生成に失敗しました: {str(e)}"
        }

    # --------------------------
    # (5) 生成されたPythonコードをファイルに保存
    output_file = "generated_transform.py"
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(generated_code)
    except Exception as e:
        return {
            "status": "error",
            "message": f"生成コードの書き込みに失敗しました: {str(e)}"
        }

    # ★ デバッグ出力: 生成されたコードの内容をライン番号付きで表示
    print("\n=== DEBUG: Generated Python code (with line numbers) ===")
    code_lines = generated_code.split("\n")
    for i, line in enumerate(code_lines, start=1):
        print(f"{i:03d}: {line}")
    print("=== End of Generated Code ===\n")

    # --------------------------
    # (6) 生成コードを読み込んで transform_data() 関数を呼び出し
    try:
        global_namespace = {}

        # exec前のデバッグ用 (内容はすでに上でプリント済み)
        # ここでさらに何か加工やログが必要なら適宜入れる

        exec(generated_code, global_namespace)

        if "transform_data" not in global_namespace:
            return {
                "status": "error",
                "message": "生成されたコードに transform_data 関数が存在しません。"
            }

        transform_func = global_namespace["transform_data"]

        transformed = transform_func(mapping_info, row_data)
        return {
            "status": "success",
            "transformedData": transformed
        }

    except SyntaxError as se:
        # Python構文エラーの場合、どの行で何が起きたかを表示
        tb_str = traceback.format_exc()
        return {
            "status": "error",
            "message": f"生成されたコードの実行に失敗しました (SyntaxError): {str(se)}",
            "traceback": tb_str
        }
    except Exception as e:
        tb_str = traceback.format_exc()
        return {
            "status": "error",
            "message": f"生成されたコードの実行に失敗しました: {str(e)}",
            "traceback": tb_str
        }

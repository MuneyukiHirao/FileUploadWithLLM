import os
import uuid
import json    # ★ これを追加
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from app.main_processor import process_file_and_map  # 以前の会話で紹介された処理を想定
from app.llm_api import call_mapping_refine  # これを忘れていないか？
from openai import OpenAI

app = Flask(__name__)
app.config["SECRET_KEY"] = "何か適当な秘密鍵"
app.config["SESSION_COOKIE_SAMESITE"] = "None"
app.config["SESSION_COOKIE_SECURE"] = True
CORS(app, supports_credentials=True)  # Cookie送受信を許可

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploaded_files')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    user_id = data.get('userId')
    password = data.get('password')
    if user_id == 'test' and password == 'test':
        return jsonify({"status": "success", "message": "ログイン成功"})
    else:
        return jsonify({"status": "error", "message": "ユーザIDまたはパスワードが違います"}), 401

@app.route('/api/upload', methods=['POST'])
def upload_file():
    print(">>> /api/upload called")  # デバッグ用
    if 'file' not in request.files:
        print("!!! No 'file' in request.files")
        return jsonify({"status": "error", "message": "ファイルが見つかりません"}), 400

    file = request.files['file']
    print(f">>> Received file: {file.filename}")

    # ファイルサイズチェック
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0, 0)
    print(f">>> File size: {file_size} bytes")

    if file_size > MAX_FILE_SIZE:
        print("!!! File too large")
        return jsonify({"status": "error", "message": "ファイルサイズが500MBを超えています。"}), 400

    filename = file.filename.lower()
    ALLOWED_EXTENSIONS = ['.xlsx', '.csv', '.json']
    if not any(filename.endswith(ext) for ext in ALLOWED_EXTENSIONS):
        print(f"!!! Invalid extension for file: {filename}")
        return jsonify({
            "status": "error",
            "message": "サポートされていない拡張子です。xlsx, csv, jsonのみ対応しています。"
        }), 400

    unique_id = str(uuid.uuid4())
    new_filename = f"{unique_id}_{filename}"
    save_path = os.path.join(UPLOAD_FOLDER, new_filename)

    print(f">>> Saving file to: {save_path}")
    try:
        file.save(save_path)
    except Exception as e:
        print(f"!!! Error saving file: {e}")
        return jsonify({"status": "error", "message": f"ファイル保存中にエラーが発生しました: {str(e)}"}), 500

    print(">>> File saved successfully.")
    return jsonify({
        "status": "success",
        "message": "ファイルをアップロードしました",
        "savedFileName": new_filename
    })

@app.route('/api/analyze', methods=['POST'])
def analyze_file():
    """
    1. リクエストボディでファイル名を受け取る
    2. UPLOAD_FOLDER から対象ファイルを探す
    3. process_file_and_map() を呼び出し、結果を返す
    """
    data = request.get_json()
    file_name = data.get('fileName')
    if not file_name:
        return jsonify({"status": "error", "message": "ファイル名が指定されていません"}), 400

    file_path = os.path.join(UPLOAD_FOLDER, file_name)
    if not os.path.exists(file_path):
        return jsonify({"status": "error", "message": "ファイルが見つかりません"}), 404

    # ここでLLM呼び出しなどを行う main_processor の関数を呼ぶ
    result = process_file_and_map(file_path)
    return jsonify(result)

@app.route('/api/remap', methods=['POST'])
def remap():
    """
    既存のmappingResponseとユーザ指示を受け取り、
    LLMに再度問い合わせて修正マッピングを提案してもらう。
    """
    data = request.get_json()
    original_mapping = data.get('originalMapping', {})
    user_instruction = data.get('userInstruction', '')

    # 必要があれば rowData なども受け取る
    # rowData = data.get('rowData', [])  # if needed

    try:
        # call_mapping_refine() は新たに定義する関数: LLMに再マッピング指示を出す処理
        refined_result = call_mapping_refine(original_mapping, user_instruction)
        return jsonify({
            "status": "success",
            "mappingResponse": refined_result  # 返却フォーマットは call_mapping() と同じを想定
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# 生成コードと変換結果を保存するフォルダ
GENERATED_FOLDER = os.path.join(os.path.dirname(__file__), "generated")
os.makedirs(GENERATED_FOLDER, exist_ok=True)

@app.route("/api/codegen", methods=["POST"])
def codegen():
    """
    1. 受け取ったmapping, rowDataでLLMにPythonコードを生成してもらう
    2. 生成スクリプトをファイルに保存
    3. スクリプトを実行し、変換結果をファイルに保存
    4. レスポンスには"status":"success"とダウンロード用パスなどを返す
    """

    data = request.get_json()
    file_name = data.get("fileName")  # (E) フロントが送るはずのファイル名

    if not file_name:
        return jsonify({"status":"error","message":"fileName is missing"}), 400

    file_path = os.path.join(UPLOAD_FOLDER, file_name)
    if not os.path.exists(file_path):
        return jsonify({"status":"error","message":"File not found on server"}), 404

    mapping = data.get("mapping", [])
    row_data = data.get("rowData", [])
    file_name = data.get("fileName")

    # (A) ファイルパスを組み立て
    # アップロード時に savedFileName を受け取っている想定
    file_path = os.path.join(UPLOAD_FOLDER, file_name)
    if not os.path.exists(file_path):
        return jsonify({"status":"error","message":"File not found"}), 404


    # (B) system_promptを読み込む
    try:
        with open("system_prompt_code_generation.md", "r", encoding="utf-8") as f:
            system_prompt = f.read()
    except Exception as e:
        app.logger.error(f"Failed to load system prompt: {str(e)}")
        return jsonify({"status":"error", "message":f"Failed to load system prompt: {str(e)}"}), 500

    # (C) OpenAI呼び出し (例)
    openai_api_key = os.environ.get("OPENAI_API_KEY")

    client = OpenAI(api_key=openai_api_key)

    user_prompt = {
        "mapping": mapping,
        "rowData": row_data
    }
    
    try:
        resp = client.chat.completions.create(
            model="o1-mini",  # 例：Pythonコード生成用モデル
            messages=[
                {"role": "user", "content": system_prompt},
                {"role": "user", "content": json.dumps(user_prompt, ensure_ascii=False)}
            ]
        )
        generated_code = resp.choices[0].message.content
        # 不要な ```python や ``` を取り除く
        generated_code = generated_code.replace("```python", "").replace("```", "")
    except Exception as e:
        app.logger.error(f"LLM code generation failed: {str(e)}")
        return jsonify({"status":"error","message":f"LLM code generation failed: {str(e)}"}), 500

    # (D) コードをファイルに保存
    generated_py_path = os.path.join(GENERATED_FOLDER, "generated_transform.py")
    try:
        with open(generated_py_path, "w", encoding="utf-8") as f:
            f.write(generated_code)
    except Exception as e:
        return jsonify({"status":"error","message":f"Writing generated file failed: {str(e)}"}), 500

    # (E) コードを実行し、変換結果を保存
    # (D) 実行 -> ただし transform_data() に渡す row_data は "全行" である必要あり
    from app.file_to_json import convert_xlsx_to_json
    full_data_result = convert_xlsx_to_json(file_path, limit_rows=False)
    if full_data_result["status"] != "success":
        return jsonify({"status":"error","message":full_data_result["message"]}), 400

    full_row_data = full_data_result["rowData"]

    transformed_data = []
    try:
        global_namespace = {}
        exec(generated_code, global_namespace)
        transform_func = global_namespace.get("transform_data")
        if not transform_func:
            return jsonify({"status":"error","message":"No transform_data in generated code"}), 500

        # 実際に全行を変換
        transformed_data = transform_func(mapping, full_row_data)

        # 変換結果をJSONとして保存 or CSVとして保存など
        # ここでは簡単にJSONとして保存
        output_json_path = os.path.join(GENERATED_FOLDER, "transformed_data.json")
        with open(output_json_path, "w", encoding="utf-8") as f:
            json.dump(transformed_data, f, ensure_ascii=False, indent=2)

    except SyntaxError as se:
        tb_str = traceback.format_exc()
        return jsonify({
            "status":"error",
            "message":f"Syntax error in generated code: {str(se)}",
            "traceback":tb_str
        }), 500
    except Exception as e:
        tb_str = traceback.format_exc()
        return jsonify({
            "status":"error",
            "message":f"Error running generated code: {str(e)}",
            "traceback":tb_str
        }), 500

    # (F) 成功レスポンス
    return jsonify({
        "status":"success",
        "message":"Code generated and executed successfully.",
        "generatedPyPath": "/api/download/py",     # ダウンロード用URL例
        "transformedDataPath": "/api/download/data" # ダウンロード用URL例
    })


@app.route("/api/download/py", methods=["GET"])
def download_py():
    """
    生成されたPythonコードをダウンロードさせる例
    """
    generated_py_path = os.path.join(GENERATED_FOLDER, "generated_transform.py")
    if not os.path.exists(generated_py_path):
        return jsonify({"status":"error","message":"No generated Python file found"}), 404

    return send_file(
        generated_py_path,
        as_attachment=True,
        download_name="generated_transform.py",
        mimetype="text/x-python"
    )


@app.route("/api/download/data", methods=["GET"])
def download_data():
    """
    変換後のデータをダウンロードさせる例 (JSON想定)
    """
    output_json_path = os.path.join(GENERATED_FOLDER, "transformed_data.json")
    if not os.path.exists(output_json_path):
        return jsonify({"status":"error","message":"No transformed data found"}), 404

    return send_file(
        output_json_path,
        as_attachment=True,
        download_name="transformed_data.json",
        mimetype="application/json"
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)

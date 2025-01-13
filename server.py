from flask import Flask, request, jsonify, session
from flask_cors import CORS

app = Flask(__name__)
app.secret_key = 'some-secret-key-for-session'
CORS(app)  # 簡易CORS対応（本番利用時は設定に注意）

@app.route('/login', methods=['POST'])
def login():
    """
    ユーザ名・パスワードが test/test なら認証成功とする簡易実装
    成功時: session['logged_in'] = True をセット
    失敗時: 401エラーを返す
    """
    data = request.json
    username = data.get('username', '')
    password = data.get('password', '')

    if username == 'test' and password == 'test':
        session['logged_in'] = True
        return jsonify({'status': 'success'})
    else:
        return jsonify({'status': 'error', 'message': 'Invalid credentials'}), 401

@app.route('/logout', methods=['POST'])
def logout():
    """
    ログアウト処理：セッション情報をクリア
    """
    session.pop('logged_in', None)
    return jsonify({'status': 'success', 'message': 'Logged out'})

@app.route('/check_login', methods=['GET'])
def check_login():
    """
    ログイン状態を確認する簡易API (フロントエンドで必要に応じて利用)
    """
    if session.get('logged_in', False):
        return jsonify({'status': 'logged_in'})
    else:
        return jsonify({'status': 'not_logged_in'}), 401

if __name__ == '__main__':
    # ローカル実行用: http://127.0.0.1:5000/
    app.run(debug=True)

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

function Login() {
  const [userId, setUserId] = useState('');
  const [password, setPassword] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  const navigate = useNavigate(); // ← 追加

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage('');

    try {
      const response = await fetch('/api/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ userId, password }),
      });

      if (!response.ok) {
        // 4xx, 5xx エラー
        const errorData = await response.json();
        setErrorMessage(errorData.message || 'Failed to login.');
        return;
      }

      // 成功時
      const data = await response.json();
      if (data.status === 'success') {
        // ログイン成功 → /upload に遷移
        navigate('/upload');
      } else {
        setErrorMessage(data.message || 'Failed to login');
      }
    } catch (err) {
      console.error("fetch error: ", err);
      setErrorMessage('Cannot communicate with server.');
    }
  };

  return (
    <div style={{ margin: '2rem' }}>
      <h1>Login</h1>
      <form onSubmit={handleSubmit} style={{ display: 'inline-block' }}>
        <div style={{ marginBottom: '1rem' }}>
          <label>
            User ID:
            <input
              type="text"
              value={userId}
              onChange={(e) => setUserId(e.target.value)}
            />
          </label>
        </div>
        <div style={{ marginBottom: '1rem' }}>
          <label>
            Password:
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </label>
        </div>
        <button type="submit">Login</button>
      </form>

      {errorMessage && (
        <div style={{ color: 'red', marginTop: '1rem' }}>{errorMessage}</div>
      )}
    </div>
  );
}

export default Login;

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

const FileUpload: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [message, setMessage] = useState('');
  const [analysisResult, setAnalysisResult] = useState<any>(null);

  // アップロード成功後にサーバから返ってくる savedFileName を保持するステート
  const [savedFileName, setSavedFileName] = useState<string | null>(null);

  const navigate = useNavigate();

  // ▼ ファイル選択時
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setSelectedFile(e.target.files[0]);
      setMessage('');
      setAnalysisResult(null);
      setSavedFileName(null);
    }
  };

  // ▼ ファイルアップロード実行
  const handleUpload = async () => {
    if (!selectedFile) {
      setMessage('Please select file.');
      return;
    }
    setMessage('Uploading...');

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);

      // /api/upload へPOST
      const response = await fetch('/api/upload', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        setMessage(errorData.message || 'Failed to upload file.');
        return;
      }

      const data = await response.json();
      if (data.status === 'success') {
        // アップロード成功、ファイル名を取得
        setSavedFileName(data.savedFileName);
        setMessage('File upload succes! Analysis start...');
        // 続けて解析APIを呼ぶ
        await analyzeFile(data.savedFileName);
      } else {
        setMessage(data.message || 'Failed to upload file.');
      }
    } catch (error) {
      console.error(error);
      setMessage('Failed to communicate with server.');
    }
  };

  // ▼ /api/analyze を呼び出してLLM解析を行い、その結果を受け取る
  //    解析が成功すれば /mapping へ画面遷移
  const analyzeFile = async (fileName: string) => {
    setMessage('Analyzing...');
    try {
      const response = await fetch('/api/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ fileName }), // サーバ側で file_path を組み立てる用
      });

      if (!response.ok) {
        const errorData = await response.json();
        setMessage(errorData.message || 'Failed to analyze.');
        return;
      }

      const resultData = await response.json();
      if (resultData.status === 'success') {
        setMessage('Analysis done! Moving to mapping...');
        setAnalysisResult(resultData);

        // マッピング画面に遷移。解析結果 & fileName を一緒に渡す。
        navigate('/mapping', {
          state: {
            analysisResult: resultData,
            fileName: fileName, // savedFileName
          },
        });
      } else {
        setMessage(resultData.message || 'Failed to analyze.');
      }
    } catch (err) {
      console.error(err);
      setMessage('Error occured while communicating with server.');
    }
  };

  return (
    <div style={{ margin: '2rem' }}>
      <h1>Upload file</h1>
      <div style={{ marginBottom: '1rem' }}>
        <input type="file" onChange={handleFileChange} />
        <button onClick={handleUpload} style={{ marginLeft: '1rem' }}>
          Upload
        </button>
      </div>

      {message && (
        <div style={{ marginTop: '1rem', color: 'blue' }}>
          {message}
        </div>
      )}

      {/* デバッグや確認用に表示 */}
      {savedFileName && (
        <div style={{ marginTop: '1rem' }}>
          <strong>File name on server:</strong> {savedFileName}
        </div>
      )}
      {analysisResult && analysisResult.status === 'success' && (
        <div style={{ marginTop: '1rem' }}>
          <pre style={{ background: '#f4f4f4', padding: '1rem' }}>
            {JSON.stringify(analysisResult, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
};

export default FileUpload;

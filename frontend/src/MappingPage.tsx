import React, { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';

// 修正指示入力コンポーネント
const RemapInstruction: React.FC<{ onRemap: (userInstruction: string) => void }> = ({ onRemap }) => {
  const [instruction, setInstruction] = useState('');

  return (
    <div style={{ marginTop: '1rem', backgroundColor: '#f7f7f7', padding: '1rem' }}>
      <h3>Revision instruction</h3>
      <textarea
        rows={5}
        cols={50}
        value={instruction}
        onChange={(e) => setInstruction(e.target.value)}
        placeholder="For example, please use the 'Customer Name' column in Excel for 'CustomerName,' instead of the 'Customer Name (abbreviated)' column."
      />
      <br />
      <button onClick={() => onRemap(instruction)} style={{ marginTop: '0.5rem' }}>
        Execute re-mapping
      </button>
    </div>
  );
};

// マッピング表示コンポーネント (システムフィールドをベースに表示)
interface MappingItem {
  columnIndex: number;
  columnName: string | null;
  matchedField: string | null;
  confidence: number;
}

interface MappingResponse {
  mapping: MappingItem[];
  missingRequiredFields: string[];
  additionalNotes: string;
}

interface HeaderDetection {
  isHeaderPresent: boolean;
  headerRowIndex: number;
  reason: string;
}

interface HeaderResponse {
  status: string;
  headerDetection: HeaderDetection;
}

interface MappingReviewProps {
  mappingResponse: MappingResponse;
  rowData: string[][];
  headerResponse: HeaderResponse;
  onConfirm: () => void;
  onNeedImprovement: () => void;
}

const MappingReview: React.FC<MappingReviewProps> = ({
  mappingResponse,
  rowData,
  headerResponse,
  onConfirm,
  onNeedImprovement
}) => {
  const { mapping, missingRequiredFields } = mappingResponse;
  const { isHeaderPresent, headerRowIndex } = headerResponse.headerDetection;

  // 顧客マスタの全フィールド
  const systemFields = [
    { name: 'distributorCode', label: 'distributorCode', required: true },
    { name: 'CustomerName', label: 'CustomerName', required: true },
    { name: 'AccountNumber', label: 'AccountNumber', required: true },
    { name: 'Rank', label: 'Rank', required: false },
    { name: 'SalesPic', label: 'SalesPic', required: false },
    { name: 'PartsSalesPic', label: 'PartsSalesPic', required: false },
    { name: 'ServicePic', label: 'ServicePic', required: false },
    { name: 'BillingAddress1', label: 'BillingAddress1', required: false },
  ];

  // データ開始行 (ヘッダーがある場合はその次の行から)
  const dataStartIndex = isHeaderPresent ? headerRowIndex + 1 : 0;

  // 指定列のサンプルデータ上位3件を返す
  const getSampleData = (colIndex: number): string[] => {
    const samples: string[] = [];
    for (let i = dataStartIndex; i < rowData.length; i++) {
      if (samples.length >= 3) break;
      const row = rowData[i];
      if (row && row.length > colIndex) {
        samples.push(String(row[colIndex]));
      }
    }
    return samples;
  };

  // ------------------------------
  // 1) システムフィールドをベースにマッピング表示
  // ------------------------------
  const systemFieldTable = (
    <table style={{ borderCollapse: 'collapse', width: '100%' }}>
      <thead>
        <tr>
          <th style={{ border: '1px solid #ccc', padding: '8px' }}>System field</th>
          <th style={{ border: '1px solid #ccc', padding: '8px' }}>Mandatory or Optional</th>
          <th style={{ border: '1px solid #ccc', padding: '8px' }}>Mapped column</th>
          <th style={{ border: '1px solid #ccc', padding: '8px' }}>Confidence</th>
          <th style={{ border: '1px solid #ccc', padding: '8px' }}>Sample data(Max 3 records)</th>
        </tr>
      </thead>
      <tbody>
        {systemFields.map((field) => {
          const found = mapping.find((m) => m.matchedField === field.name);
          if (found) {
            const samples = getSampleData(found.columnIndex);
            return (
              <tr key={field.name}>
                <td style={{ border: '1px solid #ccc', padding: '8px' }}>{field.label}</td>
                <td style={{ border: '1px solid #ccc', padding: '8px' }}>
                  {field.required ? 'Mandatory' : 'Optional'}
                </td>
                <td style={{ border: '1px solid #ccc', padding: '8px' }}>
                  Column Index: {found.columnIndex}
                  {found.columnName ? ` (${found.columnName})` : ''}
                </td>
                <td style={{ border: '1px solid #ccc', padding: '8px' }}>
                  {found.confidence.toFixed(2)}
                </td>
                <td style={{ border: '1px solid #ccc', padding: '8px' }}>
                  {samples.length > 0 ? samples.join(' / ') : '(No data)'}
                </td>
              </tr>
            );
          } else {
            // 未マッピング
            return (
              <tr key={field.name} style={{ backgroundColor: '#fff2f2' }}>
                <td style={{ border: '1px solid #ccc', padding: '8px' }}>{field.label}</td>
                <td style={{ border: '1px solid #ccc', padding: '8px' }}>
                  {field.required ? 'Mandatory' : 'Optional'}
                </td>
                <td style={{ border: '1px solid #ccc', padding: '8px' }}>
                  (Unmapped)
                </td>
                <td style={{ border: '1px solid #ccc', padding: '8px' }}>
                  -
                </td>
                <td style={{ border: '1px solid #ccc', padding: '8px' }}>
                  -
                </td>
              </tr>
            );
          }
        })}
      </tbody>
    </table>
  );

  // ------------------------------
  // 2) アップロードファイル側で「未マッピング」の列情報一覧
  // ------------------------------
  //   - まず列の最大数を確認
  //   - mapping で matchedField != null の列Indexは「マッピング済み」とみなす
  //   - それ以外をリストアップ
  const totalColCount = rowData.reduce((max, row) => Math.max(max, row.length), 0);
  const mappedColumnIndexes = new Set<number>();
  mapping.forEach(m => {
    if (m.matchedField) {
      mappedColumnIndexes.add(m.columnIndex);
    }
  });

  const unmappedColumns = [];
  for (let colIndex = 0; colIndex < totalColCount; colIndex++) {
    // もし mapping のうち matchedField が null のものがあれば、それも「unmapped」扱いにする
    // → matchedField が null でも columnIndexが同じなら "found"
    const mappedItem = mapping.find(m => m.columnIndex === colIndex);
    const isActuallyMapped = mappedItem?.matchedField ? true : false;
    if (!isActuallyMapped) {
      // ここが「ファイル上の colIndex がシステムフィールドに割り当てられていない」列
      unmappedColumns.push({ colIndex, columnName: mappedItem?.columnName || null });
    }
  }

  // アップロードファイル上のcolIndex→サンプルデータ3件
  const unmappedTable = (
    <table style={{ borderCollapse: 'collapse', width: '100%', marginTop: '1rem' }}>
      <thead>
        <tr style={{ background: '#f2f2f2' }}>
          <th style={{ border: '1px solid #ccc', padding: '8px' }}>Column Index</th>
          <th style={{ border: '1px solid #ccc', padding: '8px' }}>Column name</th>
          <th style={{ border: '1px solid #ccc', padding: '8px' }}>Sample data(Max 3 records)</th>
        </tr>
      </thead>
      <tbody>
        {unmappedColumns.map((col) => {
          const samples = getSampleData(col.colIndex);
          const colName = col.columnName
            ? col.columnName
            : (isHeaderPresent && headerRowIndex >= 0 && rowData[headerRowIndex]?.length > col.colIndex)
              ? rowData[headerRowIndex][col.colIndex]
              : null;
          return (
            <tr key={col.colIndex} style={{ backgroundColor: '#fff8dc' }}>
              <td style={{ border: '1px solid #ccc', padding: '8px' }}>{col.colIndex}</td>
              <td style={{ border: '1px solid #ccc', padding: '8px' }}>{colName || '(Unknown)'}</td>
              <td style={{ border: '1px solid #ccc', padding: '8px' }}>
                {samples.length > 0 ? samples.join(' / ') : '(No data)'}
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );


  return (
    <div style={{ marginTop: '1rem' }}>
      <h2>Mapping results</h2>
      {missingRequiredFields && missingRequiredFields.length > 0 && (
        <div style={{ color: 'red', marginBottom: '1rem' }}>
          Required fields are unmapped: {missingRequiredFields.join(', ')}
        </div>
      )}

      {/* (1) システムフィールドベースのマッピングテーブル */}
      {systemFieldTable}

      {/* (2) ファイル上の未マッピング列一覧 */}
      <h3 style={{ marginTop: '2rem' }}>Unmapped columns</h3>
      {unmappedColumns.length === 0 ? (
        <p>There are no unmapped column.</p>
      ) : (
        unmappedTable
      )}

      <div style={{ marginTop: '1rem' }}>
        <button onClick={onConfirm} style={{ marginRight: '1rem' }}>
          This mapping is OK
        </button>
        <button onClick={onNeedImprovement}>
          Provide revision instruction
        </button>
      </div>
    </div>
  );
};

// ====================================================================
// MappingPage本体
// ====================================================================
const MappingPage: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();

  // FileUpload.tsx から: navigate('/mapping', { state: { analysisResult } }) で受け取る想定
  const stateData = location.state as {
    analysisResult?: any;
    fileName?: string;
  };
  const [analysisResult, setAnalysisResult] = useState<any>(stateData?.analysisResult);
  const [uploadedFileName, setUploadedFileName] = useState<string | undefined>(stateData?.fileName);

  const [showRemapInput, setShowRemapInput] = useState(false);
  const [message, setMessage] = useState('');

  // ▼ ここでダウンロード用のURLを管理するステートを定義
  const [downloadLinks, setDownloadLinks] = useState<{ py?: string; transformed?: string }>({});

  if (!analysisResult) {
    return (
      <div style={{ margin: '2rem' }}>
        <h2>There are no mapping information</h2>
        <button onClick={() => navigate('/upload')}>Back to file upload screen</button>
      </div>
    );
  }

  // rowData, headerResponse, mappingResponse を取り出す
  const { rowData = [], headerResponse, mappingResponse } = analysisResult;

  const handleConfirmMapping = async () => {
    console.log("mappingResponse:", mappingResponse);
    console.log("uploadedFileName:", uploadedFileName);
    if (!mappingResponse || !mappingResponse.mapping) {
      setMessage("There are no mapping information.");
      return;
    }
    if (!uploadedFileName) {
      setMessage("Upload file name is not provided.");
      return;
    }
        
    setMessage("Generation of code start...");
    try {
      const res = await fetch("/api/codegen", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          mapping: mappingResponse.mapping,
          fileName: uploadedFileName, // これが大事
          rowData: rowData
        })
      });
      if (!res.ok) {
        const errData = await res.json();
        setMessage(errData.message || "Failed to generate code.");
        return;
      }
      const data = await res.json();
      if (data.status === "success") {
        setMessage("Completed code generation! Download the Python code from below link.");
        // data.generatedPyPath と data.transformedDataPath を使ってリンク表示する
        setDownloadLinks({
          py: data.generatedPyPath,
          transformed: data.transformedDataPath
        });
      } else {
        setMessage(data.message || "Failed to generate code.");
      }
    } catch (e) {
      console.error(e);
      setMessage("Failed to call API.");
    }
  };

  // 「修正指示」ボタンクリック
  const handleNeedImprovement = () => {
    setShowRemapInput(true);
  };

  // 再マッピング指示の送信
  const handleRemap = async (instruction: string) => {
    if (!mappingResponse) return;
    if (!instruction.trim()) {
      alert('Provide revision instruction.');
      return;
    }
  
    setMessage('Remap in-progerss...');
    try {
      const res = await fetch('/api/remap', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          originalMapping: mappingResponse, // 既存のマッピング情報
          userInstruction: instruction,
        }),
      });
      if (!res.ok) {
        const errData = await res.json();
        setMessage(errData.message || 'Failed to remap.');
        return;
      }
      const data = await res.json();
      if (data.status === 'success') {
        // 新しい mappingResponse に差し替え
        setAnalysisResult({
          ...analysisResult,
          mappingResponse: data.mappingResponse
        });
        setMessage('Remap completed.');
      } else {
        setMessage(data.message || 'Failed to remap.');
      }
    } catch (error) {
      console.error(error);
      setMessage('Failed to call remapping API.');
    }
  };

  return (
    <div style={{ margin: '2rem' }}>
      <h1>Mapping review screen</h1>
      {message && (
        <div style={{ color: 'blue', marginBottom: '1rem' }}>
          {message}
        </div>
      )}

      {/* ダウンロードリンク表示 */}
      {downloadLinks.py && (
        <div style={{ marginTop: '1rem' }}>
          <a href={downloadLinks.py} download>
            Download the generated Python code
          </a>
        </div>
      )}
      {downloadLinks.transformed && (
        <div style={{ marginTop: '1rem' }}>
          <a href={downloadLinks.transformed} download>
            Download the converted data
          </a>
        </div>
      )}

      {/* ヘッダー判定の概要表示 */}
      {headerResponse && headerResponse.headerDetection && (
        <div style={{ background: '#eee', padding: '1rem', marginBottom: '1rem' }}>
          <h3>Header determination result</h3>
          <p>isHeaderPresent: {String(headerResponse.headerDetection.isHeaderPresent)}</p>
          <p>headerRowIndex: {headerResponse.headerDetection.headerRowIndex}</p>
          <p>reason: {headerResponse.headerDetection.reason}</p>
        </div>
      )}

      {/* システムフィールドベースでのマッピング表示 */}
      {mappingResponse && (
        <MappingReview
          mappingResponse={mappingResponse}
          rowData={rowData}
          headerResponse={headerResponse}
          onConfirm={handleConfirmMapping}
          onNeedImprovement={handleNeedImprovement}
        />
      )}

      {/* 修正指示エリア */}
      {showRemapInput && (
        <RemapInstruction onRemap={handleRemap} />
      )}
    </div>
  );
};

export default MappingPage;

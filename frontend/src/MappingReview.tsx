import React from 'react';

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
  status: string;  // "success"等
  headerDetection: HeaderDetection;
}

interface Props {
  mappingResponse: MappingResponse;
  rowData: string[][];            // アップロードファイルの先頭100行
  headerResponse: HeaderResponse; // ヘッダー判定の結果
  onConfirm: () => void;
  onNeedImprovement: () => void;
}

const MappingReview: React.FC<Props> = ({
  mappingResponse,
  rowData,
  headerResponse,
  onConfirm,
  onNeedImprovement
}) => {
  const { mapping, missingRequiredFields } = mappingResponse;
  const { isHeaderPresent, headerRowIndex } = headerResponse.headerDetection;

  // --- システムフォーマットを定義（顧客マスタのフィールド一覧） ---
  const systemFields = [
    { name: "distributorCode", label: "distributorCode", required: true },
    { name: "CustomerName", label: "CustomerName", required: true },
    { name: "AccountNumber", label: "AccountNumber", required: true },
    { name: "Rank", label: "Rank", required: false },
    { name: "SalesPic", label: "SalesPic", required: false },
    { name: "PartsSalesPic", label: "PartsSalesPic", required: false },
    { name: "ServicePic", label: "ServicePic", required: false },
    { name: "BillingAddress1", label: "BillingAddress1", required: false },
  ];

  // --- ヘッダー行があるなら、その次の行からがデータ開始 ---
  const dataStartIndex = isHeaderPresent ? headerRowIndex + 1 : 0;

  // rowDataからサンプルデータを取り出すヘルパー
  // 指定列の上位3件を返す
  const getSampleData = (colIndex: number): string[] => {
    const samples: string[] = [];
    for (let i = dataStartIndex; i < rowData.length; i++) {
      if (samples.length >= 3) break;  // 最大3件
      const row = rowData[i];
      // row[colIndex]が存在するかチェック
      if (row && row.length > colIndex && row[colIndex] != null) {
        samples.push(String(row[colIndex]));
      }
    }
    return samples;
  };

  return (
    <div style={{ marginTop: '1rem' }}>
      <h2>マッピング結果</h2>
      {missingRequiredFields && missingRequiredFields.length > 0 && (
        <div style={{ color: 'red', marginBottom: '1rem' }}>
          必須フィールドが未マッピングです: {missingRequiredFields.join(', ')}
        </div>
      )}

      {/* 顧客マスタの全フィールドをリスト表示し、
          そのフィールドにマッピングされているアップロード列を探す */}
      <table style={{ borderCollapse: 'collapse', width: '100%' }}>
        <thead>
          <tr>
            <th style={{ border: '1px solid #ccc', padding: '8px' }}>システムフィールド</th>
            <th style={{ border: '1px solid #ccc', padding: '8px' }}>必須 or 任意</th>
            <th style={{ border: '1px solid #ccc', padding: '8px' }}>マッピングされた列</th>
            <th style={{ border: '1px solid #ccc', padding: '8px' }}>信頼度</th>
            <th style={{ border: '1px solid #ccc', padding: '8px' }}>サンプルデータ (最大3件)</th>
          </tr>
        </thead>
        <tbody>
          {systemFields.map((field) => {
            // マッピング配列の中から該当のmatchedFieldを探す
            const found = mapping.find(m => m.matchedField === field.name);
            if (found) {
              // 見つかった場合、その列Indexからサンプルデータ抽出
              const samples = getSampleData(found.columnIndex);
              return (
                <tr key={field.name}>
                  <td style={{ border: '1px solid #ccc', padding: '8px' }}>
                    {field.label}
                  </td>
                  <td style={{ border: '1px solid #ccc', padding: '8px' }}>
                    {field.required ? '必須' : '任意'}
                  </td>
                  <td style={{ border: '1px solid #ccc', padding: '8px' }}>
                    列Index: {found.columnIndex} 
                    {found.columnName ? ` (${found.columnName})` : ''}
                  </td>
                  <td style={{ border: '1px solid #ccc', padding: '8px' }}>
                    {found.confidence.toFixed(2)}
                  </td>
                  <td style={{ border: '1px solid #ccc', padding: '8px' }}>
                    {samples.length > 0 
                      ? samples.join(' / ')
                      : '(データなし)'
                    }
                  </td>
                </tr>
              );
            } else {
              // 見つからなければ未マッピング
              return (
                <tr key={field.name} style={{ backgroundColor: '#fff2f2' }}>
                  <td style={{ border: '1px solid #ccc', padding: '8px' }}>
                    {field.label}
                  </td>
                  <td style={{ border: '1px solid #ccc', padding: '8px' }}>
                    {field.required ? '必須' : '任意'}
                  </td>
                  <td style={{ border: '1px solid #ccc', padding: '8px' }}>
                    (未マッピング)
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

      <div style={{ marginTop: '1rem' }}>
        <button onClick={onConfirm} style={{ marginRight: '1rem' }}>
          このマッピングでOK
        </button>
        <button onClick={onNeedImprovement}>
          修正指示を行う
        </button>
      </div>
    </div>
  );
};

export default MappingReview;

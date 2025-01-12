def transform_data(mapping, row_data):
    required_fields = ['distributorCode', 'CustomerName', 'AccountNumber']
    optional_fields = ['Rank', 'SalesPic', 'PartsSalesPic', 'ServicePic', 'BillingAddress1']
    field_mapping = {}
    for m in mapping:
        if m['matchedField']:
            field_mapping[m['matchedField']] = m['columnIndex']
    transformed = []
    for row in row_data:
        record = {}
        invalid = False
        for field in required_fields:
            index = field_mapping.get(field)
            if index is not None and index < len(row):
                value = str(row[index])
                if value == '':
                    invalid = True
                    break
                record[field] = value
            else:
                invalid = True
                break
        if invalid:
            continue
        for field in optional_fields:
            index = field_mapping.get(field)
            if index is not None and index < len(row):
                record[field] = str(row[index])
            else:
                record[field] = ""
        transformed.append(record)
    return transformed

mapping = [
    {"columnIndex": 0, "columnName": "顧客コード", "matchedField": "distributorCode", "confidence": 0.9},
    {"columnIndex": 1, "columnName": "顧客名", "matchedField": "CustomerName", "confidence": 0.95},
    {"columnIndex": 2, "columnName": "アカウント番号", "matchedField": "AccountNumber", "confidence": 0.88},
    {"columnIndex": 3, "columnName": "ランク", "matchedField": "Rank", "confidence": 0.5}
]

row_data = [
    ["D001", "株式会社ABC", "AC123", "A"],
    ["D002", "株式会社XYZ", "AC999", "B"]
]

transformed_data = transform_data(mapping, row_data)
print(transformed_data)
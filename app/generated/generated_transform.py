def transform_data(mapping, row_data):
    required_fields = ["distributorCode", "CustomerName", "AccountNumber"]
    optional_fields = ["Rank", "SalesPic", "PartsSalesPic", "ServicePic", "BillingAddress1"]
    field_to_index = {m['matchedField']: m['columnIndex'] for m in mapping if m['matchedField']}
    result = []
    for row in row_data[1:]:
        record = {}
        # Handle required fields
        for field in required_fields:
            idx = field_to_index.get(field)
            if idx is not None and idx < len(row):
                value = row[idx]
                record[field] = str(value) if value is not None else None
            else:
                record[field] = None
        # Handle optional fields
        for field in optional_fields:
            idx = field_to_index.get(field)
            if idx is not None and idx < len(row):
                value = row[idx]
                record[field] = str(value) if value is not None else ""
            else:
                record[field] = ""
        result.append(record)
    return result
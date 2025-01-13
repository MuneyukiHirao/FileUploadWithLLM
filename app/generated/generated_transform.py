def transform_data(mapping, row_data):
    field_to_index = {}
    required_fields = ['distributorCode', 'CustomerName', 'AccountNumber']
    optional_fields = ['Rank', 'SalesPic', 'PartsSalesPic', 'ServicePic', 'BillingAddress1']
    for map_entry in mapping:
        field = map_entry.get('matchedField')
        index = map_entry.get('columnIndex')
        if field:
            field_to_index[field] = index
    output = []
    for i, row in enumerate(row_data):
        if i == 0:
            continue  # skip header
        row_dict = {}
        for field in required_fields:
            idx = field_to_index.get(field)
            if idx is not None and idx < len(row) and row[idx] != "":
                row_dict[field] = str(row[idx])
            else:
                row_dict[field] = None
        for field in optional_fields:
            idx = field_to_index.get(field)
            if idx is not None and idx < len(row) and row[idx] != "":
                row_dict[field] = str(row[idx])
            else:
                row_dict[field] = ""
        output.append(row_dict)
    return output
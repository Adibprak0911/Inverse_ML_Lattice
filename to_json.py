import openpyxl
import json

def excel_to_json_lattices(input_excel, output_json):
    wb = openpyxl.load_workbook(input_excel)
    sheet = wb.active

    headers = [cell.value for cell in sheet[1]]
    lattices = []

    for row in sheet.iter_rows(min_row=2, values_only=True):
        edge_dict = {}
        for i, val in enumerate(row):
            presence = 0
            if val is not None:
                try:
                    presence = int(val)
                except:
                    presence = 0
            key = headers[i]
            # Remove decimal from header if present (e.g. '3-4.1' -> '3-4')
            if '.' in key:
                key = key.split('.')[0]
            edge_dict[key] = presence  # keep as string
        lattices.append(edge_dict)

    with open(output_json, 'w') as f:
        json.dump(lattices, f, indent=2)  # Use json.dump, writes valid JSON

if __name__ == "__main__":
    excel_to_json_lattices('lattices.xlsx', 'lattices.json')
    print('Excel converted to lattices.json')

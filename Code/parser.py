import pandas as pd
import openpyxl
from pathlib import Path


def list_sheets(filepath: str):
    """List all sheet names in the Excel file."""
    workbook = openpyxl.load_workbook(filepath)
    print("Available sheets:")
    for i, sheet_name in enumerate(workbook.sheetnames, 1):
        print(f"  {i}. {sheet_name}")
    return workbook.sheetnames


def parse_iets_model(filepath: str) -> dict:
    """
    Parse IETS_ModelName_v6.xlsx and extract metadata and connectors sheets.
    
    Args:
        filepath: Path to the Excel file
        
    Returns:
        Dictionary with 'METADATA' and 'CONNECTORS' DataFrames
    """
    excel_file = Path(filepath)
    
    if not excel_file.exists():
        raise FileNotFoundError(f"File not found: {filepath}")
    
    result = {}
    
    # Read METADATA sheet (uppercase)
    try:
        result['METADATA'] = pd.read_excel(excel_file, sheet_name='METADATA')
        print(f"✓ Loaded 'METADATA' sheet: {result['METADATA'].shape}")
    except ValueError as e:
        print(f"⚠ Could not load 'METADATA' sheet: {e}")
    
    # Read CONNECTORS sheet (uppercase)
    try:
        result['CONNECTORS'] = pd.read_excel(excel_file, sheet_name='CONNECTORS')
        print(f"✓ Loaded 'CONNECTORS' sheet: {result['CONNECTORS'].shape}")
    except ValueError as e:
        print(f"⚠ Could not load 'CONNECTORS' sheet: {e}")
    
    return result


def main():
    # Path to the Excel file
    filepath = Path(__file__).parent.parent / "Base" / "IETS_ModelName_v6.xlsx"
    
    # Parse the file
    data = parse_iets_model(str(filepath))
    
    # Display summary
    print("\n=== METADATA ===")
    if 'METADATA' in data:
        print(data['METADATA'].head())
        print(f"\nShape: {data['METADATA'].shape}")
        print(f"\nColumns: {list(data['METADATA'].columns)}")
    
    print("\n=== CONNECTORS ===")
    if 'CONNECTORS' in data:
        print(data['CONNECTORS'].head())
        print(f"\nShape: {data['CONNECTORS'].shape}")
        print(f"\nColumns: {list(data['CONNECTORS'].columns)}")
    
    return data


if __name__ == "__main__":
    data = main()
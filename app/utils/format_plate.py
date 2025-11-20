"""
Format Plate Utility
Chuyển đổi biển số xe sang dạng chuẩn
Ví dụ: 12G500050 → 12-G5.00050
"""

import re
from typing import Optional


def standardize_plate(raw_plate: str) -> str:
    """
    Chuyển đổi biển số từ dạng OCR sang dạng chuẩn
    
    Dạng chuẩn: XX-XXXX.XX (hoặc XX-XXXXX.X)
    - 2 chữ số đầu (tỉnh): 10-99
    - Dấu gạch ngang (-)
    - Ký tự loại xe + 3 chữ số đầu serial
    - Dấu chấm (.)
    - Phần số serial còn lại
    
    Ví dụ:
    - "12G500050" → "12-G5000.50"
    - "51H123456" → "51-H1234.56"
    - "29-A1234.56" → "29-A1234.56" (đã chuẩn)
    - "12G1234.12" → "12-G1234.12" (đã chuẩn)
    
    Args:
        raw_plate (str): Biển số thô từ OCR
        
    Returns:
        str: Biển số đã chuẩn hóa
    """
    if not raw_plate:
        return ""
    
    # Loại bỏ khoảng trắng, chuyển thành chữ hoa
    plate = raw_plate.strip().upper()
    
    # Nếu đã có dấu "-" và ".", coi như đã chuẩn hóa
    if "-" in plate and "." in plate:
        return plate
    
    # Loại bỏ các ký tự đặc biệt không phải số và chữ
    plate = re.sub(r'[^A-Z0-9]', '', plate)
    
    if not plate or len(plate) < 8:
        # Nếu quá ngắn, trả về như cũ (không đủ để format)
        return plate
    
    try:
        # Chiết xuất các phần:
        # 2 chữ số đầu (tỉnh)
        province = plate[:2]
        
        # Phần còn lại
        rest = plate[2:]
        
        # Nếu bắt đầu bằng chữ
        if rest[0].isalpha():
            # Loại xe (1-2 ký tự)
            if len(rest) > 1 and rest[1].isalpha():
                vehicle_type = rest[:2]
                serial = rest[2:]
            else:
                vehicle_type = rest[0]
                serial = rest[1:]
            
            # Ensure serial có ít nhất 6 chữ số
            serial = serial.ljust(6, '0')[:6]  # Pad hoặc cắt thành 6 ký tự
            
            # Format: XX-XYYYY.ZZ (X=vehicle_type, YYYY+ZZ=serial)
            formatted = f"{province}-{vehicle_type}{serial[:4]}.{serial[4:6]}"
            
            return formatted
        else:
            # Nếu không có loại xe, cố gắng tách: XX + 1 + 7 chữ số
            if len(rest) >= 8:
                vehicle_code = rest[0]
                serial = rest[1:8]  # 7 chữ số
                return f"{province}-{vehicle_code}{serial[:4]}.{serial[4:6]}"
            else:
                return plate
    
    except (IndexError, ValueError):
        # Nếu lỗi, trả về biển số gốc
        return plate


def validate_plate_format(plate: str) -> bool:
    """
    Kiểm tra xem biển số có đúng định dạng chuẩn không
    
    Args:
        plate (str): Biển số cần kiểm tra
        
    Returns:
        bool: True nếu đúng format, False nếu không
    """
    # Format: XX-XXXX.XX (loại xe 1 ký tự + 4 ký tự serial, dấu chấm, 2 ký tự serial)
    # Hoặc: XX-XXXXX.X (loại xe 2 ký tự + 3 ký tự serial, dấu chấm, 1 ký tự serial)
    pattern = r'^\d{2}-[A-Z]{1,2}\d{4,5}\.?\d{1,2}$'
    return bool(re.match(pattern, plate))


def validate_plate(plate: str) -> dict:
    """
    Validate biển số toàn diện
    Kiểm tra format, độ dài, ký tự hợp lệ
    
    Args:
        plate (str): Biển số cần validate
        
    Returns:
        dict: {valid: bool, error: str or None, plate: standardized_plate}
    """
    if not plate:
        return {
            'valid': False,
            'error': 'Biển số không được để trống',
            'plate': ''
        }
    
    # Chuẩn hóa
    standardized = standardize_plate(plate)
    
    # Kiểm tra độ dài sau chuẩn hóa
    if len(standardized) < 10:  # Min: XX-X.XXX
        return {
            'valid': False,
            'error': f'Biển số quá ngắn: {standardized}',
            'plate': standardized
        }
    
    # Kiểm tra format
    if not validate_plate_format(standardized):
        return {
            'valid': False,
            'error': f'Format không hợp lệ: {standardized}',
            'plate': standardized
        }
    
    # Kiểm tra phần tỉnh (00-99)
    province = standardized[:2]
    if not (0 <= int(province) <= 99):
        return {
            'valid': False,
            'error': f'Mã tỉnh không hợp lệ: {province}',
            'plate': standardized
        }
    
    # Kiểm tra ký tự loại xe (chỉ A-Z)
    vehicle_part = standardized.split('-')[1].split('.')[0]
    if not all(c.isalpha() or c.isdigit() for c in vehicle_part):
        return {
            'valid': False,
            'error': f'Loại xe chứa ký tự không hợp lệ: {vehicle_part}',
            'plate': standardized
        }
    
    # Kiểm tra phần số serial (chỉ chữ số)
    serial = standardized.split('.')[-1]
    if not serial.isdigit():
        return {
            'valid': False,
            'error': f'Số serial chứa ký tự không hợp lệ: {serial}',
            'plate': standardized
        }
    
    # All checks passed
    return {
        'valid': True,
        'error': None,
        'plate': standardized
    }


def extract_plate_parts(plate: str) -> dict:
    """
    Tách biển số thành các phần
    
    Args:
        plate (str): Biển số (format chuẩn hoặc không)
        
    Returns:
        dict: {province, vehicle_type, serial}
    """
    # Chuẩn hóa trước
    standardized = standardize_plate(plate)
    
    # Pattern: XX-X(X).XXXXX
    match = re.match(r'^(\d{2})-([A-Z]{1,2}\d{1,2})\.(\d{3,5})$', standardized)
    
    if match:
        return {
            'province': match.group(1),
            'vehicle_type': match.group(2),
            'serial': match.group(3)
        }
    
    return {
        'province': '',
        'vehicle_type': '',
        'serial': ''
    }


# Test examples
if __name__ == "__main__":
    test_cases = [
        "12G500050",      # OCR → "12-G5000.50"
        "51H123456",      # OCR → "51-H1234.56"
        "29A1 23456",     # OCR → "29-A1234.56"
        "51-H1.23456",    # Already formatted (old style)
        "12-G5.00050",    # Already formatted (old style)
        "12-G1234.12",    # Already formatted (new style)
        "51-H1234.56",    # Already formatted (new style)
        "HCM12345",       # Invalid
        "29A12345",       # Valid OCR
        "12G50050",       # Too short
    ]
    
    print("Testing plate formatting:")
    print("-" * 80)
    for plate in test_cases:
        formatted = standardize_plate(plate)
        validation = validate_plate(formatted)
        is_valid = validation['valid']
        error = validation['error']
        parts = extract_plate_parts(plate)
        status = "✓" if is_valid else "✗"
        print(f"{status} Input: {plate:20} → Output: {formatted:20} Valid: {is_valid}")
        if error:
            print(f"    Error: {error}")

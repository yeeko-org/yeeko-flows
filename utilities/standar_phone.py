
import re


def standar_mx_phone(phone: str, raise_exeption = True) -> str:
    """
    For mexican phone numbers, standarize them to 521XXXXXXXXXX
    """
    phone = re.sub(r'[^0-9]', '', phone)
    if len(phone) == 10:
        return f"521{phone}"

    if len(phone) == 12 and phone[:2] == "52":
        return f"1{phone}"

    if len(phone) == 13 and phone[:3] == "521":
        return phone
    
    if raise_exeption:
        raise ValueError(f"Phone number {phone} is not valid")
    
    return phone

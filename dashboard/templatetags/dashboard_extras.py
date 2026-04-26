from django import template
import re

register = template.Library()

@register.filter(name='phone_format')
def phone_format(value):
    if not value:
        return ""
    
    # Limpiar solo dígitos
    digits = re.sub(r'\D', '', str(value))
    
    # Si tiene 10 dígitos, formatear como XX-XX-XX-XX-XX
    if len(digits) == 10:
        return "-".join([digits[i:i+2] for i in range(0, 10, 2)])
    
    # Si no, devolver original o limpio si es corto
    return value

@register.filter(name='clean_str')
def clean_str(value):
    if not value:
        return ""
    return str(value).strip().upper()

@register.filter(name='clean_phone')
def clean_phone(value):
    if not value:
        return ""
    return re.sub(r'\D', '', str(value))
@register.filter(name='replace_ok')
def replace_ok(value):
    if not value:
        return ""
    return str(value).replace(" OK", "").strip()

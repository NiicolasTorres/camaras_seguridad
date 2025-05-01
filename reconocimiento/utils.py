import re

def slugify_ip(ip: str) -> str:
    return re.sub(r'\.', '_', ip)
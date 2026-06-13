import hashlib, hmac, secrets, json, os, datetime
from core.paths import get_data_dir

SECRET_KEY = "Z3lzYWxTZWN1cml0eTIwMjU="

def generate_license_key(product="netguard", days=30):
    rand = secrets.token_hex(10).upper()
    key_part = "-".join(rand[i:i+5] for i in range(0, 20, 5))
    expiry = (datetime.datetime.now() + datetime.timedelta(days=days)).strftime("%Y%m%d")
    payload = key_part + expiry
    sig = hmac.new(SECRET_KEY.encode(), payload.encode(), hashlib.sha256).hexdigest()[:8].upper()
    return f"{key_part}-{expiry}-{sig}"

def validate_license(license_key, mac_address=None):
    parts = license_key.split("-")
    if len(parts) != 6:
        return False, "صيغة مفتاح غير صحيحة"
    key_part = "-".join(parts[:4])
    expiry_str = parts[4]
    sig_provided = parts[5]
    payload = key_part + expiry_str
    sig_computed = hmac.new(SECRET_KEY.encode(), payload.encode(), hashlib.sha256).hexdigest()[:8].upper()
    if sig_provided != sig_computed:
        return False, "مفتاح الترخيص غير صحيح"
    try:
        expiry_date = datetime.datetime.strptime(expiry_str, "%Y%m%d")
    except ValueError:
        return False, "تاريخ انتهاء غير صحيح"
    if datetime.datetime.now() > expiry_date:
        return False, "انتهت صلاحية الترخيص"
    lic_file = os.path.join(get_data_dir(), "license.json")
    data = {}
    if os.path.exists(lic_file):
        with open(lic_file, encoding="utf-8") as f:
            data = json.load(f)
    if data.get("key") == license_key:
        if data.get("mac") and mac_address and data["mac"] != mac_address:
            return False, "الترخيص مرتبط بجهاز آخر"
    elif mac_address:
        data = {"key": license_key, "mac": mac_address, "expires": expiry_str, "activated": datetime.datetime.now().isoformat()}
        os.makedirs(os.path.dirname(lic_file), exist_ok=True)
        with open(lic_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
    remaining = (expiry_date - datetime.datetime.now()).days
    return True, f"ساري المفعول — متبقي {remaining} يوم"

def get_license_info():
    lic_file = os.path.join(get_data_dir(), "license.json")
    if os.path.exists(lic_file):
        with open(lic_file, encoding="utf-8") as f:
            return json.load(f)
    return None
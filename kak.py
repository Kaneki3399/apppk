import requests
import os
from dotenv import load_dotenv
import hashlib

load_dotenv()
API_KEY = os.getenv('VIRUSTOTAL_API_KEY')
VT_URL = 'https://www.virustotal.com/vtapi/v2/file/scan'
REPORT_URL = 'https://www.virustotal.com/vtapi/v2/file/report'


def scan_and_report_file(file_hash=None):
    if file_hash:
        resource = file_hash
    else:
        raise ValueError("file_hash must be provided.")
    params = {'apikey': API_KEY, 'resource': resource}
    try:
        response = requests.get(REPORT_URL, params=params, timeout=10)  # Set a timeout
        report_response = response.json()
        return report_response
    except requests.exceptions.RequestException as e:
        print(f"Error contacting VirusTotal: {e}")
        raise


def scan_result(scans):
    clear = []
    detect = []

    for scanner, details in scans.items():
        if details['detected']:
            detect.append(scanner)
        else:
            clear.append(scanner)

    detect_str = ""
    result_string = ""
    if detect:
        for _ in detect:
            detect_str += '⛔️ ' + _ + '\n'
        result_string += f"Ushbu faylda virus borga o'xshaydi:\n{detect_str}"
    else:
        result_string = f"Ushbu fayl yangiga o'xshaydi birozdan so'ng tahlil natijalarni ulashamiz"

    return result_string


def get_hash(file_path, hash_algorithm='sha256'):
    hash_func = getattr(hashlib, hash_algorithm)()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_func.update(chunk)
    return hash_func.hexdigest()


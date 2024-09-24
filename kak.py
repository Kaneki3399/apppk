import requests
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv('VIRUSTOTAL_API_KEY')
VT_URL = 'https://www.virustotal.com/vtapi/v2/file/scan'
REPORT_URL = 'https://www.virustotal.com/vtapi/v2/file/report'


def scan_and_report_file(file_path):
    with open(file_path, 'rb') as file:
        files = {'file': (file_path, file)}
        params = {'apikey': API_KEY}
        response = requests.post(VT_URL, files=files, params=params)
        scan_response = response.json()
        resource = scan_response.get('resource')
        params = {'apikey': API_KEY, 'resource': resource}
        response = requests.get(REPORT_URL, params=params)
        report_response = response.json()
        return report_response


def scan_result(scans):
    clear = []
    detect = []

    for scanner, details in scans.items():
        if details['detected']:
            detect.append(scanner)
        else:
            clear.append(scanner)

    detect_str = ""
    clear_str = ""
    for _ in detect:
        detect_str += '⛔️ ' + _ + '\n'
    for _ in clear:
        clear_str += '✅ ' + _ + '\n'

    result_string = f"{detect_str}{clear_str}"

    return result_string


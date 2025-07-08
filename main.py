import requests
from bs4 import BeautifulSoup
import re

def download_apk(package_name):
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": f"https://apkpure.net/{package_name.replace('.', '-')}/{package_name}/download"
    }

    # Step 1: Get download page
    download_page = f"https://apkpure.net/{package_name.replace('.', '-')}/{package_name}/download"
    resp = requests.get(download_page, headers=headers)
    if resp.status_code != 200:
        print("[-] Failed to get download page")
        return

    # Step 2: Extract real .apk redirect URL
    soup = BeautifulSoup(resp.text, "html.parser")
    # Look for any <a> tag with href containing '/b/APK/'
    link = soup.find("a", href=re.compile(r"/b/APK/"))
    if not link:
        print("[-] Direct download link not found in page.")
        return

    redirect_url = link["href"]  # already full URL
    print(f"[+] Redirecting to: {redirect_url}")

    # Step 3: Follow redirect to final APK URL
    final = requests.get(redirect_url, headers=headers, allow_redirects=False)
    if final.status_code != 302 or "Location" not in final.headers:
        print("[-] Failed to get final APK link.")
        return

    apk_url = final.headers["Location"]
    print(f"[+] Final APK URL: {apk_url}")

    # Step 4: Download the APK
    apk_response = requests.get(apk_url, headers=headers, stream=True)
    if apk_response.status_code == 200:
        filename = f"{package_name}.apk"
        total = int(apk_response.headers.get("Content-Length", 0))
        with open(filename, "wb") as f:
            for chunk in apk_response.iter_content(chunk_size=1024*1024):
                if chunk:
                    f.write(chunk)
                    print(f"\r[+] Downloaded: {f.tell()}/{total} bytes", end="")
        print(f"\n[+] APK downloaded: {filename}")
    else:
        print("[-] Failed to download APK.")

# Example usage
download_apk("com.zerodha.varsity")

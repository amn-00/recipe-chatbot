"""Download the Recipe Box dataset (3 JSON files) into data/raw/."""
import io
import sys
import urllib.request
import zipfile
from pathlib import Path

URLS = ["https://eightportions.com/recipes_raw.zip"]
RAW =Path(__file__).resolve().parent.parent / "data" / "raw"


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    for url in URLS:
        try:
            print(f"Downloading {url} ...")
            request = urllib.request.Request(url, headers={"User-Agent": "recipe-chatbot-setup"})
            with urllib.request.urlopen(request, timeout=120) as resp:
                data = resp.read()
            with zipfile.ZipFile(io.BytesIO(data)) as z:
                names = [n for n in z.namelist() if n.endswith(".json")]
                for n in names:
                    (RAW / Path(n).name).write_bytes(z.read(n))
            print("Saved:", ", ".join(Path(n).name for n in names))
            return
        except Exception as e:
            print(f"  failed: {e}")
    sys.exit("Download failed. Get recipes_raw.zip from https://eightportions.com/datasets/Recipes/ "
             "and unzip the three JSON files into data/raw/.")


if __name__ == "__main__":
    main()

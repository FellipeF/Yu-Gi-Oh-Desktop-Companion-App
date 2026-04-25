import os
import time
import argparse
import subprocess

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--installer", required=True)
    args = parser.parse_args()

    if not os.path.exists(args.installer):
        print("[UPDATER] installer not found")
        return

    time.sleep(3)

    subprocess.Popen([
        args.installer,
        "/VERYSILENT",
        "/NORESTART",
        "/SUPPRESSMSGBOXES"
    ])

if __name__ == "__main__":
    main()
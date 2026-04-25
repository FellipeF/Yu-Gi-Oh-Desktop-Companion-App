import time
import argparse
import subprocess
import psutil

def wait_pid_close(pid, timeout=60):
    start = time.time()

    while time.time() - start < timeout:
        if not psutil.pid_exists(pid):
            return True
        time.sleep(1)

    return False

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--installer", required=True)
    parser.add_argument("--pid", required=True, type=int)
    args = parser.parse_args()

    wait_pid_close(args.pid)

    subprocess.Popen([
        args.installer,
        "/VERYSILENT",
        "/NORESTART",
        "/SUPPRESSMSGBOXES",
        "/CLOSEAPPLICATIONS",
        "/FORCECLOSEAPPLICATIONS"
    ])

if __name__ == "__main__":
    main()
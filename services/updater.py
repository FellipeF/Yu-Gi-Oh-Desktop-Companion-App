import os
import time
import argparse
import subprocess

def wait_and_replace(src, dst):
    """Replace exe safely with retry (Windows lock-safe)."""
    for i in range(15):
        try:
            if os.path.exists(dst):
                os.remove(dst)

            os.replace(src, dst)
            return True

        except PermissionError:
            time.sleep(1)

        except Exception as e:
            time.sleep(1)

    raise RuntimeError("Error replacing the .exe")


def restart_app(app_path):
    subprocess.Popen(
        [app_path],
        creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
        close_fds=True
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", required=True)
    parser.add_argument("--app", required=True)

    args = parser.parse_args()

    print("[UPDATER] target:", args.target)
    print("[UPDATER] app:", args.app)

    if not os.path.exists(args.target):
        print("[UPDATER] target doesn't exist")
        return

    # 3s delay so that app is closed before tring to replace
    time.sleep(3)

    wait_and_replace(args.target, args.app)
    restart_app(args.app)


if __name__ == "__main__":
    main()
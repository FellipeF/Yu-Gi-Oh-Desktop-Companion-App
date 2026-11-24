import logging

from app import App
from config import DEBUG_PERFORMANCE
from utils.performance_monitor import PerformanceMonitor


def main():
    logging.basicConfig(level=logging.INFO,format="%(asctime)s | %(levelname)s | ""%(name)s | %(message)s")

    app = App()

    if DEBUG_PERFORMANCE:
        monitor = PerformanceMonitor(app)
        monitor.start()

    app.mainloop()


if __name__ == "__main__":
    main()
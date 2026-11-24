import logging

from time import perf_counter

logger = logging.getLogger(__name__)

class PerformanceMonitor:

    def __init__(self, root, interval=100, threshold=50):
        self.root = root
        self.interval = interval
        self.threshold = threshold
        self.last_tick = None
        self.after_id = None

    def start(self):
        if self.after_id is None:
            self.last_tick = perf_counter()

            self.after_id = self.root.after(self.interval,self._tick)

    def _tick(self):
        now = perf_counter()

        delay = ((now - self.last_tick) * 1000 - self.interval)

        if delay > self.threshold:
            logger.warning("Tkinter event loop delayed by %.1f ms",delay)

        self.last_tick = now

        self.after_id = self.root.after(self.interval,self._tick)

    def stop(self):
        if self.after_id is not None:
            self.root.after_cancel(self.after_id)
            self.after_id = None
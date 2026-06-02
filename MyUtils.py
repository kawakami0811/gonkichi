import time

#　処理時間計測用ストップウォッチクラス
class StopWatch:
    def __init__(self, n_round=3):
        self.start_time = None
        self.end_time = None
        self.last_lap = None
        self.laps = []
        self.n_round = n_round

    def start(self):
        now = time.perf_counter()
        self.start_time = now
        self.last_lap = now
        self.laps = []
        self.end_time = None
        return self

    def lap(self, label=""):
        now = time.perf_counter()
        lap_time = now - self.last_lap
        self.last_lap = now
        self.laps.append((label, lap_time))
        return self

    def end(self):
        self.end_time = time.perf_counter()
        return self

    def elapsed(self):
        if self.start_time is None:
            return None
        if self.end_time is None:
            return time.perf_counter() - self.start_time
        return self.end_time - self.start_time

    def show(self, label=""):
        t = self.elapsed()
        if t is None:
            print("StopWatch: not started.")
            return None

        fmt = f"{{:.{self.n_round}f}}"
        if label:
            print(f"{label}: {fmt.format(t)} sec")
        else:
            print(f"{fmt.format(t)} sec")
        return round(t,self.n_round)

    def show_laps(self):
        fmt = f"{{:.{self.n_round}f}}"
        for i, (label, t) in enumerate(self.laps, 1):
            if label:
                print(f"Lap {i} ({label}): {fmt.format(t)} sec")
            else:
                print(f"Lap {i}: {fmt.format(t)} sec")
        return self.laps

import sys

class ProgressBar:
    def __init__(self, total: int, prefix: str = ''):
        self.prefix = prefix
        self.total = total
        self.current = 0

    def update(self, current: int = 1, progressText: str = ''):
        self.current += current
        percent = self.current / self.total
        bar_length = 50
        bar = '=' * int(percent * bar_length) + ' ' * (bar_length - int(percent * bar_length))
        sys.stdout.write(f'\r{self.prefix} [{bar}] {percent:.1%} {progressText}')
        sys.stdout.flush()

    def finish(self):
        bar = '=' * 50
        sys.stdout.write(f'\r{self.prefix} [{bar}] 100.0%\n')


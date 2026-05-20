import os, time
from datetime import datetime

def logTime(msg: str, level: str = "INF", print_this: bool = True):
    LOG_PATH = "log.txt"
    level_tag = level.upper()[:3]

    if print_this:
        print(f"[ {timestamp()} ] [{level_tag}]: {msg}")

    if not os.path.exists(LOG_PATH):
        with open(LOG_PATH, 'a', encoding='utf-8') as f:
            f.write(f'[ {timestamp()} ] [{level_tag}]: Log file created.')
    with open(LOG_PATH, 'a', encoding='utf-8') as f:
        f.write(f'\n[ {timestamp()} ] [{level_tag}]: {msg}')

def timestamp(datetime_ : datetime = None, format_="year-month-day hour:minute:second") -> str:
    if datetime_ == None:
        datetime_ = datetime.today()

    D_YYYY = f"{str(datetime_.year).zfill(4)}"
    D_MM = f"{str(datetime_.month).zfill(2)}"
    D_DD = f"{str(datetime_.day).zfill(2)}"
    T_HH = f"{str(datetime_.time().hour).zfill(2)}"
    T_MM = f"{str(datetime_.time().minute).zfill(2)}"
    T_SS = f"{str(datetime_.time().second).zfill(2)}"

    output = format_.lower()

    output = output.replace('year', D_YYYY)
    output = output.replace('month', D_MM)
    output = output.replace('day', D_DD)

    output = output.replace('hour', T_HH)
    output = output.replace('minute', T_MM)
    output = output.replace('second', T_SS)

    return output

class Stopwatch:
    # This class mainly speak in milliseconds not in seconds
    def __init__(self, Start : bool = True) -> None:
        self.StartTime : float = 0.0    # in seconds
        self.Duration : int = 0         # in ms
        if Start:
            self.StartTime = time.time()
    def Start(self):
        if not self.StartTime:
            self.StartTime = time.time()
    def Stop(self):
        # stop work just the same as pause
        if self.StartTime:
            self.Duration += int(float((time.time() - self.StartTime) * 1000).__round__())
            self.StartTime = 0.0
    def Reset(self):
        self.StartTime = 0.0
        self.Duration = 0
    def Get(self, returnType : str = 'ms', roundPoints : int = 2) -> int|float:
        returnType = returnType.lower()
        HoursAlias = ['h', 'hour', 'hours']
        MinutesAlias = ['m', 'min', 'minute', 'minutes']
        SecondsAlias = ['s', 'sec', 'second', 'seconds']
        MillisecondsAlias = ['ms', 'millisec', 'millisecond', 'milliseconds']
        if self.StartTime:
            self.Duration += int(float(((time.time() - self.StartTime) * 1000) - self.Duration).__round__())
        else:
            self.Duration = self.Duration
        if self.Duration:
            if returnType in MillisecondsAlias:
                return self.Duration
            elif returnType in SecondsAlias:
                return round(self.Duration / 1000, roundPoints)
            elif returnType in MinutesAlias:
                return round(self.Duration / 1000 / 60, roundPoints)
            elif returnType in HoursAlias:
                return round(self.Duration / 1000 / 60 / 60, roundPoints)
            else:
                return self.Duration
        return 0
    def GetStr(self, roundPoints : int = 2) -> str:
        if self.StartTime:
            self.Duration += int(float((time.time() - self.StartTime) * 1000).__round__())
            self.StartTime = 0.0
        if self.Duration:
            # return in ms
            if self.Duration > 3600000:
                return str(round(self.Duration / 1000 / 60 / 60, roundPoints)) + 'h'
            elif self.Duration > 120000:
                return str(round(self.Duration / 1000 / 60, roundPoints)) + 'm'
            elif self.Duration > 10000:
                return str(round(self.Duration / 1000, roundPoints)) + 's'
            else:
                return str(self.Duration) + 'ms'
        return '0ms'

# System Control Module

import psutil
import datetime
import os



def cpu_usage():
    usage = psutil.cpu_percent()
    return f"CPU usage is {usage}%"


def ram_usage():
    usage = psutil.virtual_memory().percent
    return f"RAM usage is {usage}%"


def battery_status():
    battery = psutil.sensors_battery()

    if battery:
        return f"Battery status is {battery.percent}%"

    return "Battery information unavailable."

def disk_usage():
    usage = psutil.disk_usage(os.getcwd()).percent
    return f"Disk usage is {usage}%"


def uptime():
    boot_time = psutil.boot_time()
    uptime_seconds = (datetime.datetime.now() - datetime.datetime.fromtimestamp(boot_time)).total_seconds()
    hours = uptime_seconds // 3600
    return f"System uptime is {int(hours)} hours"

def temperature():
    temps = psutil.sensors_temperatures()

    if not temps:
        return "Temperature sensors not available."

    for name, entries in temps.items():
        if entries:
            return f"CPU temperature: {entries[0].current}°C"

    return "Temperature unavailable."



def system_info(item):
    item = item.lower()

    if item == "cpu":
        return cpu_usage()
    elif item == "ram":
        return ram_usage()
    elif item == "battery":
        return battery_status()
    elif item == "disk":
        return disk_usage()
    elif item == "uptime":
        return uptime()
    elif item == "temp":
        return temperature()
    else:
        return "Unknown system info request."
#V0 -- All the operations under one roof.

import sys
import os
import time
from ubinascii import a2b_base64,b2a_base64


def _read_timeout(cnt, timeout_ms=2000):
    time_support = "ticks_ms" in dir(time)
    s_time = time.ticks_ms() if time_support else 0
    data = sys.stdin.read(cnt)
    if len(data) != cnt or (time_support and time.ticks_diff(time.ticks_ms(), s_time) > timeout_ms):
        return None
    return data


#https://stackoverflow.com/questions/13118029
def _deltree(target):
    for d in os.listdir(target):
        try:
            _deltree(target + '/' + d)
        except OSError:
            os.remove(target + '/' + d)

    os.rmdir(target)


def remove(file_name):
    suc = False
    try:
        os.remove(file_name)
        suc = True
    except:
        _deltree(file_name)
        suc = True

    sys.stdout.write("#0" if suc else "#4")

def listdir(mcu_folder):
       return [ chr(35+(os.stat(mcu_folder+fn)[0] == 32768))+fn
           for fn in os.listdir(mcu_folder[:-1])]

def upload(file_name):
    suc = False
    with open(file_name, "wb") as f:
        while True:
            d = _read_timeout(3)
            if not d or d[0] != "#":
                sys.stdout.write("#2")
                break
            cnt = int(d[1:3])
            if cnt == 0:
                suc = True
                break
            d = _read_timeout(cnt)
            if d:
                try:
                    f.write(a2b_base64(d))
                except OSError as e:
                    sys.stdout.write("#5")
                    sys.print_exception(e)
                    break
                else:
                    sys.stdout.write("#1")
            else:
                sys.stdout.write("#3")
                break
    sys.stdout.write("#0" if suc else "#4")


def download(file_name):
    if _read_timeout(3) != "###":
        return
    with open("file_name.py", "rb") as f:
        while True:
            chunk = f.read(48)
            if not chunk:
                break
            chunk = b2a_base64(chunk).strip()
            if isinstance(chunk, bytes):
                chunk = chunk.decode("ascii")
            cl = len(chunk)
            sys.stdout.write("".join(["#", "0" if cl < 10 else "", str(cl), chunk]))
            ack = _read_timeout(2)
            if not ack or ack != "#1":
                return

        # Mark end
        sys.stdout.write("#00")


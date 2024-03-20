import asyncio

from math import atan2, pi

from evdev import InputDevice, categorize, ecodes
import evdev

import mido

abss = {}

# 20 = pen x
# 21 = pen y
# 22 = pen pressure
# 23 = pen tilt
# 24 = pen angle

# 102 = finger x
# 103 = finger y
# 104 = finger count

CC_MOD = 1
CC_VOL = 7
CC_PAN = 10
CC_EXPR = 11
CC_SC2 = 71 # Allows shaping the Voltage Controlled Filter (VCF). Default = Resonance also (Timbre or Harmonics)
CC_SC5 = 74 #  	Controls VCFs cutoff frequency of the filter.

NOTE = 70 # static note

# codes:
# types 3
# 0 - x, 0..4095
# 1 - y, 0..4095
# 53 - x, 0..4095
# 54 - y, 0..4095
# 47 - touch count/ movement id, 0..5
# 48 - ??
# 49 - ??
# rest with type 1
# 330 - touch active, 0..1
# 333 - two fingers, 0..1
# 334 - three fingers, 0..1
# 335 - four fingers, 0..1
# 328 - five fingers, 0..1
def finger2midi(dev):
    port = mido.open_output('wacomidi', virtual=True)
    dev.grab()
    for event in dev.read_loop():
        t = event.type
        c = event.code
        v = event.value
        if t == 3:
            if c == 0:
                print(f"x = {v}")
                val = int((v/4096)*127)
                msg = mido.Message('control_change', channel=0, control=102, value=val, time=0)
                port.send(msg)
            if c == 1:
                print(f"y = {v}")
                val = int((v/4096)*127)
                msg = mido.Message('control_change', channel=0, control=103, value=val, time=0)
                port.send(msg)
        if t == 1:
            if c == 330:
                msg = mido.Message('control_change', channel=0, control=104, value=v, time=0)
                port.send(msg)
            if c == 333 and v == 1:
                msg = mido.Message('control_change', channel=0, control=104, value=2, time=0)
                port.send(msg)
            if c == 334 and v == 1:
                msg = mido.Message('control_change', channel=0, control=104, value=3, time=0)
                port.send(msg)
            if c == 335 and v == 1:
                msg = mido.Message('control_change', channel=0, control=104, value=4, time=0)
                port.send(msg)
            if c == 328 and v == 1:
                msg = mido.Message('control_change', channel=0, control=104, value=5, time=0)
                port.send(msg)

        #abss[(event.type,event.code)] = event.value
        #print(abss)


# codes:
# 0 - x, 0..31494
# 1 - y, 0..19685
# 24 - pressure, 0..2048
# 25 - height/tilt, 64 = out of range, 20 = touching the tablet, 0 = max tilt
# 26/27 - tilt angle. Maybe atan2 stuff?
# 40 - ?

# 320 using tip
# 321 using eraser

v26 = 0
v27 = 0

async def pen2midi(dev):

    global v26
    global v27


    port = mido.open_output('wacomidi', virtual=True)
    dev.grab()
    async for event in dev.async_read_loop():
        if (event.type == ecodes.EV_ABS):

            if (event.code == 0):
                val = int((event.value/31494)*127)
                msg = mido.Message('control_change', channel=0, control=20, value=val, time=0)
                yield msg
                #port.send(msg)

            elif (event.code == 1):
                val = int((event.value/19685)*127)
                msg = mido.Message('control_change', channel=0, control=21, value=val, time=0)
                yield msg
                #port.send(msg)

            elif (event.code == 24):
                val = int((event.value/2048)*127)

                if val > 2:
                    print("sending on")
                    msg = mido.Message('note_on', channel=0, note=NOTE, velocity=val)
                    yield msg
                    #port.send(msg)
                else:
                    print("sending off")
                    msg = mido.Message('note_off', channel=0, note=NOTE)
                    yield msg
                    #port.send(msg)
                #msg = mido.Message('control_change', channel=0, control=2, value=val, time=0)
                msg = mido.Message('control_change', channel=0, control=22, value=val, time=0)
                yield msg
                #port.send(msg)

            elif (event.code == 25):
                if (event.value < 20):
                    val = int(((20-event.value)/20)*127)
                    msg = mido.Message('control_change', channel=0, control=23, value=val, time=0)
                    yield msg
                    #port.send(msg)


            elif (event.code == 26):
                v26 = event.value
                a = -atan2(v27, v26)
                #print(f"angle: {a}")
                val = int(((a + pi) / (2*pi))*127)
                msg = mido.Message('control_change', channel=0, control=24, value=val, time=0)
                yield msg
                #port.send(msg)

            elif event.code == 27:
                v27 = event.value
                a = -atan2(v27, v26)
                #print(f"angle: {a}")
                val = int(((a + pi) / (2*pi))*127)
                msg = mido.Message('control_change', channel=0, control=24, value=val, time=0)
                yield msg
                #port.send(msg)

            else:
                pass
                #print(abss)
        else:
            print(event)

def find_pen_device():
    for evt in evdev.list_devices():
        dev = InputDevice(evt)
        if 'Wacom' in dev.name and 'Pen' in dev.name:
            return dev
    return None

def find_finger_device():
    for evt in evdev.list_devices():
        dev = InputDevice(evt)
        print(dev)
        if 'Wacom' in dev.name and 'Finger' in dev.name:
            return dev
    return None

def main():
    dev = find_pen_device()
    if dev:
        #pen2midi(dev)
        asyncio.ensure_future(pen2midi(dev))

    #dev = find_finger_device()
    #if dev:
    #    finger2midi(dev)

    loop = asyncio.get_event_loop()
    loop.run_forever()

if __name__ == '__main__':
    main()

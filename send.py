import os, psutil, serial, gc, struct, time
import mido
import serial_helper
from convert import parse

#buffer size = 1024
#command = b"A" + bytes(parse(msg))) MUST BE 9 BYTES LONG
#serial_device.write(command)

XOR = 0
STRUCT = struct.Struct("<H")#Struct different from convert script to facilicate wordswapping.

def separate_words(i):
    w1 = i & 0xFFFF
    w2 = (i >> 16) & 0xFFFF
    
    return w1,w2

if __name__ == "__main__":

    if(os.name == 'nt'):
        psutil.Process().nice(psutil.REALTIME_PRIORITY_CLASS)
    else:
        psutil.Process().nice(20)

    gc.disable()

    serial_port = serial_helper.select_serial_port()

    serial_device = serial.Serial(serial_port, 115200, timeout=0)

    serial_device.reset_input_buffer()

    serial_device.write(b"R")           #Reset command
    time.sleep(0.1)
    if(serial_device.read(2) != b'\x01R'):
        raise RuntimeError('Error during reset')
    serial_device.write(b"SAS\xcc\x00") #Setup run A for SNES with controllers
                                        #P1-1, P1-2, P2-1, P2-2 and no settings
    time.sleep(0.1)
    if(serial_device.read(2) != b'\x01S'):
        raise RuntimeError('Error during setup')

    print("TAStm32 initialized sucessfully.")
    midi = mido.MidiFile("midi.mid")
    gen = midi.play()
    print("Starting song playback.")
    while True:
        try:
            note, vol = parse(next(gen))
            if note != None and vol != None:
                w1, w2 = separate_words(note)
                w3, w4 = separate_words(vol)
                msg = b''.join((STRUCT.pack(w2), STRUCT.pack(w1), STRUCT.pack(w4), STRUCT.pack(w3)))
                serial_device.write(b"A" + bytes(msg))#This bytes might be redundant.
                print(b'A' + bytes(msg))
        except StopIteration:
            break
            

        

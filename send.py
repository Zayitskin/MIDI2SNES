import os, psutil, serial, gc, struct, time
import mido
import serial_helper
from convert import parse

#buffer size = 1024
#command = b"A" + bytes(parse(msg))) MUST BE 9 BYTES LONG
#serial_device.write(command)

XOR = 0
STRUCT = struct.Struct(">I")#Struct different from convert script to facilicate wordswapping.
PERMUTATION = [16,18,20,22,0,2,4,6,48,50,52,54,32,34,36,38,17,19,21,23,1,3,5,7,49,51,53,55,33,35,37,39,24,26,28,30,8,10,12,14,56,58,60,62,40,42,44,46,25,27,29,31,9,11,13,15,57,59,61,63,41,43,45,47]

def permute_bytes(b):
    c = [0]*8;
    for i in range(64):
        j = PERMUTATION[i]
        if (b[j//8] >> j%8) & 1:
            c[i//8] |= 1 << i%8
    return c;

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
                msg = bytes(permute_bytes(b''.join((STRUCT.pack(note), STRUCT.pack(vol)))))
                serial_device.write(b"A" + msg)
        except StopIteration:
            break
            

        

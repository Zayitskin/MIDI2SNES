import os, psutil, serial, gc, struct, time, zipfile, shutil
import mido
import serial_helper
from convert import parse

#buffer size = 1024
#command = b"A" + bytes(parse(msg))) MUST BE 9 BYTES LONG
#serial_device.write(command)

LSNES = 1
XOR = 0
STRUCT = struct.Struct(">I")#Struct different from convert script to facilicate wordswapping.
PERMUTATION = [16,18,20,22,0,2,4,6,48,50,52,54,32,34,36,38,17,19,21,23,1,3,5,7,49,51,53,55,33,35,37,39,24,26,28,30,8,10,12,14,56,58,60,62,40,42,44,46,25,27,29,31,9,11,13,15,57,59,61,63,41,43,45,47]
CYCLER = 1
CYCLE_DEPTH = 20 #Number of commnands between sample changes (not note_ons!)
SAMPLE_MAX = 63

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

    if LSNES == 0:
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
    else:
        f = open('input', 'w')
        print("***NOTE: You are in lsnes mode! If you want to use this with the TAStm32 replay device, please set LSNES=0 in send.py")
        time.sleep(4)
        for x in range(150):
            print("Writing frame "+str(framecounter)+" to input file")
            f.write("F|................|................|................|................\n")
            framecounter += 1
    midi = mido.MidiFile("midi.mid")
    gen = midi.play()
    print("Starting song playback.")
    framecounter = 1
    sample = 0
    cycler_count = 0
    while True:
        try:
            note, vol = parse(next(gen), sample)
            if note != None and vol != None:
                msg = bytes(permute_bytes(b''.join((STRUCT.pack(note), STRUCT.pack(vol)))))
                if CYCLER:
                    if cycle_count >= CYCLE_DEPTH:
                        cycle_count = 0
                        sample += 1
                        if sample > SAMPLE_MAX:
                            sample = 0
                    else:
                        cycle_count += 1
                if LSNES == 0:
                    serial_device.write(b"A" + msg)
                else:
                    f.write("F")
                    bits = ''
                    for x in range(8):
                        bits += format(msg[x], '#010b')[2:]
                    index = 0
                    for bit in bits:
                        if index % 16 == 0:
                            f.write("|")
                        if bit == '1':
                            f.write("x")
                        else:
                            f.write(".")
                        index += 1
                    f.write("\n")
                    print("Writing frame "+str(framecounter)+" to input file")
                    framecounter += 1
        except StopIteration:
            break
    
    if LSNES == 1:
        f.close()
        
        print("Updating null.lsmv....")
        # now we need to unzip, replace input, then rezip
        with zipfile.ZipFile('null.lsmv', 'r') as myzip:
            myzip.extractall("temp_") # unzip
        shutil.move("input","temp_\input") # replace
        with zipfile.ZipFile('null.lsmv', 'w') as myzip:
            for root, dirs, files in os.walk("temp_"):
                for file in files:
                    #rezip
                    #optional 2nd parameter ensures it is written in a flat structure
                    myzip.write(os.path.join(root, file),file)
        print("Updating Complete!")

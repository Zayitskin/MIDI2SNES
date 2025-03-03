import mido, struct
from collections import defaultdict as ddict

#("b'{}'".format(''.join('\\x{:02x}'.format(b) for b in STRUCT.pack(note))))

EMPTY_COMMAND = 0
STRUCT = struct.Struct(">I")

def parse(msg, sample = 1):

    msg = msg.dict()
    if msg["type"] == "note_on":
        return convert_note_on(msg["note"], sample), convert_volume(msg["velocity"], sample)
    elif msg["type"] == "note_off":
        return convert_note_off(msg["note"], sample), convert_volume(msg["velocity"], sample)
    else:
        return None, None
    
def convert_note_on(note, sample):

    msg = 1 << 31   # get_next_command = 1
    msg |= sample << 24  # sample_id = 1
    msg |= 1 << 16  # command_id = 1 (kon)
    msg |= note     # operand = note
    return msg

def convert_note_off(note, sample):

    msg = 1 << 31   # get_next_command = 1
    msg |= sample << 24  # sample_id = 1
    msg |= 2 << 16  # command_id = 2 (koff)
    msg |= note     # operand = note
    return msg

def convert_volume(vol, sample):

    msg = 1 << 31   # get_next_command = 1
    msg |= sample << 24  # sample_id = 1
    msg |= 6 << 16  # command_id = 6 (volB)
    msg |= vol      # operand = vol
    return msg
    

if __name__ == "__main__":
    song = mido.MidiFile("midi.mid")
    gen = song.play()
    with open("out", "wb") as f:
        while True:
            try:
                #TODO: Make this dump commands to binary file.
                note, vol = parse(next(gen))
                if note != None and vol != None:
                    f.write(STRUCT.pack(note))
                    f.write(STRUCT.pack(vol))
            except StopIteration:
                f.close()
                break
    print("Done.")

import quart


def calc_chksum(bitlist):
    # Berechnet die Checksumme anhand der Daten
    chksum_data = 0
    for i in range(12):
        chksum_data |= quart.quart(bitlist[(6 + i) * 4:(6 + i) * 4 + 4]) << 22 - 2 * i

    mask = 0x3331;
    chksum = 0x0;
    for i in range(24):
        if (chksum_data >> i) & 0x01:
            chksum ^= mask;
        msb = (mask >> 15) & 0x01
        mask = (mask << 1) & 0xFFFF
        if msb == 1:
            mask ^= 0x1021

    return chksum


def chksum(bitlist):
    # prüft die errechnete Checksumme gegen die übertragene
    # gibt das Ergebniss zurück, da es gleichzeitig die
    # zufällige ID des Senders ist

    chksum_data = calc_chksum(bitlist)

    chksum = 0
    for i in range(6):
        chksum |= quart.quart(bitlist[(18 + i) * 4:((18 + i) * 4) + 4]) << 14 - i * 2
    type = 'et732'
    chksum |= 0xFFFF & quart.quart(bitlist[24 * 4:(24 * 4) + 4]) << 2
    chksum |= 0xFFFF & quart.quart(bitlist[25 * 4:(25 * 4) + 4])

    chksum = (chksum_data & 0xffff) ^ chksum
    return type, chksum


def get_state(bitlist):
    # Wertet das Statusbye aus
    state = quart.quart(bitlist[6 * 4:6 * 4 + 4]) << 2
    state |= quart.quart(bitlist[7 * 4:7 * 4 + 4])
    if state == 7:
        return 'init'
    elif state == 2:
        return 'default'
    else:
        print('Unknown state:', state)
        return 'unknown ' + str(state)


def bitlist_to_int(bitlist):
    out = 0
    for bit in bitlist:
        out = (out << 1) | bit
    return out


def bitlist_to_hexlist(bitlist):
    # Gibt eine Bitliste als Hex aus
    # nützlich zum debuggen
    out = []
    max = int(len(bitlist) / 8)
    for i in range(max):
        out.append(hex(bitlist_to_int(bitlist[i * 8:i * 8 + 8])))
    return out


def get_data(bitlist):
    # Liest die Sensordaten aus dem Datenpaket aus
    sensor1 = 0
    sensor2 = 0

    for i in range(5):
        startbit = (4 - i) * 4
        sensor1 += quart.quart(bitlist[startbit + 32:startbit + 32 + 4]) * (1 << (2 * i))
        sensor2 += quart.quart(bitlist[startbit + 52:startbit + 52 + 4]) * (1 << (2 * i))

    if sensor1 == 0:
        sensor1 = ''
    else:
        sensor1 -= 532

    if sensor2 == 0:
        sensor2 = ''
    else:
        sensor2 -= 532

    return [sensor1, sensor2]

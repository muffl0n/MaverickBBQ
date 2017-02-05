def quart(raw):
    # 4 zu 2 Umwandlung
    if raw == [0, 1, 0, 1]:
        return 0
    elif raw == [0, 1, 1, 0]:
        return 1
    elif raw == [1, 0, 0, 1]:
        return 2
    elif raw == [1, 0, 1, 0]:
        return 3
    else:
        print('Error in Quart conversion', raw)
        return -1

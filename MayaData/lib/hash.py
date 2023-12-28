# import binascii  # python 2


def string_to_int(full_name):
    int_name = list()
    for i in list(filter(None, full_name.split('|'))):
        hex_name = i.encode('utf-8').hex()  # python 3
        # hex_name = binascii.hexlify(i)  # python 2
        int_name.append(int(hex_name, 16))
    return int_name

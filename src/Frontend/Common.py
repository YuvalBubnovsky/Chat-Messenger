import struct

"""
This is a class for potentially common methods between our server and client
"""


# Meanings in format, taken from https://docs.python.org/3/library/struct.html#struct-format-strings:
# '!'  -->   network         - ( i.e big endian )
# 'L'  -->   unsigned long   - ( 4 bytes )
# 'H'  -->   unsigned short  - ( 2 bytes )
# 'I   -->   unsigned int    - ( 4 bytes )

def transform_packet(seq_num, checksum, packet, cwnd):
    """
    This method uses the struct library to add bytes to a packet
    :param seq_num: a sequence number for RDT
    :param checksum: a checksum for the packet
    :param packet: a stream of bytes, prefferably using .encode()
    :param cwnd: the current window for RDT
    :return: a packet with 10 extra bytes at its start.
    """
    return struct.pack('!LHI', seq_num % ((1 << 16) - 1), int(checksum), int(cwnd)) + packet
    # seq_num with a binary modulo of (32,768 - 1)


def unpack_transformed_packet(packet):
    """
    Unpacks the packet using the struct library.
    returns a (sequence number, checksum, current window) tuple, packet  ( 2 items )
    :param packet: a transformed packet
    :return: tuple, packet
    """
    return struct.unpack('!LHI', packet[:10]), packet[10:]


def calc_checksum(packet):
    max_bit = 1 << 16  # 32,768
    numbers = []

    if len(packet) % 2 == 1:
        packet += bytes(1)  # adding padding of one byte in the case our packet is not of even length

    for i in range(0, len(packet), 2):
        number = packet[i] << 8  # shifts 8 bits to the left,
        number += packet[i + 1]  # making room for this number.
        numbers.append(number)

    _sum = 0
    for number in numbers:
        _sum += number
        sum1 = _sum % max_bit  # calculating carry
        sum2 = _sum // max_bit  # calculating with floor division
        _sum = sum1 + sum2

    checksum = max_bit - 1 - _sum  # checksum using one's complement.
    return checksum

import time
from . import main


def binary_clock_overlay(color=False):
    binary_time = get_bin_time()
    if color:
        main.draw_bin_number_main_menu(binary_time['hour'], 1, 14, 2)
        main.draw_bin_number_main_menu(binary_time['minute'], 4, 14, 1)
        main.draw_bin_number_main_menu(binary_time['second'], 7, 14, 0)
    else:
        main.draw_bin_number_main_menu(binary_time['hour'], 1, 14, 7)
        main.draw_bin_number_main_menu(binary_time['minute'], 4, 14, 7)
        main.draw_bin_number_main_menu(binary_time['second'], 7, 14, 7)


def get_bin_time():

    hour = time.localtime().tm_hour
    minute = time.localtime().tm_min
    second = time.localtime().tm_sec

    binary_time = {
        'hour': [dec_to_bin(hour // 10),
                 dec_to_bin(hour % 10)],
        'minute': [dec_to_bin(minute // 10),
                   dec_to_bin(minute % 10)],
        'second': [dec_to_bin(second // 10),
                   dec_to_bin(second % 10)]
    }

    return binary_time


def dec_to_bin(num):
    binstring = bin(num).replace("0b", "")
    binstring = binstring.rjust(4, '0')
    binlist = []
    for c in binstring:
        binlist.append(int(c))
    return binlist

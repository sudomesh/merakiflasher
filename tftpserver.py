#!/usr/bin/env python

import tftpy

if __name__ == "__main__":

    server = tftpy.TftpServer('./tftp_root/')
    server.listen('192.168.84.9', 69)

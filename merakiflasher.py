#!/usr/bin/env python

# Script for flashing e.g. OpenWRT onto Meraki Outdoor (a.k.a. Sparky)
# needs a 3.3v serial connection _and_ an ethernet connection

# Copyright 2013 Marc Juul
# License: GPLv3

#import tftpy
import serial
import re
import time

class Flasher:

    def readline(self):
        str = ''
        while True:
            ch = self.ser.read(1)
            if (ch == "\n") or (ch == "\r"):
                return str
            str += ch
            if re.match(".*\(y/n\)\?\s+$", str):
                return str
            if re.match("^RedBoot>\s+$", str):
                return str


    def writeslow(self, str):
        for ch in str:
            self.ser.write(ch)
            time.sleep(0.05)

    def __init__(self, ttyDevice, baudrate):
        print "initializing"
        self.ser = serial.Serial(ttyDevice, baudrate)

        self.cmds = {
            'part1': [
                "ip_address -l 192.168.84.1 -h 192.168.84.9",
                "fis init",
                "load -r -b 0x80041000 -m tftp -h 192.168.84.9 openwrt-atheros-vmlinux.gz",
                "fis create -r 0x80041000 -l 0x180000 -e 0x80041000 linux",
                "fis create -b 0xa81b0000 -l 0x620000 -f 0xa81b0000 -s 0x620000 -n rootfs",
                "fconfig -d boot_script_data\nfis load -d linux\nexec\n"
                ],
            'part2': [
                "load -r -b 0x80041000 -m tftp -h 192.168.84.9 openwrt-atheros-root.squashfs",
                "fis write -b 0x80041000 -l 0x210000 -f 0xa81b0000"
                ],
            'part3': [
                "load -r -b 0x80041000 -m tftp -h 192.168.84.9 openwrt-atheros-root.squashfs",
                "fis write -b 0x80251000 -l 0x200000 -f 0xa83c0000"
                ],
            'part4': [
                "load -r -b 0x80041000 -m tftp -h 192.168.84.9 openwrt-atheros-root.squashfs",
                "fis write -b 0x80451000 -l 0x200000 -f 0xa85c0000"
                ]
            }
        
    def expect(self, pattern):
        while True:
            got = self.readline()

            if re.match(pattern, got):
                return True

    def expect_prompt(self):
        return self.expect("^RedBoot>\s+$")
    
    def expect_yesno(self, pattern=None):
        while True:
            got = self.readline()

            if pattern:
                if re.match(pattern, got):
                    return True
            if re.match("^RedBoot>\s+$", got):

                return True
            if re.match(".*\(y/n\)\?.*$", got):
                self.ser.write("y\n")
        

    def set_progress(self, progress):
        self.send_command('alias flashprogress "'+progress+'"')

    def get_progress(self):
        self.writeslow("alias flashprogress\n")

        while True:
            result = self.readline()
            m = re.match("^'flashprogress' not found.*", result)
            if m:
                self.expect_prompt()
                return None
            m = re.match("'flashprogress' = '(.*)'.*", result)
            if m:
                self.expect_prompt()
                return m.group(1)

    def flash(self):
        while True:
            self.wait_for_boot()

            progress = self.get_progress()

            if progress == 'part1 complete':
                print "Flashing part 2 of 4"
                self.send_commands(self.cmds['part2'])
                self.set_progress('part2 complete')
            elif progress == 'part2 complete':
                print "Flashing part 3 of 4"
                self.send_commands(self.cmds['part3'])
                self.set_progress('part3 complete')
            elif progress == 'part3 complete':
                print "Flashing part 4 of 4"
                self.send_commands(self.cmds['part4'])
                self.set_progress('flashing complete')
            elif progress == 'flashing complete':
                print "Flashing complete! Please reboot your router."
                exit(0)
            else:
                print "Flashing part 1 of 4"
                self.send_commands(self.cmds['part1'])
                self.set_progress('part1 complete')

    def wait_for_boot(self):
        print "waiting for router to (re)boot"
        self.expect("^== Executing boot script in ")
        print "canceling factory standard boot script"
        self.writeslow("\x03\n")
        self.expect("^RedBoot>")
        
    def send_command(self, cmd):
        self.writeslow(cmd+"\n")
        self.expect_yesno()

    def send_commands(self, cmds):
        for cmd in cmds:
            self.send_command(cmd)
            time.sleep(1)
    

if __name__ == "__main__":
#    server = tftpy.TftpServer('./tftp_root/')
#    server.listen('192.168.84.9', 69)

    f = Flasher('/dev/ttyUSB0', 115200)
    f.flash()

#!/usr/bin/env python

# Script for flashing e.g. OpenWRT onto Meraki Outdoor (a.k.a. Sparky)
# needs a 3.3v serial connection _and_ an ethernet connection

# Copyright 2013 Marc Juul
# License: GPLv3

import serial
import subprocess
import re
import time
import sys

reflash = False

class Flasher:

    def debugPrint(self, str):
        if self.debug:
            print str

    def readline(self):
        str = ''
        while True:
            ch = self.ser.read(1)
            if (ch == "\n") or (ch == "\r"):
                if (len(str) > 0):
                    self.debugPrint("RECEIVED: " + str)
                return str
            str += ch
            if re.match(".*\(y/n\)\?\s+$", str):
                self.debugPrint("RECEIVED: " + str)
                return str
            if re.match("^RedBoot>\s+$", str):
                # self.debugPrint("RECEIVED: " + str)
                return str


    def writeslow(self, str):
        self.debugPrint("SENT: " + str.split('\n')[0])
        for ch in str:
            self.ser.write(ch)
            time.sleep(0.05)
        # TODO maybe read back remote echo before continuing?

    def __init__(self, ttyDevice, baudrate, reflash=False, debug=False):
        print "Opening serial device " + ttyDevice
        self.ser = serial.Serial(ttyDevice, baudrate)
        self.reflash = reflash
        self.debug = debug
        print "Flashing will take approximately 18 minutes"

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
             #   "load -r -b 0x80041000 -m tftp -h 192.168.84.9 openwrt-atheros-root.squashfs",
                "fis write -b 0x80041000 -l 0x210000 -f 0xa81b0000"
                ],
            'part3': [
             #   "load -r -b 0x80041000 -m tftp -h 192.168.84.9 openwrt-atheros-root.squashfs",
                "fis write -b 0x80251000 -l 0x200000 -f 0xa83c0000"
                ],
            'part4': [
             #   "load -r -b 0x80041000 -m tftp -h 192.168.84.9 openwrt-atheros-root.squashfs",
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

    def init_watchdog(self): # must do this or reset_watchdog has no effect
        self.writeslow("mfill -b 0xb1000098 -l 4 -p 0x00000043\n") # set gpio6 pin to OUTPUT

    def reset_watchdog(self): # must do this every 4.5 minutes to prevent reboot
        self.writeslow("mfill -b 0xb1000090 -l 4 -p 0x00000042\n") # set gpio6 high
        self.writeslow("mfill -b 0xb1000090 -l 4 -p 0x00000002\n") # set gpio6 low

    def flash(self):
        print "Ready to flash. Power on your router now."
        self.wait_for_boot()

        if self.reflash:
            print "Configuring router for reflash"
            self.set_progress('unflashed')
            self.reflash = False

        self.init_watchdog()

        while True:
            self.reset_watchdog()

            progress = self.get_progress()

            if progress == 'part1 complete':
                print "Flashing part 2 of 4 (~5 mins)"
                self.send_commands(self.cmds['part2'])
                self.set_progress('part2 complete')
            elif progress == 'part2 complete':
                print "Flashing part 3 of 4 (~5 mins)"
                self.send_commands(self.cmds['part3'])
                self.set_progress('part3 complete')
            elif progress == 'part3 complete':
                print "Flashing part 4 of 4 (~5 mins)"
                self.send_commands(self.cmds['part4'])
                self.set_progress('flashing complete')
            elif progress == 'flashing complete':
                print "Flashing complete! Booting into OpenWRT"
                print "Remember to change your baudrate to 9600"
                print "And put watchdog resetting into rc.local and crontab"
                self.send_command('reset')
                return True
            else:
                print "Flashing part 1 of 4 (~5 mins)"
                self.send_commands(self.cmds['part1'])
                self.set_progress('part1 complete')

    def wait_for_boot(self):
        print "waiting for router to (re)boot"
        self.expect("^== Executing boot script in ")
        print "Router bootup detected"
        self.writeslow("\x03")
        self.expect("^RedBoot>")
        
    def send_command(self, cmd):
        self.writeslow(cmd+"\n")
        self.expect_yesno()

    def send_commands(self, cmds):
        for cmd in cmds:
            self.send_command(cmd)
    

def usage():
    print __file__+" [-r] -d <serial_device>"
    print " "
    print " -r: reflash a device that was previously flashed"
    print " -d: enable debug output"
    print " "
    print "  example: "+__file__+" /dev/ttyUSB0"
    print " "

if __name__ == "__main__":

    serial_dev = None
    reflash = False
    debug = False

    if (len(sys.argv) < 2) or (len(sys.argv) > 4):
        usage()
        sys.exit(1)
       
    if len(sys.argv) == 4:
        if sys.argv[1] == '-r' or sys.argv[2] == '-r':
            reflash = True
        if sys.argv[1] == '-d' or sys.argv[2] == '-d':
            debug = True
    elif len(sys.argv) == 3:
        if sys.argv[1] == '-r':
            reflash = True
        if sys.argv[1] == '-d':
            debug = True

    serial_dev = sys.argv[len(sys.argv)-1]

    print "Starting tftp server"
    p = subprocess.Popen(["/usr/bin/python", "tftpserver.py"])

    try:
        f = Flasher(serial_dev, 115200, reflash=reflash, debug=debug)
        f.flash()
        print " "
        print " .__        ,         .    .            ,      . "
        print " [__) _ . .-+- _ ._.  |   *|_  _ ._. _.-+- _  _| "
        print " |  \(_)(_| | (/,[    |___|[_)(/,[  (_] | (/,(_] "
        print "    .        __..  ..__ .__..  ..___ __..  .      "
        print "    |_   .  (__ |  ||  \|  ||\/|[__ (__ |__|      "    
        print "    [_)\_|  .__)|__||__/|__||  |[___.__)|  |      "    
        print "       ._|                                        "

    finally:
        p.kill()
        p.wait()

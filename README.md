This is a program for flashing OpenWRT onto Meraki Outdoor (also known as Meraki Sparky board) units. It may work for other models, but it expects the hardware watchdog to reboot the router every five minutes. 

# Prerequisites

## Hardware

You need a USB to 3.3 volt serial adapter hooked up to the Meraki Outdoor. The pin header is already on there, but you'll have to open the case to get to it. Connect ground on the adapter to the ground pin on the Meraki board. Connect send on the adapter and to receive on the Meraki board, and connect receive on the adapter to send on the Meraki board. 

Connect the serial adapter. Connect an ethernet cable from your computer to the primary ethernet port on the Meraki board (the one closest to the power jack). Don't power on the board yet

## Software

You need wget, Python 2.6 and the python tftpy library. For Debian-based systems (e.g. Ubuntu) you can install these with:

```
sudo apt-get install python-tftpy wget
```

You also need OpenWRT images to flash onto the router. Download these by running:

```
./get_openwrt.sh
```

# Usage

First ensure that your ethernet adapter has the IP 192.168.84.9 and the netmask 255.255.255.0. You should also ensure that network-manager is not going to change your IP while you're flashing. If you're not sure how do this, you can use:

```
sudo /etc/init.d/network-manager stop
sudo ifconfig eth0 192.168.84.9 netmask 255.255.255.0 up
```

If your computer is connected to the internet, then you may loose your internet connectivity until you restart network manager.

To flash the device simply run merakiflasher.py:

```
sudo ./merakiflasher.py [-r] -d <serial_device>
  
  -r: reflash a device that was previously flashed
  -d: enable debug output
```

example:

```
sudo ./merakiflasher.py /dev/ttyUSB0
```

Now power up your router.

The flashing proceeds automatically, and takes about 20 minutes. The router will reboot four times.

After the script informs you that flashing is done, simply reboot the router. It should be reachable via telnet after boot. 

# Getting a root console

The baudrate on the Meraki is per default 115200 but at some point while booting the kernel OpenWRT will switch to a baudrate of 9600. You'll have to set your terminal program to a baudrate of 9600 to get a root console.

# Keeping the watchdog at bay

To prevent the watchdog from rebooting the meraki router, create a cron entry that runs the following script:

```
#!/bin/sh
/usr/bin/gpioctl dirout 6
/usr/bin/gpioctl set 6
/usr/bin/gpioctl clear 6
exit 0
```

Thanks to [Adrian Chadd for figuring this out](http://adrianchadd.blogspot.com/2014/03/meraki-sparky-boards-and-constant.html).

# License

The license of this software is GPLv3.


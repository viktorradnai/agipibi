#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  Copyright 2018 Viktor Radnai <viktor.radnai@gmail.com>
#
#  This file is part of Agipibi.
#
#  Agipibi is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  Agipibi is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with Agipibi.  If not, see <http://www.gnu.org/licenses/>.
#

from agipibi import Agipibi, AgipibiError

import sys
import logging
import argparse

logger = logging.getLogger(__name__)

CIC_ADDRESS=0x00
SCOPE_ADDRESS=0x0a

def parse_cmdline():
    parser = argparse.ArgumentParser(description='''
        TODO: insert description.'''
    )
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output')
    parser.add_argument('-q', '--quiet', action='store_true', help='Output errors only')
    parser.add_argument('-d', '--device', default='/dev/ttyUSB0', help='Serial device to use')
    args = parser.parse_args()

    if args.verbose: loglevel = logging.DEBUG
    elif args.quiet: loglevel = logging.ERROR
    else:            loglevel = logging.INFO

    logging.basicConfig(level=loglevel, format='%(asctime)s %(levelname)s %(message)s')

    return args


def main():

    args = parse_cmdline()

    # Open serial port with the Arduino.
    ctl = Agipibi(device=args.device, debug=False)

    if ctl.interface_ping():
        logger.info("Arduino is alive")
    else:
        logger.warn("No reponse to ping, you should reset the board")

    # Initialize bus lines and become Controller-In-Charge.
    # All lines will be put to HiZ except for NRFD asserted because we gave no
    # argument to the function, so we pause the Talker while setting up.
    # IFC is pulsed to gain CIC status.
    ctl.gpib_init(address=CIC_ADDRESS, controller=True)

    # Activate 'remote' mode of instruments (not required with this scope).
    # It asserts REN untill disabled with False or gpib_init() is called again.
    ctl.gpib_remote(True)

    # Clear all instruments on the bus.
    # Sends DCL when bus=True, reaching all devices. But it would use SDC
    # if bus=True and Listeners are set.
    ctl.gpib_clear(bus = True)

    logger.info("Get instrument ID")
    gpib_write(ctl, 'ID?')
    id = gpib_read(ctl)
    logger.info("ID: %s", id)

    try:
        while True:
            cmd = raw_input("agipibi> ")
            gpib_write(ctl, cmd)
            ret = gpib_read(ctl).strip()
            if ret != "\xff": print ret
    except EOFError:
        print # newline
        sys.exit(0)
    except KeyboardInterrupt:
        print # newline
        sys.exit(0)


def gpib_write(ctl, msg):
    cic_to_scope(ctl)
    ctl.gpib_write(msg)

def gpib_read(ctl):
    scope_to_cic(ctl)
    return ctl.gpib_read()


# Two functions to set direction of the communication.
def cic_to_scope(ctl):
    # Unaddress everyone.
    ctl.gpib_untalk()
    ctl.gpib_unlisten()
    # Set ourself as the Talker.
    ctl.gpib_talker(CIC_ADDRESS)
    # Scope will listen.
    ctl.gpib_listener(SCOPE_ADDRESS)

def scope_to_cic(ctl):
    # Unaddress everyone.
    ctl.gpib_untalk()
    ctl.gpib_unlisten()
    # Set scope as the Talker.
    ctl.gpib_talker(SCOPE_ADDRESS)
    # We'll listen for data.
    ctl.gpib_listener(CIC_ADDRESS)


# call main()
if __name__ == '__main__':
    main()


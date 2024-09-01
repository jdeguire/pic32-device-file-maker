#! /usr/bin/env python3
#
# Copyright (c) 2024, Jesse DeGuire
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification, are permitted
# provided that the following conditions are met:
# 
# * Redistributions of source code must retain the above copyright notice, this list of conditions
#   and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice, this list of
#   conditions and the following disclaimer in the documentation and/or other materials provided
#   with the distribution.
# 
# * Neither the name of the copyright holder nor the names of its contributors may be used to
#   endorse or promote products derived from this software without specific prior written
#   permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND
# FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
# IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT
# OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# #####
#
# atdf_reader.py
#
# This is a class that will read an XML file assuming it is an Atmel/Microchip ".atdf" file. It
# provides utility methods for accessing things like register and peripheral lists, getting CPU
# information, and the memory layout of the device. Data will be parsed and wrapped into data
# structures as needed. Allows us to handle different XML formats for device info, like Microchip's
# previous EDC file format.
#
# This class uses the default XML parsers in Python, which are vulnerable to certain attacks
# relying on XML entities referecing other entities multiple times. Specifically, the attacks are
# called "Billion Laughs" and "Quadratic Blowup". Therefore, you should ensure that the packs files
# you give to this module are really from Microchip and not some malicious user. See the info here:
# https://docs.python.org/3/library/xml.html#module-xml. That page has a link to a package called
# "defusedxml" you can use if you want to be safer. You should just need to get it from PIP and
# update the import statement for ElementTree below and in other modules to use it.
#

# On another note, I'm using this class to try out the Python type hints. I don't know what I'm
# doing, so I'm using the cheat sheet here for help: 
# https://mypy.readthedocs.io/en/stable/cheat_sheet_py3.html


from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import Element


#####
# TODO:
# Move these Device___ things into their own spot. I'll keep them here for now while I'm forming
# them, but they really should be somewhere else.
#
# Maybe this DeviceArch one should be more specific and have methods to get a high-level class.
#####
class DeviceArch(Enum):
    '''An enum of high-level architecture types currently supported.

    This is not very granular, so would be more useful for getting you the class of device rather
    than details. For example, this might indicates the device is some sort of Cortex-M device, but
    not whether this is an M7, M4, etc.
    '''
    Mips = 0
    CortexM = 1
    CortexA = 2
    RiscV32 = 3
    RiscV64 = 4
    Unknown = 5

@dataclass
class DeviceMemoryRegion:
    '''A data structure to represent a region of memory in the device.

    Memory regions are inside of address spaces and define regions of the space that are actually
    used and what they are used for, such as flash, RAM, or peripherals.
    '''
    name: str
    start_addr: int
    size: int


@dataclass
class DeviceAddressSpace:
    '''A data structure to represent an address space in a device, usually for memory vs fuses.

    A single address space can optionally have one or more memory regions in it. It is possible for
    other device elements, like peripherals, to provide their memory locations relative to an
    address space or memory region start, though whether that happens seems to depend on whether
    the device is a MIPS or ARM device. This address space distinction is probably more useful for
    Harvard Architecture devices with separate address spaces for flash and RAM.
    '''
    id: str
    start_addr: int
    size: int
    mem_regions: list[DeviceMemoryRegion] = field(default_factory=list[DeviceMemoryRegion])


class AtdfReader:
    # These are relative to the root element, which points to the top-level node
    # "avr-tools-device-file".
    device_path: str = 'devices/device'


    def __init__(self, atdf_path: Path) -> None:
        '''Create a new AtdfReader class instance with the given file assuming it is a valid ATDF
        file.

        This does not check that the file is really an ATDF file, but if not then many of the
        methods in this class simply will not work properly. Like the main comment in this file
        says, you need to ensure that the files you are giving this class are really from Microhip.
        '''
        self.path = atdf_path
        self.tree = ET.parse(self.path)
        self.root = self.tree.getroot()

    def get_device_name(self) -> str:
        '''Get the name of the device like you would see on a datasheet.

        This does not return the extra order codes for things like temperature rating or package
        type. For example, you would get back "ATSAME54P20A", not "ATSAME54P20A-CTU".
        '''
        element: Element = self.root.find(AtdfReader.device_path)

        if element:
            return element.get('name', default='')
        else:
            return ''

    def get_device_arch(self) -> DeviceArch:
        '''Get the high-level architecture of the device as a DeviceArch enum value.

        This will return the "Unknown" value if the architecture is not recognized.
        '''
        arch: DeviceArch = DeviceArch.Unknown
        element: Element = self.root.find(AtdfReader.device_path)
        
        if element:
            arch_str: str = element.get('architecture', default='').lower()

            if arch_str.startswith('mips'):
                arch = DeviceArch.Mips
            elif arch_str.startswith('cortex-m'):
                arch = DeviceArch.CortexM
            elif arch_str.startswith('cortex-a'):
                arch = DeviceArch.CortexA
            # Thsese RISC-V ones are just guesses for now. There are no files for RISC-V parts yet.
            elif arch_str.startswith('risc-v32'):
                arch = DeviceArch.RiscV32
            elif arch_str.startswith('risc-v64'):
                arch = DeviceArch.RiscV64

        return arch
    
    def get_device_memory(self) -> list[DeviceAddressSpace]:
        '''Get a list of address spaces in this device, which in turn may contain memory regions.
        '''
        memories: list[DeviceAddressSpace] = []
        element: Element = self.root.find(AtdfReader.device_path + '/address-spaces')

        if element:
            for space in element.findall('address-space'):
                # Start by getting the basic attributes for this address space.
                addr_space = DeviceAddressSpace(id=space.get('id', ''),
                                                start_addr=int(space.get('start', '0'), 0),
                                                size=int(space.get('size', '0'), 0))
                
                # Get any memory segments this space has and add them to this address space's list.
                for segment in space.findall('memory-segment'):
                    region = DeviceMemoryRegion(name=segment.get('name', ''),
                                                start_addr=int(segment.get('start', '0'), 0),
                                                size=int(segment.get('size', '0'), 0))
                    addr_space.mem_regions.append(region)

                memories.append(addr_space)

        return memories
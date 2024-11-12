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

'''device_info.py

This is a big dataclass that will encapsulate all of the necessary information about a device that
was read from a device file. The device file class, like AtdfReader, will have methods to let you
read these individual structures and one to read out everything into the big DeviceInfo structure.

This is a big structure, so here is a tree showing all of its members.

name : str
cpu : str
family : str
series : str
pincount : int
parameters : list[ParameterValue]
    name : str
    value : str
    caption : str
property_groups : list[PropertyGroup]
    name : str
    properties : list[ParameterValue]
        name : str
        value : str
        caption : str
address_spaces : list[DeviceAddressSpace]
    id : str
    start_addr : int
    size : int
    mem_regions: list[DeviceMemoryRegion]
        name : str
        start_addr : int
        size : int
        type : str
        page_size : int
        external : bool
peripherals : list[PeripheralGroup]
    name : str
    id : str
    version : str
    instances : list[PeripheralInstance]
        name : str
        reg_group_refs : list[RegisterGroupReference]
            instance_name : str
            module_name : str
            addr_space : str
            offset : int
        params : list[ParameterValue]
            name : str
            value : str
            caption : str
    reg_groups : list[RegisterGroup]
        name : str
        caption : str
        size : int
        modes : list[str]
        members : list[RegisterGroupMember]
            is_subgroup : bool
            name : str
            mode : str
            offset : int
            size : int
            count : int
            init_val : int
            caption : str
            fields : list[RegisterField]
                name : str
                caption : str
                mask : int
                modes : list[str]
                values : list[ParameterValue]
                    name : str
                    value : str
                    caption : str
interrupts : list[DeviceInterrupt]
    name : str
    index : int
    module_instance : str
    caption : str
event_generators : list[DeviceEvent]
    name : str
    index : int
    module_instance : str
event_users : list[DeviceEvent]
    name : str
    index : int
    module_instance : str
'''

from dataclasses import dataclass

@dataclass
class ParameterValue:
    '''A simple data structue containing general info about a device or peripheral. These will
    usually end up being turned into C macros or enum values the user can reference. Many elements
    in this file consist of (name, value, caption), so this data structure is used for those.
    '''
    name: str
    value: str
    caption: str        # This is a comment to explain the parameter

@dataclass
class DeviceMemoryRegion:
    '''A data structure to represent a region of memory in the device.

    Memory regions are inside of address spaces and define regions of the space that are actually
    used and what they are used for, such as flash, RAM, or peripherals.
    '''
    name: str
    start_addr: int
    size: int
    type: str           # Is it flash, RAM, other IO, and so on.
    page_size: int      # This appears to be non-zero for flash segments only
    external: bool      # Is this an external memory interface?


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
    mem_regions: list[DeviceMemoryRegion]

@dataclass
class RegisterGroupReference:
    '''A data structure to represent a reference to a register group.

    Peripheral instances have a list of register groups they use. The list has the name used for
    that instance, the name of the group as defined in the ATDF file, the address space in which
    it is located, and the offset within that space. The register group definitions are elsewhere
    and covered by the RegisterGroup type.
    '''
    instance_name: str
    module_name: str
    addr_space: str
    offset: int

@dataclass
class PeripheralInstance:
    '''A data structure to represent a single instance of a peripheral.

    These are grouped together using peripheral groups. All instances in a group will have the same
    registers, but of course they will be at difference memory addresses. Each instance will also
    have its own set of parameter macros.
    '''
    name: str           # "ADC0" vs "ADC1" and so on
    reg_group_refs: list[RegisterGroupReference]
    params: list[ParameterValue]

@dataclass
class RegisterField:
    '''A data structure representing a single bitfield in a register.
    '''
    name: str
    caption: str
    mask: int
    modes: list[str]
    values: list[ParameterValue]    # Enum values for the possible values of this field

@dataclass
class RegisterGroupMember:
    '''A data structure to represent a member of a register group.
    
    These are usually registers, but in rare case can actually be other register groups. The PORT
    peripheral on the SAME54 and newer PIC32C parts is like this.
    '''
    is_subgroup: bool               # False for registers, True for register subgroups
    name: str
    mode: str
    offset: int                     # The offset from the start of the instance
    size: int                       # Size in bytes
    count: int                      # Number of members in array
    init_val: int                   # Initial value
    caption: str                    # Description
    fields: list[RegisterField]

@dataclass
class RegisterGroup:
    '''A data structure to represent a set of registers grouped together in a peripheral.

    Most peripherals have only a single group with the same name as the peripheral, but a few have
    extra groups used to describe in-memory structures like DMA or CAN buffers.
    '''
    name: str
    caption: str
    size: int           # Might be used when count is non-zero to have padding between each set
    modes: list[str]    # Used for SERCOM because registers change based on SPI vs I2C vs whatever
    members: list[RegisterGroupMember]

@dataclass
class PeripheralGroup:
    '''A data structure to represent a group of peripherals of the same type.
    '''
    name: str           # The name you would use for the peripheral, like "ADC" or "SERCOM"
    id: str             # A unique ID used to distinguish, for example, different types of ADCs
    version: str
    instances: list[PeripheralInstance]
    reg_groups: list[RegisterGroup]

@dataclass
class DeviceInterrupt:
    '''A data structure to represent a single interrupt in a device.
    '''
    name: str
    index: int
    module_instance: str
    caption: str

@dataclass
class DeviceEvent:
    '''A data structure to represent a single event generator or user in a device.
    '''
    name: str
    index: int
    module_instance: str

@dataclass
class PropertyGroup:
    '''A data structure to represent a group of additional properties for a device provided by the
    XML file.
    '''
    name: str
    properties: list[ParameterValue]


@dataclass
class DeviceInfo:
    '''The top-level structure for device information, this will contain all of the above structures
    within it.
    '''
    name: str
    cpu: str
    family: str
    series: str
    pincount: int
    parameters: list[ParameterValue]
    property_groups: list[PropertyGroup]
    address_spaces: list[DeviceAddressSpace]
    peripherals: list[PeripheralGroup]
    interrupts: list[DeviceInterrupt]
    event_generators: list[DeviceEvent]
    event_users: list[DeviceEvent]

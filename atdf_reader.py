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
# Should these all be grouped into a big "Device" structure?
#
# Maybe this DeviceArch one should be more specific and have methods to get a high-level class.
#
# Maybe don't even bother with this enum and just return a string for the arch-speicifc classes to
# handle.
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
class ParameterValue:
    '''A simple data structue containing general info about a device or peripheral. These will
    usually end up being turned into C macros or enum values the user can reference. Many elements
    in this file consist of (name, value, caption), so this data structure is used for those.
    '''
    name: str
    value: int
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
class PeripheralInstance:
    '''A data structure to represent a single instance of a peripheral.

    These are grouped together using peripheral groups. All instances in a group will have the same
    registers, but of course they will be at difference memory addresses. Each instance will also
    have its own set of parameter macros.
    '''
    name: str           # "ADC0" vs "ADC1" and so on
    addr_space: str     # The address space in which this is located
    offset: int         # The offset from the start of the address space
    params: list[ParameterValue]

@dataclass
class RegisterField:
    '''A data structure representing a single bitfield in a register.
    '''
    name: str
    caption: str
    mask: int
    values: list[ParameterValue]    # Enum values for the possible values of this field

@dataclass
class PeripheralRegister:
    '''A data structure to represent a single register in a peripheral.
    '''
    name: str
    mode: str
    offset: int                     # The offset from the start of the instance
    size: int                       # Size in bytes
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
    offset: int         # Will usually be zero since the register offset is usually enough
    count: int          # Used for some GPIO peripherals to create an array of register sets
    modes: list[str]    # Used for SERCOM because registers change based on SPI vs I2C vs whatever
    regs: list[PeripheralRegister]

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


class AtdfReader:
    # These are relative to the root element, which points to the top-level node
    # "avr-tools-device-file".
    device_path: str = 'devices/device'
    modules_path: str = 'modules'


    def __init__(self, atdf_path: Path) -> None:
        '''Create a new AtdfReader class instance with the given file assuming it is a valid ATDF
        file.

        This does not check that the file is really an ATDF file, but if not then many of the
        methods in this class simply will not work properly. Like the main comment in this file
        says, you need to ensure that the files you are giving this class are really from Microhip.
        '''
        self.path: Path = atdf_path
        self.tree = ET.parse(self.path)
        self.root: Element = self.tree.getroot()


    def get_str(e: Element, name: str, default: str = '') -> str:
        '''A convenience method for reading a string attribute with a configurable defualt.
        '''
        return e.get(name, default)

    def get_int(e: Element, name: str, default: int = 0) -> int:
        '''A convenience method for reading an integer attribute with a configurable default.
        '''
        attr: str = e.get(name)
        if attr is not None:
            return int(attr, 0)     # last 0 tells int() to figure out base automatically
        else:
            return default


    def get_device_name(self) -> str:
        '''Get the name of the device like you would see on a datasheet.

        This does not return the extra order codes for things like temperature rating or package
        type. For example, you would get back "ATSAME54P20A", not "ATSAME54P20A-CTU".
        '''
        element: Element = self.root.find(AtdfReader.device_path)

        if element is not None:
            return AtdfReader.get_str(element, 'name')
        else:
            return ''

    def get_device_arch(self) -> DeviceArch:
        '''Get the high-level architecture of the device as a DeviceArch enum value.

        This will return the "Unknown" value if the architecture is not recognized.
        '''
        arch: DeviceArch = DeviceArch.Unknown
        element: Element = self.root.find(AtdfReader.device_path)
        
        if element is not None:
            arch_str: str = AtdfReader.get_str(element, 'architecture').lower()

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
    
    def get_device_family(self) -> str:
        '''Get the family of the device, such as "SAME", "PIC32CX", and so on.

        This will return an empty string if the family is not found.
        '''
        element: Element = self.root.find(AtdfReader.device_path)

        if element is not None:
            return AtdfReader.get_str(element, 'family')
        else:
            return ''

    def get_device_memory(self) -> list[DeviceAddressSpace]:
        '''Get a list of address spaces in this device, which in turn may contain memory regions.
        '''
        start_element: Element = self.root.find(AtdfReader.device_path + '/address-spaces')

        if start_element is None:
            return []

        memories: list[DeviceAddressSpace] = []

        for space_element in start_element.findall('address-space'):
            regions: list[DeviceMemoryRegion] = []

            # Get any memory segments this space.
            for segment_element in space_element.findall('memory-segment'):
                region = DeviceMemoryRegion(name = AtdfReader.get_str(segment_element, 'name'),
                                            start_addr = AtdfReader.get_int(segment_element, 'start'),
                                            size = AtdfReader.get_int(segment_element, 'size'),
                                            type = AtdfReader.get_str(segment_element, 'type'),
                                            page_size = AtdfReader.get_int(segment_element, 'pagesize'))
                regions.append(region)

            # Get the address space info and add the regions we found.
            addr_space = DeviceAddressSpace(id = AtdfReader.get_str(space_element, 'id'),
                                            start_addr = AtdfReader.get_int(space_element, 'start'),
                                            size = AtdfReader.get_int(space_element, 'size'),
                                            mem_regions = regions)
            
            memories.append(addr_space)

        return memories
    
    def get_device_parameters(self) -> list[ParameterValue]:
        '''Get a list of parameters (C macros containing info) for the device itself.
        '''
        start_element: Element = self.root.find(AtdfReader.device_path + '/parameters')

        if start_element is None:
            return []

        params: list[ParameterValue] = []

        for param_element in start_element.findall('param'):
            pv = ParameterValue(name = AtdfReader.get_str(param_element, 'name'),
                                value = AtdfReader.get_int(param_element, 'value'),
                                caption = AtdfReader.get_str(param_element, 'caption'))
            params.append(pv)

        return params

    def get_peripheral_groups(self) -> list[PeripheralGroup]:
        '''Get a list of the peripheral groups for the device.

        Each peripheral group will contain one or more instances of the peripheral and the register
        definitions used by all of the instances.
        '''
        start_element: Element = self.root.find(AtdfReader.device_path + '/peripherals')

        if start_element is None:
            return []

        periph_groups: list[PeripheralGroup] = []

        for module_element in start_element.findall('module'):
            group = PeripheralGroup(name = AtdfReader.get_str(module_element, 'name'),
                                    id = AtdfReader.get_str(module_element, 'id'),
                                    version = AtdfReader.get_str(module_element, 'version'),
                                    instances = self._get_peripheral_instances(module_element),
                                    reg_groups = self._get_register_groups(module_element))
            periph_groups.append(group)

        return periph_groups
    
    def get_interrupts(self) -> list[DeviceInterrupt]:
        '''Get a list of all interrupts on the device.
        '''
        start_element: Element = self.root.find(AtdfReader.device_path + '/interrupts')

        if start_element is None:
            return []

        interrupt_list: list[DeviceInterrupt] = []

        for interrupt_element in start_element.findall('interrupt'):
            di = DeviceInterrupt(name = AtdfReader.get_str(interrupt_element, 'name'),
                                 index = AtdfReader.get_int(interrupt_element, 'index'),
                                 module_instance = AtdfReader.get_str(interrupt_element, 'module-instance'),
                                 caption = AtdfReader.get_str(interrupt_element, 'caption'))
            interrupt_list.append(di)

        return interrupt_list

    def get_event_generators(self) -> list[DeviceEvent]:
        '''Get a list of event generators on the device.
        '''
        start_element: Element = self.root.find(AtdfReader.device_path + '/events/generators')

        if start_element is None:
            return []

        events_list: list[DeviceEvent] = []

        for event_element in start_element.findall('generator'):
            de = DeviceEvent(name = AtdfReader.get_str(event_element, 'name'),
                             index = AtdfReader.get_int(event_element, 'index'),
                             module_instance = AtdfReader.get_str(event_element, 'module_instance'))
            events_list.append(de)
        
        return events_list

    def get_event_users(self) -> list[DeviceEvent]:
        '''Get a list of event users on the device.
        '''
        start_element: Element = self.root.find(AtdfReader.device_path + '/events/users')

        if start_element is None:
            return []

        events_list: list[DeviceEvent] = []

        for event_element in start_element.findall('user'):
            de = DeviceEvent(name = AtdfReader.get_str(event_element, 'name'),
                             index = AtdfReader.get_int(event_element, 'index'),
                             module_instance = AtdfReader.get_str(event_element, 'module_instance'))
            events_list.append(de)
        
        return events_list

    def get_device_propertes(self) -> list[PropertyGroup]:
        '''Get a list of property groups for the device.

        These are similar to device parameters like you would get with get_device_parameters(), but
        are listed separately and in groups in the XML file for some reason.
        '''
        start_element: Element = self.root.find(AtdfReader.device_path + '/property-groups')

        if start_element is None:
            return []

        propgroups: list[PropertyGroup] = []

        for propgroup_element in start_element.findall('property-group'):
            group_name = AtdfReader.get_str(propgroup_element, 'name')
            group_props: list[ParameterValue] = []

            for prop_element in propgroup_element.findall('property'):
                pv = ParameterValue(name = AtdfReader.get_str(prop_element, 'name'),
                                    value = AtdfReader.get_int(prop_element, 'value'),
                                    caption = AtdfReader.get_str(prop_element, 'caption'))
                group_props.append(pv)
            
            propgroups.append(PropertyGroup(name = group_name, properties = group_props))
        
        return propgroups


    def _get_peripheral_instances(self, module_element: Element) -> list[PeripheralInstance]:
        '''Get a list of peripheral instances for the peripheral referred to by the given Element.

        This is a private method. You should call 'get_peripheral_groups()' to get all the info
        you will need for the device peripherals.
        '''
        instances: list[PeripheralInstance] = []

        for inst_element in module_element.findall('instance'):
            inst_name: str = AtdfReader.get_str(inst_element, 'name')
            inst_addr_space: str = 'base'
            inst_offset: int = 0
            inst_params: list[ParameterValue] = []

            reg_group: Element = inst_element.find('register-group')
            if reg_group is not None:
                inst_addr_space = AtdfReader.get_str(reg_group, 'address-space')
                inst_offset = AtdfReader.get_int(reg_group, 'offset')

            parameters: Element = inst_element.find('parameters')
            if parameters is not None:
                for param_element in parameters.findall('param'):
                    pv = ParameterValue(name = AtdfReader.get_str(param_element, 'name'),
                                        value = AtdfReader.get_int(param_element, 'value'),
                                        caption = AtdfReader.get_str(param_element, 'caption'))
                    inst_params.append(pv)

            instance = PeripheralInstance(name = inst_name,
                                          addr_space = inst_addr_space,
                                          offset = inst_offset,
                                          params = inst_params)
            instances.append(instance)

        return instances
    
    def _get_register_groups(self, periph_name: str) -> list[RegisterGroup]:
        '''Get a list of register groups for the peripheral with the given name (ADC, CAN, etc.).

        This is a private method. You should call 'get_peripheral_groups()' to get all the info
        you will need for the device peripherals.
        '''        
        # First find the module element corresponding to our desired peripheral.
        start_element: Element = self.root.find(AtdfReader.modules_path)        
        module_element: Element = self._find_element_with_name_attr(start_element,
                                                                    'module',
                                                                    periph_name)
        if module_element is None:
            return []

        register_groups: list[RegisterGroup] = []

        group_elements: list[Element] = module_element.findall('register-group')
        done_elements: list[Element] = []

        # A register group can point at another group to say "I'm made up of 4 of this other
        # group" for example. Find all groups that do this and handle those first. In practice,
        # this seems to be very rare. The PORT peripheral in the SAME54 is an example.
        for indirect_group in group_elements:
            redirect_element: Element = indirect_group.find('register-group')

            if redirect_element is not None:
                real_name: str = AtdfReader.get_str(redirect_element, 'name')
                real_group: Element = self._find_element_with_name_attr(module_element,
                                                                        'register-group',
                                                                        real_name)

                group_modes: list[str] = []
                for mode_element in real_group.findall('mode'):
                    group_modes.append(AtdfReader.get_str(mode_element, 'name'))

                rg = RegisterGroup(name = AtdfReader.get_str(indirect_group, 'name'),
                                   caption = AtdfReader.get_str(indirect_group, 'caption'),
                                   offset = AtdfReader.get_int(redirect_element, 'offset'),
                                   count = AtdfReader.get_int(redirect_element, 'count'),
                                   modes = group_modes,
                                   regs = self._get_registers_from_group(module_element, real_group))
                register_groups.append(rg)

                done_elements.append(indirect_group)
                done_elements.append(real_group)

        # Any elements we already handled in the above loop need to be removed from the group list
        # so we don't process them again.
        for done in done_elements:
            group_elements.remove(done)

        # Now finish up by processing everything else.
        for group in group_elements:
            group_modes: list[str] = []
            for mode_element in group.findall('mode'):
                group_modes.append(AtdfReader.get_str(mode_element, 'name'))

            rg = RegisterGroup(name = AtdfReader.get_str(group, 'name'),
                               caption = AtdfReader.get_str(group, 'caption'),
                               offset = 0,
                               count = 0,
                               modes = group_modes,
                               regs = self._get_registers_from_group(module_element, group))
            register_groups.append(rg)

        return register_groups

    def _get_registers_from_group(self,
                                  module_element:Element,
                                  group_element: Element) -> list[PeripheralRegister]:
        '''Get the register definitions for the register group referred to by the given Element.

        The peripheral module element is also needed because that is used when getting info about
        the bitfields in the register.

        This is a private method. You should call 'get_peripheral_groups()' to get all the info
        you will need for the device peripherals.
        '''
        group_regs: list[PeripheralRegister] = []

        for reg_element in group_element.findall('register'):
            reg = PeripheralRegister(name = AtdfReader.get_str('name'),
                                     mode = AtdfReader.get_str('modes'),
                                     offset = AtdfReader.get_int('offset'),
                                     size = AtdfReader.get_int('size'),
                                     init_val = AtdfReader.get_int('initval'),
                                     caption = AtdfReader.get_str('caption'),
                                     fields = self._get_register_fields(module_element, reg_element))
            group_regs.append(reg)

        return group_regs

    def _get_register_fields(self, module_element: Element, reg_element: Element) -> list[RegisterField]:
        '''Get the definitions of the bitfields within the given register, including the list of
        possible values if that is provided.

        The peripheral module of which the given register is a memeber is also needed to get the
        list of possible values for the register if those are provided.
        
        This is a private method. You should call 'get_peripheral_groups()' to get all the info
        you will need for the device peripherals.
        '''
        reg_fields: list[RegisterField] = []

        for field_element in reg_element.findall('bitfield'):
            values_name: str = field_element.get('values')
            values_list: list[ParameterValue] = []

            if values_name is not None:
                values_element: Element = self._find_element_with_name_attr(module_element,
                                                                            'value-group',
                                                                            values_name)

                if values_element is not None:
                    for val_element in values_element.findall('value'):
                        val = ParameterValue(name = AtdfReader.get_str(val_element, 'name'),
                                             value = AtdfReader.get_int(val_element, 'value'),
                                             caption = AtdfReader.get_str(val_element, 'caption'))
                        values_list.append(val)

            rf = RegisterField(name = AtdfReader.get_str(field_element, 'name'),
                               caption = AtdfReader.get_str(field_element, 'caption'),
                               mask = AtdfReader.get_int(field_element, 'mask'),
                               values = values_list)
            reg_fields.append(rf)

        return reg_fields

    def _find_element_with_name_attr(self, start_element: Element, 
                                     subelement_name: str, value: str) -> Element:
        '''Search under the starting element for the first subelement with a 'name' attribute that
        matches the given attribute value or None if one could not be found.
        '''
        if start_element is None:
            return None

        for subelement in start_element.findall(subelement_name):
            attr = subelement.get('name')
            if attr is not None and attr == value:
                return subelement
            
        return None

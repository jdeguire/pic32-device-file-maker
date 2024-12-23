#! /usr/bin/env python3
#
# Copyright (c) 2024, Jesse DeGuire
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

'''atdf_reader.py

This module contains the AtdfReader class to read an XML file assuming it is an Atmel/Microchip
".atdf" file. It provides utility methods for accessing things like register and peripheral lists,
getting CPU information, and the memory layout of the device. Data will be parsed and wrapped into
data structures as needed. Allows us to handle different XML formats for device info, like
Microchip's previous EDC file format.

This class uses the default XML parsers in Python, which are vulnerable to certain attacks
relying on XML entities referecing other entities multiple times. Specifically, the attacks are
called "Billion Laughs" and "Quadratic Blowup". Therefore, you should ensure that the packs files
you give to this module are really from Microchip and not some malicious user. See the info here:
https://docs.python.org/3/library/xml.html#module-xml. That page has a link to a package called
"defusedxml" you can use if you want to be safer. You should just need to get it from PIP and
update the import statement for ElementTree below and in other modules to use it.
'''

# On another note, I'm using this class to try out the Python type hints. I don't know what I'm
# doing, so I'm using the cheat sheet here for help: 
# https://mypy.readthedocs.io/en/stable/cheat_sheet_py3.html


from device_info import *
from pathlib import Path
import re
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import Element


class AtdfReader:
    # These are relative to the root element, which points to the top-level node
    # "avr-tools-device-file".
    variants_path: str = 'variants'
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


    @staticmethod
    def get_str(e: Element, name: str, default: str = '') -> str:
        '''A convenience method for reading a string attribute with a configurable defualt.
        '''
        return e.get(name, default)


    @staticmethod
    def get_int(e: Element, name: str, default: int = 0) -> int:
        '''A convenience method for reading an integer attribute with a configurable default.
        '''
        attr: str | None = e.get(name)
        if attr is not None:
            return int(attr, 0)     # last 0 tells int() to figure out base automatically
        else:
            return default


    @staticmethod
    def get_bool(e: Element, name: str, default: bool = False) -> bool:
        '''A convenience method for reading a Boolean attribute with a configurable default.
        '''
        attr: str | None = e.get(name)
        if attr is not None:
            if 'true' == attr.lower():
                return True
            else:
                return False
        else:
            return default


    def get_all_device_info(self) -> DeviceInfo:
        '''Return a DeviceInfo structure with all of the info from below functions added to it.
        '''
        return DeviceInfo(name = self.get_device_name(),
                          cpu = self.get_device_cpu(),
                          family = self.get_device_family(),
                          series = self.get_device_series(),
                          pincount = self.get_device_pincount(),
                          parameters = self.get_device_parameters(),
                          property_groups = self.get_device_propertes(),
                          address_spaces = self.get_device_memory(),
                          peripherals = self.get_peripheral_groups(),
                          interrupts = self.get_interrupts(),
                          event_generators = self.get_event_generators(),
                          event_users = self.get_event_users())


    def get_device_name(self) -> str:
        '''Get the name of the device like you would see on a datasheet.

        This does not return the extra order codes for things like temperature rating or package
        type. This will also return "SAM..." instead 'ATSAM..." for Atmel devices. For example, you
        would get back "SAME54P20A", not "ATSAME54P20A-CTU" or "ATSAME54P20A".
        '''
        element: Element | None = self.root.find(AtdfReader.device_path)

        if element is not None:
            name = AtdfReader.get_str(element, 'name')
            if name.upper().startswith('ATSAM'):
                return name[2:]
            else:
                return name
        else:
            return ''


    def get_device_cpu(self) -> str:
        '''Get the cpu name of the device as a lower-case string, such as "mips" or "cortex-m4".

        This will return an empty string if the cpu name was not found.
        '''
        element: Element | None = self.root.find(AtdfReader.device_path)
        
        if element is not None:
            # The tag is "architecture", but we use that to refer to ARMv7-M vs ARMv8M whereas the
            # ATDF files use that to refer to what we are calling the CPU name. Our usage matches
            # how LLVM and GCC options work.
            return AtdfReader.get_str(element, 'architecture').lower()
        else:
            return ''
    

    def get_device_family(self) -> str:
        '''Get the family of the device, such as "SAME", "PIC32CX", and so on.

        This will return an empty string if the family is not found.
        '''
        element: Element | None = self.root.find(AtdfReader.device_path)

        if element is not None:
            return AtdfReader.get_str(element, 'family')
        else:
            return ''


    def get_device_series(self) -> str:
        '''Get the family of the device, such as "SAME54", "PIC32CXSG41", and so on.

        This will return an empty string if the family is not found.
        '''
        element: Element | None = self.root.find(AtdfReader.device_path)

        if element is not None:
            return AtdfReader.get_str(element, 'series')
        else:
            return ''


    def get_device_pincount(self) -> int:
        '''Get the number of pins on the device or 0 if this info could not be found.

        Some devices, like the PIC32MX795F512L, are available in packages of different sizes even
        though the number of usable pins (100 in this case) remains the same. This will use the
        package with the lowest pin count to determine the number of pins.
        '''
        element: Element | None = self.root.find(AtdfReader.variants_path)

        if element is None:
            return 0
        else:
            min_pincount = 999999
            for variant_element in element.findall('variant'):
                package = AtdfReader.get_str(variant_element, 'package')
                match = re.search(r'\d+$', package)

                if match:
                    package_pins = int(match.group())
                    if package_pins < min_pincount:
                        min_pincount = package_pins

            if 999999 == min_pincount:
                return 0
            else:
                return min_pincount


    def get_device_memory(self) -> list[DeviceAddressSpace]:
        '''Get a list of address spaces in this device, which in turn may contain memory regions.
        '''
        start_element: Element |None = self.root.find(AtdfReader.device_path + '/address-spaces')

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
                                            page_size = AtdfReader.get_int(segment_element, 'pagesize'),
                                            external = AtdfReader.get_bool(segment_element, 'external'))
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
        start_element: Element | None = self.root.find(AtdfReader.device_path + '/parameters')

        if start_element is None:
            return []

        params: list[ParameterValue] = []

        for param_element in start_element.findall('param'):
            pv = ParameterValue(name = AtdfReader.get_str(param_element, 'name'),
                                value = AtdfReader.get_str(param_element, 'value'),
                                caption = AtdfReader.get_str(param_element, 'caption'))
            params.append(pv)

        return params


    def get_peripheral_groups(self) -> list[PeripheralGroup]:
        '''Get a list of the peripheral groups for the device.

        Each peripheral group will contain one or more instances of the peripheral and the register
        definitions used by all of the instances.
        '''
        start_element: Element | None = self.root.find(AtdfReader.device_path + '/peripherals')

        if start_element is None:
            return []

        periph_groups: list[PeripheralGroup] = []

        for module_element in start_element.findall('module'):
            module_name = AtdfReader.get_str(module_element, 'name')
            group = PeripheralGroup(name = module_name,
                                    id = AtdfReader.get_str(module_element, 'id'),
                                    version = AtdfReader.get_str(module_element, 'version'),
                                    instances = self._get_peripheral_instances(module_element),
                                    reg_groups = self._get_register_groups(module_name))
            periph_groups.append(group)

        return periph_groups


    def get_interrupts(self) -> list[DeviceInterrupt]:
        '''Get a list of all interrupts on the device.
        '''
        start_element: Element | None = self.root.find(AtdfReader.device_path + '/interrupts')

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
        start_element: Element | None = self.root.find(AtdfReader.device_path + '/events/generators')

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
        start_element: Element | None = self.root.find(AtdfReader.device_path + '/events/users')

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
        start_element: Element | None = self.root.find(AtdfReader.device_path + '/property-groups')

        if start_element is None:
            return []

        propgroups: list[PropertyGroup] = []

        for propgroup_element in start_element.findall('property-group'):
            group_name = AtdfReader.get_str(propgroup_element, 'name')
            group_props: list[ParameterValue] = []

            for prop_element in propgroup_element.findall('property'):
                pv = ParameterValue(name = AtdfReader.get_str(prop_element, 'name'),
                                    value = AtdfReader.get_str(prop_element, 'value'),
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
            inst_group_refs: list[RegisterGroupReference] = []
            inst_params: list[ParameterValue] = []

            for group_element in inst_element.findall('register-group'):
                rgr = RegisterGroupReference(instance_name = AtdfReader.get_str(group_element, 'name'),
                                             module_name = AtdfReader.get_str(group_element, 'name-in-module'),
                                             addr_space = AtdfReader.get_str(group_element, 'address-space'),
                                             offset = AtdfReader.get_int(group_element, 'offset'))
                inst_group_refs.append(rgr)

            parameters: Element | None = inst_element.find('parameters')
            if parameters is not None:
                for param_element in parameters.findall('param'):
                    pv = ParameterValue(name = AtdfReader.get_str(param_element, 'name'),
                                        value = AtdfReader.get_str(param_element, 'value'),
                                        caption = AtdfReader.get_str(param_element, 'caption'))
                    inst_params.append(pv)

            instance = PeripheralInstance(name = inst_name,
                                          reg_group_refs = inst_group_refs,
                                          params = inst_params)
            instances.append(instance)

        return instances


    def _get_register_groups(self, periph_name: str) -> list[RegisterGroup]:
        '''Get a list of register groups for the peripheral with the given name (ADC, CAN, etc.).

        This is a private method. You should call 'get_peripheral_groups()' to get all the info
        you will need for the device peripherals.
        '''        
        # First find the module element corresponding to our desired peripheral.
        start_element: Element | None = self.root.find(AtdfReader.modules_path)        
        module_element: Element | None = self._find_element_with_name_attr(start_element,
                                                                            'module',
                                                                            periph_name)
        if module_element is None:
            return []

        register_groups: list[RegisterGroup] = []

        for group in module_element.findall('register-group'):
            group_modes: list[str] = []
            for mode_element in group.findall('mode'):
                group_modes.append(AtdfReader.get_str(mode_element, 'name'))

            rg = RegisterGroup(name = AtdfReader.get_str(group, 'name'),
                               caption = AtdfReader.get_str(group, 'caption'),
                               size = AtdfReader.get_int(group, 'size'),
                               modes = group_modes,
                               members = self._get_register_group_members(module_element, group))
            register_groups.append(rg)

        return register_groups


    def _get_register_group_members(self,
                                    module_element:Element,
                                    group_element: Element) -> list[RegisterGroupMember]:
        '''Get the members for the register group referred to by the given Element, which can be
        either a register definition or a reference to another group.

        The peripheral module element is also needed because that is used when getting info about
        the bitfields in the register.

        This is a private method. You should call 'get_peripheral_groups()' to get all the info
        you will need for the device peripherals.
        '''
        group_members: list[RegisterGroupMember] = []

        for member in group_element:
            if 'register-group' == member.tag:
                # This group member is a reference to another group. This is used to add another
                # layer of indirection to a set of registers. For example, the PORT peripheral on
                # some parts uses this to denote an array of a group with one for each port.

                ref = RegisterGroupMember(is_subgroup = True,
                                          name = AtdfReader.get_str(member, 'name'),
                                          module_name = AtdfReader.get_str(member, 'name-in-module'),
                                          mode = AtdfReader.get_str(member, 'modes'),
                                          offset = AtdfReader.get_int(member, 'offset'),
                                          size = AtdfReader.get_int(member, 'size'),
                                          count = AtdfReader.get_int(member, 'count'),
                                          init_val = 0,
                                          caption = AtdfReader.get_str(member, 'caption'),
                                          fields = [])
                group_members.append(ref)
            elif 'register' == member.tag:
                # This group member is a register.

                reg = RegisterGroupMember(is_subgroup = False,
                                          name = AtdfReader.get_str(member, 'name'),
                                          module_name = '',
                                          mode = AtdfReader.get_str(member, 'modes'),
                                          offset = AtdfReader.get_int(member, 'offset'),
                                          size = AtdfReader.get_int(member, 'size'),
                                          count = AtdfReader.get_int(member, 'count'),
                                          init_val = AtdfReader.get_int(member, 'initval'),
                                          caption = AtdfReader.get_str(member, 'caption'),
                                          fields = self._get_register_fields(module_element, member))
                group_members.append(reg)

        return group_members


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
            values_name: str | None = field_element.get('values')
            values_list: list[ParameterValue] = []

            if values_name is not None:
                values_element: Element | None = self._find_element_with_name_attr(module_element,
                                                                                   'value-group',
                                                                                    values_name)

                if values_element is not None:
                    for val_element in values_element.findall('value'):
                        val = ParameterValue(name = AtdfReader.get_str(val_element, 'name'),
                                             value = AtdfReader.get_str(val_element, 'value'),
                                             caption = AtdfReader.get_str(val_element, 'caption'))
                        values_list.append(val)

            field_modes_str = AtdfReader.get_str(field_element, 'modes')
            field_modes: list[str] = []
            if field_modes_str:
                field_modes = field_modes_str.split()

            rf = RegisterField(name = AtdfReader.get_str(field_element, 'name'),
                               caption = AtdfReader.get_str(field_element, 'caption'),
                               mask = AtdfReader.get_int(field_element, 'mask'),
                               modes = field_modes,
                               values = values_list)
            reg_fields.append(rf)

        return reg_fields


    def _find_element_with_name_attr(self, start_element: Element | None, 
                                     subelement_name: str, value: str) -> Element | None:
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

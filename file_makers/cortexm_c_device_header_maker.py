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

'''cortexm_c_device_header_maker.py

Contains a single public function to make a C device-specific header file for a single Arm Cortex-M
device. This is the header you would include in a project for your processor.
This is based on the sample headers found in Arm CMSIS 6 at
https://github.com/ARM-software/CMSIS_6/blob/main/CMSIS/Core/Template/Device_M/Include/.
'''

from device_info import *
from . import strings
from . import version
import textwrap
from typing import IO


def run(devinfo: DeviceInfo, outfile: IO[str]) -> None:
    '''Make a C header file for the given device assuming is a a PIC or SAM Cortex-M device.
    '''
    outfile.write(_get_file_prologue(devinfo.name))
    outfile.write('\n')

    outfile.write('/* ----- Interrupt Number Enumeration ----- */\n')
    outfile.write(_get_interrupt_enum(devinfo.interrupts))
    outfile.write('\n\n')

    outfile.write('/* ----- Core Configuration Macros ----- */\n')
    outfile.write(_get_parameter_macros(devinfo.parameters))
    outfile.write('\n\n')

    if devinfo.property_groups:
        outfile.write('/* ----- Device Property Macros ----- */\n')
    
        for prop_group in devinfo.property_groups:
            outfile.write(_get_parameter_macros(prop_group.properties))

        outfile.write('\n\n')

    outfile.write('/* ----- Address Space Macros ----- */\n')
    outfile.write(_get_memory_region_macros(devinfo.address_spaces))
    outfile.write('\n\n')

    outfile.write('/* ----- CMSIS Core and Peripherals Header ----- */\n')
    outfile.write('#include <cortex_' + devinfo.arch.split('-')[1].lower() + '.h>\n')
    outfile.write('\n\n')

    outfile.write('/* ----- Device Peripheral Headers ----- */\n')
    outfile.write(_get_peripheral_headers(devinfo.peripherals))
    outfile.write('\n\n')

    outfile.write('/* ----- Device Peripheral Address Macros ----- */\n')
    outfile.write(_get_peripheral_address_macros(devinfo.peripherals, devinfo.address_spaces))
    outfile.write('\n\n')

    outfile.write('/* ----- Device Peripheral Instance Parameters ----- */\n')
    for periph in devinfo.peripherals:
        if _peripheral_is_special(periph):
            continue

        for instance in periph.instances:
            outfile.write('// ' + instance.name + '\n')
            outfile.write(_get_parameter_macros(instance.params, instance.name + '_'))
    outfile.write('\n\n')

#TODO: We will need special handling for device fuses.
    outfile.write(_get_file_epilogue(devinfo.name))


def _get_file_prologue(devname: str) -> str:
    '''Return a string with the file prologue, which is stuff like license info, include guards,
    the extern "C" declaration, and other things at the top of the file.
    '''
    prologue: str = ''

    # Write the header block with copyright info.
    prologue += '/*\n'
    prologue += strings.get_generated_by_string(' * ')
    prologue += ' * \n'
    prologue += strings.get_cmsis_apache_license(' * ')
    prologue += ' */\n\n'

    # Include guard
    prologue += f'#ifndef {devname.upper()}_H_\n'
    prologue += f'#define {devname.upper()}_H_\n\n'

    # File version
    # For now, make this the same as our version
    fm_version: list[str] = version.FILE_MAKER_VERSION.split('.')
    prologue += f'#define FILE_VERSION_STR   "{version.FILE_MAKER_VERSION}"\n'
    prologue += f'#define FILE_VERSION_MAJOR ({fm_version[0]})\n'
    prologue += f'#define FILE_VERSION_MINOR ({fm_version[1]})\n'
    prologue += f'#define FILE_VERSION_PATCH ({fm_version[2]})\n\n'

    # extern "C"
    prologue += '#ifdef __cplusplus\n'
    prologue += 'extern "c" {\n'
    prologue += '#endif\n'

    return prologue

def _get_interrupt_enum(interrupts: list[DeviceInterrupt]) -> str:
    '''Return a string containing a C enum that provides values for all of the device interrupts.
    '''
    enum_str: str = textwrap.dedent('''
        typedef enum IRQn
        {
        ''')

    for interrupt in interrupts:
        name = interrupt.name + '_IRQn'
        index = interrupt.index
        caption = interrupt.caption
        enum_str += f'    {name :<24} = {index :>3}, /* {caption} */\n'

    enum_str += '} IRQn_Type;\n'

    return enum_str

def _get_parameter_macros(parameters: list[ParameterValue], prefix: str = '') -> str:
    '''Return a string containing C macros defining the given parameters and their values.
    '''
    macros: str = ''

    for param in parameters:
        macro_name = prefix + param.name
        macro_value = '(' + param.value + ')'

        if param.caption:
            macros += f'#define {macro_name :<32} {macro_value :<16} /* {param.caption} */\n'
        else:
            macros += f'#define {macro_name :<32} {macro_value}\n'

    return macros

def _get_memory_region_macros(address_spaces: list[DeviceAddressSpace]) -> str:
    '''Return a string containing C macros defining the locations and sizes of the memory regions
    on the device.
    '''
    region_str: str = ''

    for addr_space in address_spaces:
        for mem_region in addr_space.mem_regions:
            base = addr_space.start_addr + mem_region.start_addr
            base_macro_name = mem_region.name.upper() + '_BASE'
            region_str += f'#define {base_macro_name :<32} (0x{base :08X}UL)\n'

            size = mem_region.size
            size_macro_name = mem_region.name.upper() + '_SIZE'
            region_str += f'#define {size_macro_name :<32} (0x{size :08X}UL)\n'

            page_size = mem_region.page_size
            pagesize_macro_name = mem_region.name.upper() + '_PAGESIZE'
            region_str += f'#define {pagesize_macro_name :<32} ({page_size}UL)\n\n'

    return region_str

def _get_peripheral_headers(peripherals: list[PeripheralGroup]) -> str:
    '''Return a string containing include declarations for this devices' peripherals, not including
    device fuses or core peripherals.
    '''
    periph_str: str = ''

    for periph in peripherals:
        if not _peripheral_is_special(periph):
            name = periph.name.lower()
            id = periph.id.lower()
            periph_str += f'#include "periph/{name}_{id}.h"\n'

    return periph_str

def _get_peripheral_address_macros(peripherals: list[PeripheralGroup], 
                                   address_spaces: list[DeviceAddressSpace]) -> str:
    '''Return a string containing macros that define the location of peripheral instances on the
    device.

    The macros also cast the address to a pointer to a device-specific structure. These do not
    include device fuses or core peripherals. 
    '''
    macros: str = ''

    for periph in peripherals:
        if _peripheral_is_special(periph):
            continue

        for instance in periph.instances:
            for group_ref in instance.reg_group_refs:
                macro_name = group_ref.instance_name.upper() + '_REGS'
                macro_type = group_ref.module_name.lower() + '_regs_t'
                macro_addr = (group_ref.offset + 
                              _find_start_of_address_space(address_spaces, group_ref.addr_space))

                macros += f'#define {macro_name :<32} ((volatile {macro_type}*)0x{macro_addr :08X})\n'

    return macros


def _get_file_epilogue(devname: str) -> str:
    '''Return a string with the file epilogue, which is the stuff at the end of the file like
    the end of the include guard and extern "C" statements that were at the top.
    '''
    epilogue: str = ''

    # extern "C"
    epilogue += '#ifdef __cplusplus\n'
    epilogue += '}\n'
    epilogue += '#endif\n\n'

    # Include guard
    epilogue += f'#endif /* {devname.upper()}_H_ */\n'

    return epilogue

def _peripheral_is_special(periph: PeripheralGroup) -> bool:
    '''Return True if the given peripheral is special and thus would require handling different
    from other peripherals.

    Currently, these are device fuses and core peripherals. Fuses need to be defined in a special
    location in flash whereas other peripherals look like predefined RAM addresses. Core peripherals
    like SysTick are already defined in the CMSIS device header ("cortex-mNN.h") and do not need to
    be defined here.
    '''
    if 'fuses' == periph.name.lower():
        return True

    # Check this becaus a peripheral might not have any register groups associated with them.
    # It's weird, but we probably do not need to do anything special with these.
    if not periph.instances[0].reg_group_refs:
        return False

    # Core peripherals are at addres 0xE0000000 and above.
    # This just checks the first group of the first instance we have, which should be fine.
    if periph.instances[0].reg_group_refs[0].offset >= 0xE0000000:
        return True
    
    return False

def _find_start_of_address_space(addr_spaces: list[DeviceAddressSpace], name: str) -> int:
    '''Search the list of address spaces for the one with the given name and return its start
    address.

    Returns 0 if the named space is not found.
    '''
    for space in addr_spaces:
        if name == space.id:
            return space.start_addr

    return 0
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

'''arm_c_device_header_maker.py

Contains a single public function to make a C device-specific header file for a single Arm Cortex-M
device. This is the header you would include in a project for your processor.
This is based on the sample headers found in Arm CMSIS 6 at
https://github.com/ARM-software/CMSIS_6/blob/main/CMSIS/Core/Template/Device_M/Include/.
'''

from device_info import *
from . import strings
from . import version
from typing import IO


def run(devinfo: DeviceInfo, outfile: IO[str], periph_prefix: str, fuse_prefix: str) -> None:
    '''Make a C header file for the given device assuming is a a PIC or SAM Cortex-M device.
    '''
    outfile.write(_get_file_prologue(devinfo.name))
    outfile.write('\n')

    outfile.write('/* ----- Interrupt Vector Enumeration ----- */\n')
    outfile.write(_get_interrupt_enum(devinfo.interrupts))
    outfile.write('\n\n')

    outfile.write('/* ----- Core Configuration Macros ----- */\n')
    outfile.write(_get_parameter_macros(devinfo.parameters))
    outfile.write('\n\n')

    if devinfo.property_groups:
        outfile.write('/* ----- Device Property Macros ----- */\n')
    
        for prop_group in devinfo.property_groups:
            outfile.write(_get_device_property_macros(prop_group.properties))

        outfile.write('\n\n')

    outfile.write('/* ----- Address Space Macros ----- */\n')
    outfile.write(_get_memory_region_macros(devinfo.address_spaces))
    outfile.write('\n\n')

    outfile.write('/* ----- CMSIS Core and Peripherals Header ----- */\n')
    if devinfo.cpu.startswith('cortex'):
        outfile.write('#include <core_c' + devinfo.cpu.split('-')[1].lower() + '.h>\n')
    elif devinfo.cpu.startswith('arm'):
        outfile.write('#include "../arm_legacy/core_arm_legacy.h"\n')
    else:
        raise ValueError(f'Unrecognized CPU name {devinfo.cpu}')
    outfile.write('\n\n')

    outfile.write('/* ----- Device Peripheral Headers ----- */\n')
    outfile.write(_get_peripheral_headers(devinfo.peripherals, periph_prefix))
    outfile.write('\n\n')

    outfile.write('/* ----- Device Peripheral Address Macros ----- */\n')
    outfile.write(_get_peripheral_address_macros(devinfo.peripherals, devinfo.address_spaces))
    outfile.write('\n\n')

    outfile.write('/* ----- Device Peripheral Instance Parameters ----- */\n')
    fuses_peripheral: PeripheralGroup | None = None
    for periph in devinfo.peripherals:
        if _peripheral_is_special(periph):
            # Fuses need special handling--done below--so track it here.
            if 'fuses' == periph.name.lower():
                fuses_peripheral = periph
            continue

        for instance in periph.instances:
            outfile.write('// ' + instance.name + '\n')
            outfile.write(_get_parameter_macros(instance.params, instance.name + '_'))
    outfile.write('\n\n')

    # Fuses need special handling from other peripherals. This assumes there is at most one fuse
    # peripheral called FUSES, though that peripheral can have multiple groups.
    if fuses_peripheral:
        outfile.write('/* ----- Device Configuration Fuses ----- */\n')
        outfile.write(f'#include "{fuse_prefix}/{devinfo.name.lower()}.h"\n\n')
        outfile.write(_get_device_fuse_declarations(fuses_peripheral, devinfo.address_spaces))
        outfile.write('\n\n')

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
    prologue += strings.get_cmsis_license(' * ', strings.COPYRIGHT_CMSIS)
    prologue += ' */\n\n'

    # Include guard
    prologue += f'#ifndef {devname.upper()}_H_\n'
    prologue += f'#define {devname.upper()}_H_\n\n'

    # File version
    # For now, make this the same as our version
    fm_version: list[str] = version.FILE_MAKER_VERSION.split('.')
    prologue += f'#define DEVICE_FILE_VERSION_STR   "{version.FILE_MAKER_VERSION}"\n'
    prologue += f'#define DEVICE_FILE_VERSION_MAJOR ({fm_version[0]})\n'
    prologue += f'#define DEVICE_FILE_VERSION_MINOR ({fm_version[1]})\n'
    prologue += f'#define DEVICE_FILE_VERSION_PATCH ({fm_version[2]})\n\n'

    # extern "C"
    prologue += '#ifdef __cplusplus\n'
    prologue += 'extern "C" {\n'
    prologue += '#endif\n'

    return prologue


def _get_interrupt_enum(interrupts: list[DeviceInterrupt]) -> str:
    '''Return a string containing a C enumerations for the device interrupts.
    '''
    enum_str: str = 'typedef enum IRQn\n{\n'

    for interrupt in interrupts:
        name = interrupt.name + '_IRQn'
        index = interrupt.index
        caption = interrupt.caption
        enum_str += f'    {name:<24} = {index :>3}, /* {caption} */\n'

    enum_str += '} IRQn_Type;\n'

    return ('#ifndef __ASSEMBLER__\n' +
            enum_str +
            '#endif /* ifndef __ASSEMBLER__ */\n')


def _get_parameter_macros(parameters: list[ParameterValue], prefix: str = '') -> str:
    '''Return a string containing C macros defining the given parameters and their values.
    '''
    macros: str = ''

    for param in parameters:
        macro_name = prefix + param.name
        macro_value = '(' + param.value + ')'

        if param.caption:
            macros += f'#define {macro_name:<32} {macro_value:<16} /* {param.caption} */\n'
        else:
            macros += f'#define {macro_name:<32} {macro_value}\n'

    return macros


def _get_device_property_macros(parameters: list[ParameterValue]) -> str:
    '''Return a string containing C macros defining special properties about a device, such as its
    JTAG ID value.

    Device proprties need to be appending with something to avoid conflicting with other macros.
    XC32 uses "CHIP_", so we will use that for compatibility.
    '''
    macros: str = ''

    for param in parameters:
        if param.name.startswith('CHIPID_'):
            macro_name = 'CHIP_' + param.name[7:]
        elif not param.name.startswith('CHIP_'):
            macro_name = 'CHIP_' + param.name
        else:
            macro_name = param.name

        macro_value = '(' + param.value + ')'

        if param.caption:
            macros += f'#define {macro_name:<32} {macro_value:<16} /* {param.caption} */\n'
        else:
            macros += f'#define {macro_name:<32} {macro_value}\n'

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
            region_str += f'#define {base_macro_name:<32} (0x{base:08X}ul)\n'
            addr_macro_name = mem_region.name.upper() + '_ADDR'
            region_str += f'#define {addr_macro_name:<32} (0x{base:08X}ul)\n'

            size = mem_region.size
            size_macro_name = mem_region.name.upper() + '_SIZE'
            region_str += f'#define {size_macro_name:<32} (0x{size:08X}ul)\n'

            page_size = mem_region.page_size
            pagesize_macro_name = mem_region.name.upper() + '_PAGESIZE'
            region_str += f'#define {pagesize_macro_name:<32} ({page_size}ul)\n\n'

    return region_str


def _get_peripheral_headers(peripherals: list[PeripheralGroup], prefix: str) -> str:
    '''Return a string containing include declarations for this devices' peripherals, not including
    device fuses or core peripherals.

    The prefix is prepended to every include declaration to form a relative path to the peripheral
    headers from this device file. This creates "" includes, not <> includes.
    '''
    periph_str: str = ''

    for periph in peripherals:
        if not _peripheral_is_special(periph):
            name = periph.name.lower()
            id = periph.id.lower()
            version = periph.version.lower().replace(' ', '_')
            if version:
                periph_str += f'#include "{prefix}/{name}_{id}_{version}.h"\n'
            else:
                periph_str += f'#include "{prefix}/{name}_{id}.h"\n'

    return periph_str


def _get_peripheral_address_macros(peripherals: list[PeripheralGroup], 
                                   address_spaces: list[DeviceAddressSpace]) -> str:
    '''Return a string containing macros that define the location of peripheral instances on the
    device.

    The macros also cast the address to a pointer to a device-specific structure. These do not
    include device fuses or core peripherals. 
    '''
    base_macros: str = ''
    decl_macros: str = ''
    array_defs: str = ''

    for periph in peripherals:
        if _peripheral_is_special(periph):
            continue

        decl_macros_list: list[str] = []

        for instance in periph.instances:
            for group_ref in instance.reg_group_refs:
                base_macro_name = group_ref.instance_name.upper() + '_REGS_BASE'
                decl_macro_name = group_ref.instance_name.upper() + '_REGS'
                macro_type = group_ref.module_name.lower() + '_registers_t'
                macro_addr = (group_ref.offset + 
                              _find_start_of_address_space(address_spaces, group_ref.addr_space))

                base_macros += f'#define {base_macro_name:<32} (0x{macro_addr:08X}ul)\n'
                decl_macros += f'#define {decl_macro_name:<32} ((volatile {macro_type}*){base_macro_name})\n'
                decl_macros_list.append(decl_macro_name)

        if decl_macros_list:
            array_type = periph.name.lower() + '_registers_t*'
            array_name = periph.name.upper() + 'n_REGS[]'
            array_decl = f'static volatile __attribute__((unused)) {array_type} {array_name}'
            array_defs += f'{array_decl:<72} = {{{', '.join(decl_macros_list)}}};\n'

    return (base_macros + 
            '\n#ifndef __ASSEMBLER__\n' +
            decl_macros +
            '\n' +
            array_defs +
            '#endif /* ifndef __ASSEMBLER__ */\n')


def _get_device_fuse_declarations(fuse_periph: PeripheralGroup, 
                                  addr_spaces: list[DeviceAddressSpace]
                                 ) -> str:
    '''Return a string of declarations for the given periepheral group assuming the group represents
    a set of device fuses.

    Fuses need special handling because their definitions need to be present in the firmware image
    so they can be programmed onto the device. The linker script for this device will need to have
    output sections for these.
    '''
    decl_str: str = ''
    addr_macro_str: str = ''

    for instance in fuse_periph.instances:
        for group_ref in instance.reg_group_refs:
            # Find the matching register group for this reference.
            reg_group: RegisterGroup | None = None
            for group in fuse_periph.reg_groups:
                if group.name == group_ref.module_name:
                    reg_group = group
                    break

            if not reg_group:
                continue

            base_addr = (_find_start_of_address_space(addr_spaces, group_ref.addr_space)
                         + group_ref.offset)

            for member in reg_group.members:
                regtype: str = _get_reg_type_from_size(member.size)

                # There are multiple of some registers, so make declarations for each one.
                if member.count > 0:
                    for i in range(member.count):
                        reg_addr = base_addr + member.offset + (member.size*i)
                        base_name = group_ref.instance_name + '_' + member.name
                        section_name = '.' + base_name.lower() + str(i)
                        variable_name = base_name.upper() + str(i)

                        if not variable_name.startswith('FUSES_'):
                            variable_name = 'FUSES_' + variable_name

                        addr_macro_str += f'#define {variable_name + '_BASE':<32} (0x{reg_addr:08X}ul)\n'

                        decl_str += f'extern const {regtype} __attribute__((used, retain, section("{section_name}"))) '
                        decl_str += variable_name + ';\n'
                else:
                    reg_addr = base_addr + member.offset
                    base_name = group_ref.instance_name + '_' + member.name
                    section_name = '.' + base_name.lower()
                    variable_name = base_name.upper()

                    if not variable_name.startswith('FUSES_'):
                        variable_name = 'FUSES_' + variable_name

                    addr_macro_str += f'#define {variable_name + '_BASE':<32} (0x{reg_addr:08X}ul)\n'

                    decl_str += f'extern const {regtype} __attribute__((used, retain, section("{section_name}"))) '
                    decl_str += variable_name + ';\n'

    return (addr_macro_str +
            '\n#ifndef __ASSEMBLER__\n' +
            decl_str +
            '\n#endif /* ifndef __ASSEMBLER__ */\n')


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

    # Core peripherals appear to either not have an ID or have SYSTEM_IP as their ID.
    if not periph.id  or 'system_ip' in periph.id.lower():
        return True
    
    return False


def _find_start_of_address_space(addr_spaces: list[DeviceAddressSpace], name: str) -> int:
    '''Search the list of address spaces for the one with the given name and return its start
    address.
    '''
    for space in addr_spaces:
        if name == space.id:
            return space.start_addr

    raise ValueError(f'Address space {name} could not be found!')


def _get_reg_type_from_size(size: int) -> str:
    '''Return a C99 type to be used with the given size, such as uint32_t for something that is
    four bytes.
    '''
    if size > 8:
        raise ValueError(f'Invalid size {size} for register type!')
    if size > 4:
        return 'uint64_t'
    elif size > 2:
        return 'uint32_t'
    elif size > 1:
        return 'uint16_t'
    else:
        return 'uint8_t'

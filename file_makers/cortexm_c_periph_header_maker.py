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

'''cortexm_c_periph_header_maker.py

Contains a single public function to make a C peripheral header file for a single Arm Cortex-M
device. These are included by the device-specific header files and contain the definitions for the
peripherals on the device.
This is based on the sample headers found in Arm CMSIS 6 at
https://github.com/ARM-software/CMSIS_6/blob/main/CMSIS/Core/Template/Device_M/Include/.
'''

from device_info import *
import operator
from . import strings
from typing import IO


def run(basename: str, peripheral: PeripheralGroup, outfile: IO[str]) -> None:
    '''Make a C header file for the given device assuming is a a PIC or SAM Cortex-M device.

    The basename is the file name without the extension and without any paths.
    '''
    outfile.write(_get_file_prologue(basename))
    outfile.write('\n')

    outfile.write('/* ----- Register Bitfield Macros ----- */\n')
    for reg_group in peripheral.reg_groups:
        for member in reg_group.members:
            if not member.is_subgroup:
                outfile.write(_get_register_macros(peripheral.name, member))
                outfile.write('\n')

    outfile.write('\n\n#ifndef __ASSEMBLER__\n\n')

    outfile.write('/* ----- Register Group Definitions ----- */\n')
    for reg_group in peripheral.reg_groups:
        outfile.write(_get_register_group_definition(peripheral.name, reg_group))
        outfile.write('\n')

    outfile.write('#endif /* ifndef __ASSEMBLER__ */\n\n')

    outfile.write(_get_file_epilogue(basename))


def _get_file_prologue(filename: str) -> str:
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
    prologue += f'#ifndef {filename.upper()}_H_\n'
    prologue += f'#define {filename.upper()}_H_\n\n'

    # extern "C"
    prologue += '#ifdef __cplusplus\n'
    prologue += 'extern "c" {\n'
    prologue += '#endif\n'

    return prologue

def _get_register_macros(periph_name: str, reg: RegisterGroupMember) -> str:
    '''Return a string containing macros defining the given register and its bitfields assuming it
    is a register and not a reference to another register group.
    '''
    macros: str = ''

    # Some registers on some devices (SAME70) repeat the peripheral name in them. Strip it off so
    # we don't duplicate it later.
    if reg.name.startswith(periph_name + '_'):
        reg_name = reg.name.split('_', 1)[1]
    else:
        reg_name = reg.name

    if reg.mode:
        macro_base_name = f'{periph_name}_{reg.mode}_{reg_name}'
    else:
        macro_base_name = f'{periph_name}_{reg_name}'

    # If a peripheral has modes, then register definitions will contain the mode to which they apply.
    # An example of this is the SERCOM peripheral, which can be in SPI, UART, or I2C mode.
    # Some bitfields also have register modes to which they apply. An example of this is the TCC
    # peripheral, which allows for the period and counter registers to have different resolutions to
    # support dithering.
    # The PeriphMode and RegMode bits and an adjacent underscore are omitted if a mode isn't used.
    #
    # Macro base name: PeriphName_PeriphMode_RegName
    # Offset macro name format: BaseName_OFFSET
    # Field macro name format:  BaseName_RegMode_FieldName_foo
    # Value macro name format:  BaseName_FieldName_ValueName_foo

    # A comment with the register name and an optional caption.
    macros += f'// {macro_base_name}'
    if reg.caption:
        macros += ': ' + reg.caption
    macros += '\n'

    # A macro with the initial value upon reset.
    macros += _get_basic_macro(f'{macro_base_name}_RESETVAL' , f'0x{reg.init_val :08X}ul')

    # A macro giving the offset. If this is an array of registers, create another macro to let you
    # get the offset into the array.
    macros += _get_basic_macro(f'{macro_base_name}_OFFSET', f'0x{reg.offset :02X}ul')
    if reg.count:
        macros += _get_basic_macro(f'{macro_base_name}_OFFSETn(off)',
                                   f'{macro_base_name}_OFFSET + ({reg.size}ul * off)')
    macros += '\n'

    # Get the 'Field_Msk', 'Field_Pos', and 'Field(v)' macros that every field has. Fields that
    # apply only in certain register modes will need a set for each mode.
    # If a field also has specific values associated with it, then get those too.
    for field in reg.fields:
        if field.modes:
            for fmode in field.modes:
                field_macro_name = f'{macro_base_name}_{fmode}_{field.name}'
                macros += _get_bitfield_macros(field_macro_name, field.mask, field.caption)
        else:
            field_macro_name = f'{macro_base_name}_{field.name}'
            macros += _get_bitfield_macros(field_macro_name, field.mask, field.caption)

        if field.values:
            value_macro_base = f'{macro_base_name}_{field.name}'
            macros += _get_bitfield_value_macros(value_macro_base, field.values)


    return macros

def _get_register_group_definition(periph_name: str, group: RegisterGroup) -> str:
    '''Return a string containing a C struct or union that defines a single register group.
    '''
    group_def: str = ''

    if group.modes:
        # We have modes, so we need to output a structure for each mode.
        for mode in group.modes:
            group_def += _get_register_struct(periph_name, group, mode)
            group_def += '\n'
        
        # Now the "main" structure is a union containing the different modes.
        union_name = _get_base_groupdef_name(periph_name, group.name)
        group_def += f'typedef union _{union_name}\n{{\n'

        for mode in group.modes:
            mode_type_name = _get_base_groupdef_name(periph_name, group.name, mode) + '_t'
            group_def += f'    {mode_type_name :<24} {mode};\n'
        
        group_def += f'}} {union_name}_t;\n'
    else:
        group_def += _get_register_struct(periph_name, group)

    return group_def

def _get_file_epilogue(filename: str) -> str:
    '''Return a string with the file epilogue, which is the stuff at the end of the file like
    the end of the include guard and extern "C" statements that were at the top.
    '''
    epilogue: str = ''

    # extern "C"
    epilogue += '#ifdef __cplusplus\n'
    epilogue += '}\n'
    epilogue += '#endif\n\n'

    # Include guard
    epilogue += f'#endif /* {filename.upper()}_H_ */\n'

    return epilogue


def _get_bitfield_macros(field_macro_name: str, mask: int, caption: str) -> str:
    '''Return a string containing set of macros based on the given base name that define a mask,
    position, and a way to set a value for this field.
    '''
    macros: str = ''

    msk_macro_name = f'{field_macro_name}_Msk'
    pos_macro_name = f'{field_macro_name}_Pos'

    # This returns -1 if the input is 0. This was found on Stack Overflow by searching online for
    # "python ctz": https://stackoverflow.com/a/63552117.
    pos = (mask & -mask).bit_length() - 1

    macros += _get_basic_macro(msk_macro_name, f'0x{mask :08X}ul', caption)
    macros += _get_basic_macro(pos_macro_name, f'{pos}ul')
    macros += _get_basic_macro(f'{field_macro_name}(v)',
                               f'{msk_macro_name} & ((uint32_t)(v) << {pos_macro_name})')

    return macros

def _get_bitfield_value_macros(macro_base_name: str, values: list[ParameterValue]) -> str:
    '''Return a string containing macros for each value in the given list: one macro defining the
    value and another convenience macro to assign this value to a register.
    '''
    macros: str = ''

    for val in values:
        macros += _get_basic_macro(f'    {macro_base_name}_{val.name}_Val',
                                   val.value + 'ul',
                                   val.caption)

    for val in values:
        macros += _get_basic_macro(f'{macro_base_name}_{val.name}',
                                   f'{macro_base_name}_{val.name}_Val << {macro_base_name}_Pos')

    return macros

def _get_basic_macro(macro_name: str, macro_value: str, macro_caption: str = '') -> str:
    '''Return a string containing a single macro definition with the given value and optional
    caption comment.
    '''
    macro: str = ''

    if macro_caption:
        val_str = f'({macro_value})'
        macro += f'#define {macro_name :<48} {val_str :<16} /* {macro_caption} */\n'
    else:
        macro += f'#define {macro_name :<48} ({macro_value})\n'

    return macro

def _get_register_struct(periph_name: str, group: RegisterGroup, mode: str = '') -> str:
    '''Return a string containing a C struct that defines a single register group.

    If a mode is provided, the resulting structure will include only registers from that mode or
    ones that do not have a mode. Otherwise, all registers in the group are included.
    '''
    reg_struct: str = ''

    # A comment with the group name and optional caption.
    reg_struct += f'// {group.name}'
    if group.caption:
        reg_struct += f': {group.caption}'
    reg_struct += '\n'

    struct_name = _get_base_groupdef_name(periph_name, group.name, mode)

    reg_struct += f'typedef struct _{struct_name}\n{{\n'
    current_offset: int = 0

    for member in group.members:
        # If we were given a mode, then ouptut only registers that have the same mode or no mode. 
        if mode  and  member.mode  and  mode != member.mode:
            continue

        # Do we need to add some padding for unused space?
        if current_offset != member.offset:
            pad = member.offset - current_offset
            reg_struct += f'    uint8_t                  unused_0x{current_offset :<02X}[{pad}];\n'
            current_offset = member.offset

        # Get the type name.
        if member.is_subgroup:
            subgroup_type = _get_base_groupdef_name(periph_name, member.name) + '_t'
        else:
            subgroup_type = _get_reg_type_from_size(member.size)

        # Some registers on some devices repeat the peripheral name in them. Strip that off.
        if member.name.startswith(periph_name + '_'):
            mem_name = member.name.split('_', 1)[1]
        else:
            mem_name = member.name

        reg_struct += f'    {subgroup_type :<24} {mem_name}'

        # Is this an array?
        if member.count:
            reg_struct += f'[{member.count}]'
            current_offset += (member.size * member.count)
        else:
            current_offset += member.size

        reg_struct += ';\n'

    # Do we need to add padding to the end of the struct/union?
    if current_offset < group.size:
        pad = group.size - current_offset
        reg_struct += f'    uint8_t                  unused_0x{current_offset :<02X}[{pad}];\n'

    reg_struct += f'}} {struct_name}_t;\n'

    return reg_struct

def _get_base_groupdef_name(periph_name: str, group_name: str, mode_name: str = '') -> str:
    '''Return a base name to used used for the type name of the given group.

    The resulting name will be "periph_mode_group_regs". If a mode is not provided (the default),
    then the resulting name will be "periph_group_regs". The peripheral name is stripped from the
    start of the group name if needed. If the group name is then empty, the resulting name will be
    "periph_mode_regs" or "periph_regs" if a mode is not provided. The name is all lower-case.
    '''
    if group_name.startswith(periph_name):
        group_name = group_name[len(periph_name):]

    if group_name:
        group_name = '_' + group_name.lower()

    if mode_name:
        mode_name = '_' + mode_name.lower()

    return f'{periph_name.lower()}{mode_name}{group_name}_regs'

def _get_reg_type_from_size(size: int) -> str:
    '''Return a C99 type to be used with the given size, such as uint32_t for something that is
    four bytes.
    '''
    if size > 4:
        return 'uint64_t'
    elif size > 2:
        return 'uint32_t'
    elif size > 1:
        return 'uint16_t'
    else:
        return 'uint8_t'
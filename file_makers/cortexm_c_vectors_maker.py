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

'''cortexm_c_vectors_maker.py

Contains a single public function to make a C file containing vector table declarations for a single
Arm Cortex-M device. These would be built with the project along with the Cortex-M startup code.
This is based on the sample startup code found in Arm CMSIS 6 at
https://github.com/ARM-software/CMSIS_6/blob/main/CMSIS/Core/Template/Device_M/Source/startup_Device.c.
'''

from device_info import *
from . import strings
import textwrap
from typing import IO


def run(proc_header_name: str, interrupts: list[DeviceInterrupt], outfile: IO[str]) -> None:
    '''Make a C vector definition file for the given device assuming it is a PIC or SAM Cortex-M
    device.

    The proc_header_name is the name of a header file this can include to get processor-specific
    info. This can be the processor-specifc header file or an all-encompassing header that will
    figure out which processor-specific header to use based on macros. This should include the
    extension but not the full path.
    '''
    outfile.write(_get_file_prologue(proc_header_name))
    outfile.write('\n')
    outfile.write(_get_default_handlers())
    outfile.write('\n\n')
    outfile.write(_get_handler_declarations(interrupts))
    outfile.write('\n\n')
    outfile.write(_get_vector_table(interrupts))
    outfile.write('\n')

    # This file does not have an epilogue.


def _get_file_prologue(proc_header_name: str) -> str:
    '''Return a string with the file prologue, which contains the license info, a reference to
    this project, and some other declarations.
    '''
    prologue: str = ''

    # Write the header block with copyright info.
    prologue += '/*\n'
    prologue += strings.get_generated_by_string(' * ')
    prologue += ' * \n'
    prologue += strings.get_cmsis_apache_license(' * ')
    prologue += ' */\n\n'
    prologue += f'#include <{proc_header_name}>\n'
    prologue += '#include <stdint.h>\n\n'
    prologue += '/* Stack top provided by device linker script. */\n'
    prologue += '/* This is an alias defined by CMSIS. */\n'
    prologue += 'extern uint32_t __INITIAL_SP;\n'

    return prologue


def _get_default_handlers() -> str:
    '''Return a string containing definitions for the default interrupt handler and the Hard Fault
    interrupt handler.
    '''
    return textwrap.dedent(
        '''
        /* ----- Default Handlers: Provide your own definitions to override these. ----- */
        // Default Hard Fault Handler
        void __attribute__((noreturn, weak)) HardFault_Handler(void)
        {
        #ifdef __DEBUG
            __BKPT(0);
        #endif
            while(1)
            {}
        }

        // Default Handler For Other Exceptions and Interrupts
        void __attribute__((noreturn, weak)) Default_Handler(void)
        {
        #ifdef __DEBUG
            __BKPT(0);
        #endif
            while(1)
            {}
        }

        // Default Handler For Reserved Interrupt Vectors
        void __attribute__((noreturn, weak)) Reserved_Handler(void)
        {
        #ifdef __DEBUG
            __BKPT(0);
        #endif
            while(1)
            {}
        }

        /* ----- Reset Handler Declaration: Provided by the startup code ----- */
        void __attribute__((noreturn, section(".reset"))) Reset_Handler(void);
        ''')


def _get_handler_declarations(interrupts: list[DeviceInterrupt]) -> str:
    '''Return a string containing weak declarations for the interrupt and exception handlers not
    already covered by _get_default_handlers().

    Most of these will be weak aliases of the Default_Handler(). The idea is that users will create
    their own definitions in their code, which will override these weak versions.
    '''
    decl_str: str = '/* ----- Exception and Interrupt Handlers ----- */\n'
    decl_str += '/* Provide your own definitions to override these. */\n'

    for intr in interrupts:
        # Skip these because we already declared them in _get_default_handlers().
        if 'HardFault' == intr.name  or  'Reset' == intr.name:
            continue

        func_str = f'{intr.name}_Handler'
        decl_str += f'void {func_str :<32}(void) __attribute__((weak, alias("Default_Handler")));\n'

    return decl_str


def _get_vector_table(interrupts: list[DeviceInterrupt]) -> str:
    '''Return a string containing the definition of the vector table for this device.

    The vector table is an array of function pointers, but the very first entry is the initial top
    of the stack to be loaded into the stack pointer register.
    '''
    intr_decls: list[str] = []
    intr_decls.append('    (void (*)(void))&__INITIAL_SP,   /*     Initial Stack Pointer */')

    current_index = interrupts[0].index

    for intr in interrupts:
        # Fill in gaps with the reserved handler.
        while current_index < intr.index:
            intr_decls.append('    Reserved_Handler,                /*     Reserved */')
            current_index += 1
        
        entry = f'{intr.name}_Handler,'
        intr_decls.append(f'    {entry :<32} /* {intr.index :3} {intr.caption} */')

        current_index += 1

    # +1 for initial stack value.
    num_entries = current_index - interrupts[0].index + 1

    vec_table_decl =  f'extern const void(*__VECTOR_TABLE[{num_entries}])(void);\n'
    vec_table_decl += f'       const void(*__VECTOR_TABLE[{num_entries}])(void) '
    vec_table_decl +=  '__attribute__((used, retain, section(".vectors"))) = {\n'
    vec_table_decl += '\n'.join(intr_decls)
    vec_table_decl += '\n};'

    return vec_table_decl

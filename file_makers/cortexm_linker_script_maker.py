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

'''cortexm_linker_script_maker.py

Contains a single public function to make a GNU linker script file for a single Arm Cortex-M device.
This is based on the sample linker script found in Arm CMSIS 6 at
https://github.com/ARM-software/CMSIS_6/blob/main/CMSIS/Core/Template/Device_M/Config/Device_gcc.ld.
'''

from device_info import *
import operator
from . import strings
import textwrap
from typing import IO


def run(devinfo: DeviceInfo, outfile: IO[str]) -> None:
    '''Make a linker script for the given device assuming is a a PIC or SAM Cortex-M device.
    '''

    # Write the header block with copyright info.
    outfile.write('/*\n')
    outfile.write(strings.get_generated_by_string(' * '))
    outfile.write(' * \n')
    outfile.write(strings.get_cmsis_apache_license(' * '))
    outfile.write(' */\n\n')
    
    unique_addr_spaces: list[DeviceAddressSpace] = _remove_overlapping_memory(devinfo.address_spaces)

    # Sort the now-not-overlapping memory regions by starting address.
    # See https://docs.python.org/3/howto/sorting.html
    for addr_space in unique_addr_spaces:
        addr_space.mem_regions.sort(key=operator.attrgetter('start_addr'))

    # Now we can output the actual linker script bits.
    outfile.write(_get_memory_symbols(unique_addr_spaces))
    outfile.write('\n\n')
    outfile.write(_get_MEMORY_command(unique_addr_spaces))
    outfile.write('\n\n')
    outfile.write('ENTRY(Reset_Handler)')
    outfile.write('\n\n')

    outfile.write('SECTIONS\n{\n')
    outfile.write(_get_standard_SECTIONS())

    # Fuses are special because unlike other peripherals with their fixed locations, fuses
    # need to be programmed into the flash at the correct spot. We need to create linker sections
    # for them to go. This assumes a device has at most one fuses peripheral called FUSES.
    for periph in devinfo.peripherals:
        if 'fuses' == periph.name.lower():
            outfile.write(_get_fuse_SECTIONS(unique_addr_spaces, periph))
            break

    outfile.write('}\n')


def _remove_overlapping_memory(address_spaces: list[DeviceAddressSpace]) -> list[DeviceAddressSpace]:
    '''Return a list of address spaces with overlapping regions removed.

    Some devices, like the SAME54 series, have multiple regions with the same starting address. We
    don't want those in our linker script because they will produce linker errors, so we need to 
    remove them. Do this by finding and keeping only the biggest region of the overlapping spaces.
    To keep us sane, this assumes that any overlapping regions are contained wholly within another
    region. Otherwise, we probably have bigger problems and a really weird memory layout.
    '''
    new_spaces: list[DeviceAddressSpace] = []

    for addr_space in address_spaces:
        # In Python, both sets and dicts (maps) use curly braces. Any empty pair of braces "{}"
        # creates an empty dict by default, so use 'set()' to create an empty set.
        regions_to_remove: set[str] = set()

        for i in range(0, len(addr_space.mem_regions)):
            name_i = addr_space.mem_regions[i].name
            start_i = addr_space.mem_regions[i].start_addr
            end_i = start_i + addr_space.mem_regions[i].size

            for j in range(i+1, len(addr_space.mem_regions)):
                name_j = addr_space.mem_regions[j].name
                start_j = addr_space.mem_regions[j].start_addr
                end_j = start_j + addr_space.mem_regions[j].size

                if start_i >= start_j  and  end_i <= end_j:
                    # Region i is contained in region j, so remove region i.
                    regions_to_remove.add(name_i)
                elif start_j >= start_i  and  end_j <= end_i:
                    # Region j is contained in region i, so remove region j.
                    regions_to_remove.add(name_j)

        new_regions: list[DeviceMemoryRegion] = []

        for region in addr_space.mem_regions:
            if region.name not in regions_to_remove:
                new_regions.append(region)

        new_spaces.append(DeviceAddressSpace(id = addr_space.id,
                                             start_addr = addr_space.start_addr,
                                             size = addr_space.size,
                                             mem_regions = new_regions))
        
    return new_spaces

def _find_biggest_internal_region(address_spaces: list[DeviceAddressSpace],
                                  type: str) -> DeviceMemoryRegion | None:
    '''Find and return the largest internal memory region of the given type (flash, ram, io, etc.).

    This will return a copy of the region with the starting address of the containing address space
    added to the found region. This will return None if a region of the given type cannot be found.
    '''
    biggest: DeviceMemoryRegion | None = None

    for addr_space in address_spaces:
        for region in addr_space.mem_regions:
            if region.external  or  type != region.type.lower():
                continue

            if not biggest or region.size > biggest.size:
                start = addr_space.start_addr + region.start_addr
                biggest = DeviceMemoryRegion(name = region.name,
                                                start_addr = start,
                                                size = region.size,
                                                type = region.type,
                                                page_size = region.page_size,
                                                external = region.external)

    return biggest

def _get_memory_symbols(address_spaces: list[DeviceAddressSpace]) -> str:
    '''Return a set of linker symbols giving the start and size of ROM, RAM, and any other useful
    tidbits.
    '''
    biggest_flash_region = _find_biggest_internal_region(address_spaces, 'flash')
    biggest_ram_region = _find_biggest_internal_region(address_spaces, 'ram')

    if biggest_flash_region is None  or  biggest_ram_region is None:
        return ''

    symbol_str: str = f'''
        /* Internal flash base address and size in bytes. */
        __ROM_BASE = 0x{biggest_flash_region.start_addr :08X}
        __ROM_SIZE = 0x{biggest_flash_region.size :08X}

        /* Internal RAM base address and size in bytes. */
        __RAM_BASE = 0x{biggest_ram_region.start_addr :08X}
        __RAM_SIZE = 0x{biggest_ram_region.size :08X}

        /* Stack and heap configuration. 
           Modify these using the --defsym option to the linker. */
        PROVIDE(__STACK_SIZE = 0x00000400);
        PROVIDE(__HEAP_SIZE  = 0x00000C00);

        /* ARMv8-M stack sealing:
           To use ARMv8-M stack sealing set __STACKSEAL_SIZE to 8 otherwise keep 0. */
        __STACKSEAL_SIZE = 0;
        '''

    return textwrap.dedent(symbol_str)

def _get_MEMORY_command(address_spaces: list[DeviceAddressSpace]) -> str:
    '''Return the MEMORY command for GNU linker scripts that lists the memory regions in the device.
    '''
    biggest_flash_region = _find_biggest_internal_region(address_spaces, 'flash')
    biggest_ram_region = _find_biggest_internal_region(address_spaces, 'ram')

    if biggest_flash_region is None  or  biggest_ram_region is None:
        return ''

    memory_cmd: str = 'MEMORY\n{\n'

    for addr_space in address_spaces:
        for region in addr_space.mem_regions:
            name: str = region.name.lower()
            start: int = addr_space.start_addr + region.start_addr
            size: int = region.size

            # We need to add some region attributes to the main flash and RAM sections. Unfortunately,
            # the device info we can get from the ATDF files is not totally helpful here.
            if name == biggest_flash_region.name.lower():
                memory_cmd += f'  {name :<17} (rx)  : ORIGIN = 0x{start :08X}, LENGTH = 0x{size :08X}\n'
            elif name == biggest_ram_region.name.lower():
                memory_cmd += f'  {name :<17} (rwx) : ORIGIN = 0x{start :08X}, LENGTH = 0x{size :08X}\n'
            else:
                memory_cmd += f'  {name :<23} : ORIGIN = 0x{start :08X}, LENGTH = 0x{size :08X}\n'

    memory_cmd += '}\n\n'

    # The ATDF files are not consistent with the names of the main flash and RAM regions, so add
    # these aliases if needed to make dealing with the output sections a little easier.
    if 'flash' != biggest_flash_region.name.lower():
        memory_cmd += f'REGION_ALIAS("flash", {biggest_flash_region.name.lower()});\n'
    if 'ram' != biggest_flash_region.name.lower():
        memory_cmd += f'REGION_ALIAS("ram", {biggest_ram_region.name.lower()});\n'

    return memory_cmd

def _get_standard_SECTIONS() -> str:
    '''Return the standard sections that would be in a SECTIONS command for Arm linker scripts.
     
    The SECTIONS command indicates how object file sections will map into the memory regions from
    the MEMORY command.
    '''
    sections_cmd: str = textwrap.dedent('''
          .text :
          {
            KEEP(*(.vectors))
            *(.text*)

            KEEP(*(.init))
            KEEP(*(.fini))

            /* .ctors */
            *crtbegin.o(.ctors)
            *crtbegin?.o(.ctors)
            *(EXCLUDE_FILE(*crtend?.o *crtend.o) .ctors)
            *(SORT(.ctors.*))
            *(.ctors)

            /* .dtors */
            *crtbegin.o(.dtors)
            *crtbegin?.o(.dtors)
            *(EXCLUDE_FILE(*crtend?.o *crtend.o) .dtors)
            *(SORT(.dtors.*))
            *(.dtors)

            *(.rodata*)

            KEEP(*(.eh_frame*))
          } > flash

          /*
           * SG veneers:
           * All SG veneers are placed in the special output section .gnu.sgstubs. Its start address
           * must be set, either with the command line option '--section-start' or in a linker script,
           * to indicate where to place these veneers in memory.
           */
          /*
          .gnu.sgstubs :
          {
            . = ALIGN(32);
          } > flash
          */
          .ARM.extab :
          {
            *(.ARM.extab* .gnu.linkonce.armextab.*)
          } > flash

          __exidx_start = .;
          .ARM.exidx :
          {
            *(.ARM.exidx* .gnu.linkonce.armexidx.*)
          } > flash
          __exidx_end = .;

          .copy.table :
          {
            . = ALIGN(4);
            __copy_table_start__ = .;

            LONG (LOADADDR(.data))
            LONG (ADDR(.data))
            LONG (SIZEOF(.data) / 4)

            /* Add each additional data section here */

            __copy_table_end__ = .;
          } > flash

          .zero.table :
          {
            . = ALIGN(4);
            __zero_table_start__ = .;

            LONG (ADDR(.bss))
            LONG (SIZEOF(.bss) / 4)

            /* Add each additional bss section here */

            __zero_table_end__ = .;
          } > flash

          /*
           * This __etext variable is kept for backward compatibility with older,
           * ASM based startup files.
           */
          PROVIDE(__etext = LOADADDR(.data));

          .data : ALIGN(4)
          {
            __data_start__ = .;
            *(vtable)
            *(.data)
            *(.data.*)

            . = ALIGN(4);
            /* preinit data */
            PROVIDE_HIDDEN (__preinit_array_start = .);
            KEEP(*(.preinit_array))
            PROVIDE_HIDDEN (__preinit_array_end = .);

            . = ALIGN(4);
            /* init data */
            PROVIDE_HIDDEN (__init_array_start = .);
            KEEP(*(SORT(.init_array.*)))
            KEEP(*(.init_array))
            PROVIDE_HIDDEN (__init_array_end = .);

            . = ALIGN(4);
            /* finit data */
            PROVIDE_HIDDEN (__fini_array_start = .);
            KEEP(*(SORT(.fini_array.*)))
            KEEP(*(.fini_array))
            PROVIDE_HIDDEN (__fini_array_end = .);

            KEEP(*(.jcr*))
            . = ALIGN(4);
            /* All data end */
            __data_end__ = .;

          } > ram AT > flash

          /*
           * Secondary data section, optional
           *
           * Remember to add each additional data section
           * to the .copy.table above to assure proper
           * initialization during startup.
           */
          /*
          .data2 : ALIGN(4)
          {
            . = ALIGN(4);
            __data2_start__ = .;
            *(.data2)
            *(.data2.*)
            . = ALIGN(4);
            __data2_end__ = .;

          } > ram2 AT > flash
          */

          .bss :
          {
            . = ALIGN(4);
            __bss_start__ = .;
            *(.bss)
            *(.bss.*)
            *(COMMON)
            . = ALIGN(4);
            __bss_end__ = .;
          } > ram AT > ram

          /*
           * Secondary bss section, optional
           *
           * Remember to add each additional bss section
           * to the .zero.table above to assure proper
           * initialization during startup.
           */
          /*
          .bss2 :
          {
            . = ALIGN(4);
            __bss2_start__ = .;
            *(.bss2)
            *(.bss2.*)
            . = ALIGN(4);
            __bss2_end__ = .;
          } > ram2 AT > ram2
          */

          .heap (NOLOAD) :
          {
            . = ALIGN(8);
            __end__ = .;
            PROVIDE(end = .);
            . = . + __HEAP_SIZE;
            . = ALIGN(8);
            __HeapLimit = .;
          } > ram

          .stack (ORIGIN(RAM) + LENGTH(RAM) - __STACK_SIZE - __STACKSEAL_SIZE) (NOLOAD) :
          {
            . = ALIGN(8);
            __StackLimit = .;
            . = . + __STACK_SIZE;
            . = ALIGN(8);
            __StackTop = .;
          } > ram
          PROVIDE(__stack = __StackTop);

          /* ARMv8-M stack sealing:
             to use ARMv8-M stack sealing uncomment '.stackseal' section
           */
          /*
          .stackseal (ORIGIN(RAM) + LENGTH(RAM) - __STACKSEAL_SIZE) (NOLOAD) :
          {
            . = ALIGN(8);
            __StackSeal = .;
            . = . + 8;
            . = ALIGN(8);
          } > ram
          */

          /* Check if data + heap + stack exceeds RAM limit */
          ASSERT(__StackLimit >= __HeapLimit, "region RAM overflowed with stack")
        ''')

    return textwrap.indent(sections_cmd, '  ')

def _get_fuse_SECTIONS(addr_spaces: list[DeviceAddressSpace], fuses: PeripheralGroup) -> str:
    '''Create special output sections for the given peripherals assuming they are fuses. This will
    look through the address spaces to find one to which they belong.
    '''
    fuse_str: str = ''

    for inst in fuses.instances:
        for ref in inst.reg_group_refs:
            section_addr = ref.offset + _find_start_of_address_space(addr_spaces, ref.addr_space)
            section_name = '.' + ref.instance_name.lower()

            fuse_str += f'\n{section_name} 0x{section_addr :08X} READONLY :\n'
            fuse_str += '{\n'
            fuse_str += f'  KEEP(*({section_name}))\n'
            fuse_str += '}\n'

    return textwrap.indent(fuse_str, '  ')

def _find_start_of_address_space(addr_spaces: list[DeviceAddressSpace], name: str) -> int:
    '''Search the list of address spaces for the one with the given name and return its start
    address.
    '''
    for space in addr_spaces:
        if name == space.id:
            return space.start_addr

    raise RuntimeError(f'Address space {name} could not be found!')
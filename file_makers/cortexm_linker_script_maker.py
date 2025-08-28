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

    #
    # First gather info on our memory spaces.
    #

    unique_addr_spaces: list[DeviceAddressSpace] = _remove_overlapping_memory(devinfo.address_spaces)

    # Sort the now-not-overlapping memory regions by starting address.
    # See https://docs.python.org/3/howto/sorting.html
    for addr_space in unique_addr_spaces:
        addr_space.mem_regions.sort(key=operator.attrgetter('start_addr'))

    # Find our main memory regions for flash and RAM. For now, assume that boot flash regions
    # have "bfm" in the name.
    main_flash_region = _find_biggest_memory_region(unique_addr_spaces, 'flash', False)
    main_ram_region = _find_biggest_memory_region(unique_addr_spaces, 'ram', False)
    main_bootflash_region = _find_biggest_memory_region(unique_addr_spaces, 'flash', False, 'bfm')
    itcm_region = _find_biggest_memory_region(unique_addr_spaces, 'ram', False, 'itcm')
    dtcm_region = _find_biggest_memory_region(unique_addr_spaces, 'ram', False, 'dtcm')

    if not main_flash_region:
        # Some devices have only external flash, so check for that.
        main_flash_region = _find_biggest_memory_region(unique_addr_spaces, 'flash', True)
        if not main_flash_region:
            # Some devices have no flash, so use RAM.
            main_flash_region = _find_biggest_memory_region(unique_addr_spaces, 'ram', False)

    if not main_flash_region:
        raise RuntimeError(f'Failed to find a program flash region for {devinfo.name}')
    if not main_ram_region:
        raise RuntimeError(f'Failed to find a RAM region for {devinfo.name}')
    # Do not check for bootflash region because not all devices have boot flash.

    # Look for a fuses peripheral.
    # Fuses are special because unlike other peripherals with their fixed locations, fuses
    # need to be programmed into the flash at the correct spot. We need to create linker sections
    # for them to go. This assumes a device has at most one fuses peripheral called FUSES.
    fuses_periph: PeripheralGroup | None = None
    for periph in devinfo.peripherals:
        if 'fuses' == periph.name.lower():
            fuses_periph = periph
            break

    #
    # Now we can start writing the linker script
    #

    # Header block with copyright info.
    outfile.write('/*\n')
    outfile.write(strings.get_generated_by_string(' * '))
    outfile.write(' * \n')
    outfile.write(strings.get_cmsis_apache_license(' * '))
    outfile.write(' */\n\n')

    # MEMORY command
    outfile.write(_get_memory_symbols(main_flash_region, main_ram_region))
    outfile.write('\n\nMEMORY\n{\n')
    outfile.write(_get_MEMORY_regions(unique_addr_spaces, main_flash_region, main_ram_region,
                                      main_bootflash_region))
    if fuses_periph:
        outfile.write(_get_fuse_MEMORY(unique_addr_spaces, fuses_periph))
    outfile.write('}\n\nENTRY(Reset_Handler)')
    outfile.write('\n\n')

    # SECTIONS commands
    #
    outfile.write('SECTIONS\n{\n')
    outfile.write(_get_standard_program_SECTIONS(main_flash_region, main_bootflash_region))

    if itcm_region:
        outfile.write(_get_tcm_data_SECTION(itcm_region))
    if dtcm_region:
        outfile.write(_get_tcm_data_SECTION(dtcm_region))

    outfile.write(_get_standard_data_SECTIONS(main_flash_region, main_ram_region))

    if fuses_periph:
        outfile.write('\n    /* Device configuration fuses */')
        outfile.write(_get_fuse_SECTIONS(unique_addr_spaces, periph))

    outfile.write('\n}\n')


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


def _find_biggest_memory_region(address_spaces: list[DeviceAddressSpace],
                                type: str,
                                is_external: bool,
                                partial_name: str = '') -> DeviceMemoryRegion | None:
    '''Find and return the largest memory region of the given type (flash, ram, io, etc.).

    Set 'is_external' to False to skip over regions marked as external or True to look only for
    external regions. Use the 'partial_name' parameter to further filter regions to only ones
    containing the given string in their name. This match is not case sensitive. This will return
    a copy of the region with the starting address of the containing address space added to the
    found region. This will return None if a region of the given type cannot be found.
    '''
    biggest: DeviceMemoryRegion | None = None

    for addr_space in address_spaces:
        for region in addr_space.mem_regions:
            if region.external != is_external  or  type != region.type.lower():
                continue

            if partial_name  and  partial_name.lower() not in region.name.lower():
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


def _get_memory_symbols(main_flash_region: DeviceMemoryRegion,
                        main_ram_region: DeviceMemoryRegion) -> str:
    '''Return a set of linker symbols giving the start and size of ROM, RAM, and any other useful
    tidbits.
    '''
    symbol_str: str = f'''
        /* Internal flash base address and size in bytes. */
        __ROM_BASE = 0x{main_flash_region.start_addr:08X};
        __ROM_SIZE = 0x{main_flash_region.size:08X};

        /* Internal RAM base address and size in bytes. */
        __RAM_BASE = 0x{main_ram_region.start_addr:08X};
        __RAM_SIZE = 0x{main_ram_region.size:08X};

        /* Stack and heap configuration. 
           Modify these using the --defsym option to the linker. */
        PROVIDE(__STACK_SIZE = 0x00000400);
        PROVIDE(__HEAP_SIZE  = 0x00000C00);

        /* ARMv8-M stack sealing:
           To use ARMv8-M stack sealing set __STACKSEAL_SIZE to 8 otherwise keep 0. */
        __STACKSEAL_SIZE = 0;
        '''

    return textwrap.dedent(symbol_str)


def _get_MEMORY_regions(address_spaces: list[DeviceAddressSpace],
                        main_flash_region: DeviceMemoryRegion,
                        main_ram_region: DeviceMemoryRegion,
                        main_bootflash_region: DeviceMemoryRegion | None) -> str:
    '''Return the memory regions on the device formatted for the MEMORY linker script command.
    '''
    memory_cmd: str = ''

    for addr_space in address_spaces:
        for region in addr_space.mem_regions:
            name: str = region.name.lower()
            start: int = addr_space.start_addr + region.start_addr
            size: int = region.size

            # We need to add some region attributes to the main flash and RAM sections. Unfortunately,
            # the device info we can get from the ATDF files is not totally helpful here.
            if name == main_flash_region.name.lower():
                memory_cmd += f'    {name:<34} (rx)  : ORIGIN = 0x{start:08X}, LENGTH = 0x{size:08X}\n'
            elif main_bootflash_region  and  name == main_bootflash_region.name.lower():
                memory_cmd += f'    {name:<34} (rx)  : ORIGIN = 0x{start:08X}, LENGTH = 0x{size:08X}\n'
            elif name == main_ram_region.name.lower():
                memory_cmd += f'    {name:<34} (rwx) : ORIGIN = 0x{start:08X}, LENGTH = 0x{size:08X}\n'
            else:
                memory_cmd += f'    {name:<40} : ORIGIN = 0x{start:08X}, LENGTH = 0x{size:08X}\n'

    return memory_cmd


def _get_fuse_MEMORY(addr_spaces: list[DeviceAddressSpace],
                     fuses_periph: PeripheralGroup) -> str:
    '''Return the device fuse locations formatted for the MEMORY linker script command.
    '''
    memory_cmd: str = ''

    for inst in fuses_periph.instances:
        for ref in inst.reg_group_refs:
            # Find the matching register group for this reference.
            reg_group: RegisterGroup | None = None
            for group in fuses_periph.reg_groups:
                if group.name == ref.module_name:
                    reg_group = group
                    break

            if not reg_group:
                continue

            base_addr = ref.offset + _find_start_of_address_space(addr_spaces, ref.addr_space)

            for member in reg_group.members:
                # There are multiple of some registers, so make sections for each one.
                if member.count > 0:
                    for i in range(member.count):
                        fuse_addr = base_addr + member.offset + (4*i)
                        region_name = ref.instance_name.lower() + '_' + member.name.lower() + str(i)

                        memory_cmd += f'    {region_name:<40} : ORIGIN = 0x{fuse_addr:08X}, LENGTH = 0x04\n'
                else:
                    fuse_addr = base_addr + member.offset
                    region_name = ref.instance_name.lower() + '_' + member.name.lower()

                    memory_cmd += f'    {region_name:<40} : ORIGIN = 0x{fuse_addr:08X}, LENGTH = 0x04\n'

    return memory_cmd


def _get_standard_program_SECTIONS(main_flash_region: DeviceMemoryRegion,
                                   main_bootflash_region: DeviceMemoryRegion | None) -> str:
    '''Return the standard program sections that would be in a SECTIONS command for Arm linker scripts.
     
    The SECTIONS command indicates how object file sections will map into the memory regions from
    the MEMORY command. The names of the program flash, boot flash, and RAM memory regions are not
    consistent in the ATDF files for different devices, so the caller will need to provide those.
    '''
    vectors_region: str = main_flash_region.name.lower()
    if main_bootflash_region:
        vectors_region = main_bootflash_region.name.lower()

    progflash_name: str = main_flash_region.name.lower()

    sections_cmd: str = f'''
        .vectors :
        {{
            KEEP(*(.vectors*))
            KEEP(*(.reset*))
        }} > {vectors_region}

        .text :
        {{
            *(.text*)

            KEEP(*(.init))
            KEEP(*(.fini))

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
        }} > {progflash_name}

        /*
         * SG veneers:
         * All SG veneers are placed in the special output section .gnu.sgstubs. Its start address
         * must be set, either with the command line option '--section-start' or in a linker script,
         * to indicate where to place these veneers in memory.
         */
        .gnu.sgstubs :
        {{
            . = ALIGN(32);
            KEEP(*(.gnu.sgstubs))
        }} > {progflash_name}

        .ARM.extab :
        {{
            *(.ARM.extab* .gnu.linkonce.armextab.*)
        }} > {progflash_name}

        __exidx_start = .;
        .ARM.exidx :
        {{
            *(.ARM.exidx* .gnu.linkonce.armexidx.*)
        }} > {progflash_name}
        __exidx_end = .;

        PROVIDE(__etext = LOADADDR(.data));

        '''

    sections_cmd = textwrap.dedent(sections_cmd)
    return textwrap.indent(sections_cmd, '    ')


def _get_tcm_data_SECTION(tcm_region: DeviceMemoryRegion) -> str:
    '''Return a section used for the Tightly-Coupled Memory feature some Arm devices have.
    '''
    region_name = tcm_region.name.lower()

    if 'itcm' in region_name:
        section_name: str = 'itcm'
    elif 'dtcm' in region_name:
        section_name: str = 'dtcm'
    else:
        raise ValueError(f'Unrecognized TCM section name {region_name}')

    section_cmd: str = f'''
        .{section_name} : ALIGN(4)
        {{
            *(.{section_name})
            *(.{section_name}.*)
        }} > {region_name}

        PROVIDE(__{section_name}_start = ADDR(.{section_name}));
        PROVIDE(__{section_name}_end = ADDR(.{section_name}) + SIZEOF(.{section_name}));
        '''

    section_cmd = textwrap.dedent(section_cmd)
    return textwrap.indent(section_cmd, '    ')


def _get_standard_data_SECTIONS(main_flash_region: DeviceMemoryRegion,
                                main_ram_region: DeviceMemoryRegion) -> str:
    '''Return the standard data sections that would be in a SECTIONS command for Arm linker scripts.
     
    The SECTIONS command indicates how object file sections will map into the memory regions from
    the MEMORY command. The names of the program flash, boot flash, and RAM memory regions are not
    consistent in the ATDF files for different devices, so the caller will need to provide those.
    '''
    progflash_name: str = main_flash_region.name.lower()
    ram_name: str = main_ram_region.name.lower()

    sections_cmd: str = f'''
        .data : ALIGN(4)
        {{
            *(vtable)
            *(.data)
            *(.data.*)
            *(.gnu.linkonce.d.*)

            KEEP(*(.jcr*))
            . = ALIGN(4);
        }} > {ram_name} AT > {progflash_name}

        PROVIDE(__data_start = ADDR(.data));
        PROVIDE(__data_source = LOADADDR(.data));

        /* Thread local initialized data. This gets space allocated as it is expected to be placed
         * in ram to be used as a template for TLS data blocks allocated at runtime. We're slightly
         * abusing that by placing the data in flash where it will be copied into the allocated ram
         * addresses by the existing data initialization code in crt0.
         */
        .tdata :
        {{
            *(.tdata .tdata.* .gnu.linkonce.td.*)
            PROVIDE(__data_end = .);
            PROVIDE(__tdata_end = .);
        }} > {ram_name} AT > {progflash_name}

        PROVIDE(__non_tls_data_end = ADDR(.tdata));
        PROVIDE(__tls_base = ADDR(.tdata));
        PROVIDE(__tdata_start = ADDR(.tdata));
        PROVIDE(__tdata_source = LOADADDR(.tdata) );
        PROVIDE(__tdata_source_end = LOADADDR(.tdata) + SIZEOF(.tdata) );
        PROVIDE(__data_source_end = __tdata_source_end );
        PROVIDE(__tdata_size = SIZEOF(.tdata) );

        PROVIDE(__edata = __data_end );
        PROVIDE(_edata = __data_end );
        PROVIDE(edata = __data_end );
        PROVIDE(__data_size = __data_end - __data_start );
        PROVIDE(__data_source_size = __data_source_end - __data_source );

        .tbss (NOLOAD) :
        {{
            *(.tbss .tbss.* .gnu.linkonce.tb.*)
            *(.tcommon)
            PROVIDE( __tls_end = . );
            PROVIDE( __tbss_end = . );
        }} > {ram_name} AT > {ram_name}

        PROVIDE(__bss_start = ADDR(.tbss));
        PROVIDE(__tbss_start = ADDR(.tbss));
        PROVIDE(__tbss_offset = ADDR(.tbss) - ADDR(.tdata) );
        PROVIDE(__tbss_size = SIZEOF(.tbss) );
        PROVIDE(__tls_size = __tls_end - __tls_base );
        PROVIDE(__tls_align = MAX(ALIGNOF(.tdata), ALIGNOF(.tbss)) );
        PROVIDE(__arm32_tls_tcb_offset = MAX(8, __tls_align) );
        PROVIDE(__arm64_tls_tcb_offset = MAX(16, __tls_align) );

        /*
        * The linker special cases .tbss segments which are
        * identified as segments which are not loaded and are
        * thread_local.
        *
        * For these segments, the linker does not advance 'dot'
        * across them.  We actually need memory allocated for tbss,
        * so we create a special segment here just to make room
        */
        /*
        .tbss_space (NOLOAD) :
        {{
            . = ADDR(.tbss);
            . = . + SIZEOF(.tbss);
        }} > {ram_name} AT > {ram_name}
        */
        
        .bss :
        {{
            . = ALIGN(4);
            *(.bss)
            *(.bss.*)
            *(COMMON)
            . = ALIGN(4);
            __bss_end = .;
        }} > {ram_name} AT > {ram_name}

        PROVIDE(__non_tls_bss_start = ADDR(.bss) );
        PROVIDE(__end = __bss_end );
        PROVIDE(_end = __bss_end );
        PROVIDE(end = __bss_end );
        PROVIDE(__bss_size = __bss_end - __bss_start );

        .heap (NOLOAD) :
        {{
            . = ALIGN(8);
            . = . + __HEAP_SIZE;
            . = ALIGN(8);
            __HeapLimit = .;
            __llvm_libc_heap_limit = .;
        }} > {ram_name}

        .stack (ORIGIN({ram_name}) + LENGTH({ram_name}) - __STACK_SIZE - __STACKSEAL_SIZE) (NOLOAD) :
        {{
            . = ALIGN(8);
            __StackLimit = .;
            . = . + __STACK_SIZE;
            . = ALIGN(8);
            __StackTop = .;
        }} > {ram_name}
        PROVIDE(__stack = __StackTop);

        /* ARMv8-M stack sealing:
            to use ARMv8-M stack sealing uncomment '.stackseal' section
          */
        /*
        .stackseal (ORIGIN({ram_name}) + LENGTH({ram_name}) - __STACKSEAL_SIZE) (NOLOAD) :
        {{
            . = ALIGN(8);
            __StackSeal = .;
            . = . + 8;
            . = ALIGN(8);
        }} > {ram_name}
        */

        /* Check if data + heap + stack exceeds RAM limit */
        ASSERT(__StackLimit >= __HeapLimit, "RAM region overflowed with stack")

        '''

    sections_cmd = textwrap.dedent(sections_cmd)
    return textwrap.indent(sections_cmd, '    ')


def _get_fuse_SECTIONS(addr_spaces: list[DeviceAddressSpace], fuses: PeripheralGroup) -> str:
    '''Create special output sections for the given peripherals assuming they are fuses. This will
    look through the address spaces to find one to which they belong.
    '''
    fuse_str: str = ''

    for inst in fuses.instances:
        for ref in inst.reg_group_refs:
            # Find the matching register group for this reference.
            reg_group: RegisterGroup | None = None
            for group in fuses.reg_groups:
                if group.name == ref.module_name:
                    reg_group = group
                    break

            if not reg_group:
                continue

            for member in reg_group.members:
                # There are multiple of some registers, so make sections for each one.
                if member.count > 0:
                    for i in range(member.count):
                        region_name = ref.instance_name.lower() + '_' + member.name.lower() + str(i)
                        section_name = '.' + region_name

                        fuse_str += f'\n{section_name:<40} : {{ KEEP(*({section_name})) }} > {region_name}'
                else:
                    region_name = ref.instance_name.lower() + '_' + member.name.lower()
                    section_name = '.' + region_name

                    fuse_str += f'\n{section_name:<40} : {{ KEEP(*({section_name})) }} > {region_name}'

    return textwrap.indent(fuse_str, '    ')


def _find_start_of_address_space(addr_spaces: list[DeviceAddressSpace], name: str) -> int:
    '''Search the list of address spaces for the one with the given name and return its start
    address.
    '''
    for space in addr_spaces:
        if name == space.id:
            return space.start_addr

    raise ValueError(f'Address space {name} could not be found!')

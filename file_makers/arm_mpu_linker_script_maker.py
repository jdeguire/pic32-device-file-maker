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

'''arm_mpu_linker_script_maker.py

Contains a single public function to make a GNU linker script file for a single Arm Cortex-A or
ARM MPU device. This is based on the sample linker scripts found in Arm CMSIS 6 and from a linker
script provided with the Microchip XC32 toolchain.
'''

from device_info import *
import itertools
import operator
from . import strings
import textwrap
from typing import IO


def run(devinfo: DeviceInfo, outfile: IO[str]) -> None:
    '''Make a linker script for the given device assuming is a a PIC or SAM MPU device
    '''

    #
    # First gather info on our memory spaces.
    #
    address_spaces = _remove_known_problematic_regions(devinfo.address_spaces)
    unique_addr_spaces, aliases = _remove_overlapping_memory(address_spaces)

    # Sort the now-not-overlapping memory regions by starting address.
    # See https://docs.python.org/3/howto/sorting.html
    for addr_space in unique_addr_spaces:
        addr_space.mem_regions.sort(key=operator.attrgetter('start_addr'))

    # Find our main DDR memory region. The ATDF files are not consistent on how these are named nor
    # their attributes, so for now we will have to just look for known names.
    main_ddr_region = (_find_region_by_name(unique_addr_spaces, aliases, 'ddr_cs', exact=True)    or
                       _find_region_by_name(unique_addr_spaces, aliases, 'ebi_mpddr', exact=True) or
                       _find_region_by_name(unique_addr_spaces, aliases, 'ddr', exact=False))
    if not main_ddr_region:
        raise RuntimeError(f'Failed to find a DDR region for {devinfo.name}')

    # Do the same for our main SRAM region.
    main_sram_region = (_find_region_by_name(unique_addr_spaces, aliases, 'sram0', exact=True)    or
                        _find_region_by_name(unique_addr_spaces, aliases, 'iram', exact=True)     or
                        _find_region_by_name(unique_addr_spaces, aliases, 'sram', exact=False)    or
                        _find_region_by_name(unique_addr_spaces, aliases, 'iram', exact=False))
    if not main_sram_region:
        raise RuntimeError(f'Failed to find an SRAM region for {devinfo.name}')

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
    #
    outfile.write('/*\n')
    outfile.write(strings.get_generated_by_string(' * '))
    outfile.write(' * \n')
    outfile.write(strings.get_cmsis_license(' * ', strings.COPYRIGHT_CMSIS))
    outfile.write(' */\n/*\n')
    outfile.write(strings.get_mchp_bsd_license(' * '))
    outfile.write(' */\n\n')

    # MEMORY command
    #
    outfile.write(_get_memory_symbols())
    outfile.write('\n\nMEMORY\n{\n')
    outfile.write(_get_MEMORY_regions(unique_addr_spaces, main_ddr_region, main_sram_region))
    if fuses_periph:
        outfile.write(_get_fuse_MEMORY(unique_addr_spaces, fuses_periph))
    outfile.write('}\n\nENTRY(Reset_Handler)')
    outfile.write('\n\n')

    # Region aliases
    #
    for key, vals in aliases.items():
        for v in vals:
            outfile.write(f'REGION_ALIAS("{v.lower()}", {key.lower()});\n')

    # SECTIONS commands
    #
    outfile.write('\nSECTIONS\n{\n')
    outfile.write(_get_standard_program_SECTIONS(main_ddr_region, main_sram_region))
    outfile.write(_get_standard_data_SECTIONS(main_ddr_region))

    if fuses_periph:
        outfile.write('\n    /* Device configuration fuses */')
        outfile.write(_get_fuse_SECTIONS(unique_addr_spaces, periph))

    outfile.write('\n}\n')


def _remove_known_problematic_regions(address_spaces: list[DeviceAddressSpace]) -> list[DeviceAddressSpace]:
    '''Remove regions that are known to be problematic from the given address spaces.

    This is basically a hacky workaround to some "overzealous" ATDF files that define a memory region
    that encompasses other regions we care about. An example of this is the SAMA5D27WLSOM1, which
    has a IMEMORIES region that overlaps with all of the internal memory regions on the part. We
    need those regions, so we need to remove the IMEMORIES region.
    '''
    new_spaces: list[DeviceAddressSpace] = []

    for addr_space in address_spaces:
        new_regions: list[DeviceMemoryRegion] = []

        for region in addr_space.mem_regions:
            if not region.name.lower() == 'imemories':
                new_regions.append(region)

        new_spaces.append(DeviceAddressSpace(id = addr_space.id,
                                             start_addr = addr_space.start_addr,
                                             size = addr_space.size,
                                             mem_regions = new_regions))

    return new_spaces


def _remove_overlapping_memory(address_spaces: list[DeviceAddressSpace]) -> (
    tuple[list[DeviceAddressSpace], dict[str, set[str]]] ):
    '''Return a list of address spaces with overlapping regions removed and a list of regions that
    are aliases of one another.

    Some devices, like the SAME54 series, have multiple regions with the same starting address. We
    don't want those in our linker script because they will produce linker errors, so we need to 
    remove them. Do this by finding and keeping only the bigger region of the overlapping spaces.
    To keep us sane, this assumes that any overlapping regions are contained wholly within another
    region. Otherwise, we probably have bigger problems and a really weird memory layout.

    If two regions are the same size and location, then one is an alias of the other. Track and
    return these aliases separately so we can add these aliases to the linker script later.
    '''
    new_spaces: list[DeviceAddressSpace] = []
    aliases: dict[str, set[str]] = {}

    for addr_space in address_spaces:
        # In Python, both sets and dicts (maps) use curly braces. Any empty pair of braces "{}"
        # creates an empty dict by default, so use 'set()' to create an empty set.
        regions_to_remove: set[str] = set()

        for i, j in itertools.combinations(addr_space.mem_regions, 2):
            if i.name in regions_to_remove:
                continue

            i_end = i.start_addr + i.size
            j_end = j.start_addr + j.size

            if i.start_addr == j.start_addr  and  i_end == j_end:
                # These regions are aliases of one another.
                if i.name in aliases:
                    aliases[i.name].add(j.name)
                else:
                    aliases[i.name] = {j.name}

                regions_to_remove.add(j.name)
            elif i.start_addr >= j.start_addr  and  i_end <= j_end:
                # Region i is contained in region j, so remove region i.
                regions_to_remove.add(i.name)
            elif j.start_addr >= i.start_addr  and  j_end <= i_end:
                # Region j is contained in region i, so remove region j.
                regions_to_remove.add(j.name)

        new_regions: list[DeviceMemoryRegion] = []

        for region in addr_space.mem_regions:
            if region.name in regions_to_remove:
                if region.name in aliases:
                    del aliases[region.name]
            else:
                new_regions.append(region)

        new_spaces.append(DeviceAddressSpace(id = addr_space.id,
                                             start_addr = addr_space.start_addr,
                                             size = addr_space.size,
                                             mem_regions = new_regions))
        
    return (new_spaces, aliases)


def _find_region_by_name(address_spaces: list[DeviceAddressSpace],
                         aliases: dict[str, set[str]],
                         name: str,
                         exact: bool) -> DeviceMemoryRegion | None:
    '''Find and return the first region available with the given name.

    The name is not case-sensitive. If 'exact' is True, then the region name must match the given
    name exactly. Otherwise, this will return the first region containing the name.
    '''
    name = name.lower()

    # Check if our target region is an alias of another region. If so, then we need to look for
    # that other region instead.
    for key, vals in aliases.items():
        found = False
        for v in vals:
            if name == v.lower():
                name = key.lower()
                found = True
                break

        if found:
            break

    for addr_space in address_spaces:
        for region in addr_space.mem_regions:
            region_name = region.name.lower()

            if (not exact  and  name in region_name)  or  name == region_name:
                start = addr_space.start_addr + region.start_addr
                return DeviceMemoryRegion(name = region.name,
                                          start_addr = start,
                                          size = region.size,
                                          type = region.type,
                                          page_size = region.page_size,
                                          external = region.external)

    return None    

def _get_memory_symbols() -> str:
    '''Return a set of linker symbols giving the start and size of ROM, RAM, and any other useful
    tidbits.
    '''
    symbol_str: str = f'''
        /* Stack and heap configuration. 
           Modify these using the --defsym option to the linker. */
        PROVIDE(__STACK_SIZE = 4096);
        PROVIDE(__FIQ_STACK_SIZE = 512);
        PROVIDE(__IRQ_STACK_SIZE = 512);
        PROVIDE(__SVC_STACK_SIZE = 4096);
        PROVIDE(__ABT_STACK_SIZE = 512);
        PROVIDE(__UND_STACK_SIZE = 512);
        __ALL_STACKS_SIZE = (__STACK_SIZE + __FIQ_STACK_SIZE + __IRQ_STACK_SIZE + __SVC_STACK_SIZE +
                             __ABT_STACK_SIZE + __UND_STACK_SIZE);

        PROVIDE(__HEAP_SIZE  = 1024);
        '''

    return textwrap.dedent(symbol_str)


def _get_MEMORY_regions(address_spaces: list[DeviceAddressSpace],
                        main_ddr_region: DeviceMemoryRegion,
                        main_sram_region: DeviceMemoryRegion) -> str:
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
            if name == main_ddr_region.name.lower():
                memory_cmd += f'    {name:<28} (lwx!r) : ORIGIN = 0x{start:08X}, LENGTH = 0x{size:08X}\n'
            elif name == main_sram_region.name.lower():
                memory_cmd += f'    {name:<28} (wx!r)  : ORIGIN = 0x{start:08X}, LENGTH = 0x{size:08X}\n'
            else:
                memory_cmd += f'    {name:<36} : ORIGIN = 0x{start:08X}, LENGTH = 0x{size:08X}\n'

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


def _get_standard_program_SECTIONS(main_ddr_region: DeviceMemoryRegion,
                                   main_sram_region: DeviceMemoryRegion) -> str:
    '''Return the standard program sections that would be in a SECTIONS command for Arm linker scripts.

    The SECTIONS command indicates how object file sections will map into the memory regions from
    the MEMORY command. The names of the DDR and SRAM memory regions are not consistent in the ATDF
    files for different devices, so the caller will need to provide those.
    '''
    sram_name = main_sram_region.name.lower()
    ddr_name = main_ddr_region.name.lower()

    sections_cmd: str = f'''
        .text :
        {{
            KEEP(*(.reset*))
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
        }} > {ddr_name}

        PROVIDE(__sfixed = ADDR(.text));

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
        }} > {ddr_name}

        .ARM.extab :
        {{
            *(.ARM.extab* .gnu.linkonce.armextab.*)
        }} > {ddr_name}

        __exidx_start = .;
        .ARM.exidx :
        {{
            *(.ARM.exidx* .gnu.linkonce.armexidx.*)
        }} > {ddr_name}
        __exidx_end = .;

        PROVIDE(__stext = LOADADDR(.text));
        PROVIDE(__etext = LOADADDR(.data));

        .relocate :
        {{
            . = ALIGN(4);
            KEEP(*(.vectors*))
            KEEP(*(.fiq_handler))
            *(.ramfunc)
            . = ALIGN(4);
        }} > {sram_name} AT > {ddr_name}

        PROVIDE(__relocate_start = ADDR(.relocate));
        PROVIDE(__relocate_end = ADDR(.relocate) + SIZEOF(.relocate) );
        PROVIDE(__relocate_source = LOADADDR(.relocate));
        PROVIDE(__relocate_source_end = LOADADDR(.relocate) + SIZEOF(.relocate) );
        PROVIDE(__relocate_size = __relocate_end - __relocate_start );
        PROVIDE(__relocate_source_size = __relocate_source_end - __relocate_source );
        PROVIDE(_srelocate = __relocate_start );
        PROVIDE(_erelocate = __relocate_end );

        '''

    sections_cmd = textwrap.dedent(sections_cmd)
    return textwrap.indent(sections_cmd, '    ')


def _get_standard_data_SECTIONS(main_ddr_region: DeviceMemoryRegion) -> str:
    '''Return the standard data sections that would be in a SECTIONS command for Arm linker scripts.

    The SECTIONS command indicates how object file sections will map into the memory regions from
    the MEMORY command. The names of the DDR and SRAM memory regions are not consistent in the ATDF
    files for different devices, so the caller will need to provide those.
    '''
    ddr_name: str = main_ddr_region.name.lower()

    sections_cmd: str = f'''
        .data : ALIGN(4)
        {{
            *(vtable)
            *(.data)
            *(.data.*)
            *(.gnu.linkonce.d.*)

            KEEP(*(.jcr*))
            . = ALIGN(4);
        }} > {ddr_name}

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
        }} > {ddr_name}

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
        }} > {ddr_name}

        PROVIDE(__bss_start = ADDR(.tbss));
        PROVIDE(__tbss_start = ADDR(.tbss));
        PROVIDE(__tbss_offset = ADDR(.tbss) - ADDR(.tdata) );
        PROVIDE(__tbss_size = SIZEOF(.tbss) );
        PROVIDE(__tls_size = __tls_end - __tls_base );
        PROVIDE(__tls_align = MAX(ALIGNOF(.tdata), ALIGNOF(.tbss)) );
        PROVIDE(__arm32_tls_tcb_offset = MAX(8, __tls_align) );
        PROVIDE(__arm64_tls_tcb_offset = MAX(16, __tls_align) );

        PROVIDE(__efixed = __bss_start);

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
        }} > {ddr_name}
        */
        
        .bss (NOLOAD) :
        {{
            . = ALIGN(4);
            *(.bss)
            *(.bss.*)
            *(COMMON)
            . = ALIGN(4);
            __bss_end = .;
        }} > {ddr_name}

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
        }} > {ddr_name}

        .stack (ORIGIN({ddr_name}) + LENGTH({ddr_name}) - __ALL_STACKS_SIZE) (NOLOAD) :
        {{
            . = ALIGN(8);
            __StackLimit = .;
            . = . + __STACK_SIZE;
            . = ALIGN(8);
            __StackTop = .;

            __fiq_stack_limit = .;
            . = . + __FIQ_STACK_SIZE;
            . = ALIGN(8);
            __fiq_stack = .;

            __irq_stack_limit = .;
            . = . + __IRQ_STACK_SIZE;
            . = ALIGN(8);
            __irq_stack = .;

            __svc_stack_limit = .;
            . = . + __SVC_STACK_SIZE;
            . = ALIGN(8);
            __svc_stack = .;

            __abt_stack_limit = .;
            . = . + __ABT_STACK_SIZE;
            . = ALIGN(8);
            __abt_stack = .;

            __und_stack_limit = .;
            . = . + __UND_STACK_SIZE;
            . = ALIGN(8);
            __und_stack = .;
        }} > {ddr_name}
        PROVIDE(__stack = __StackTop);

        /* Check if data + heap + stack exceeds RAM limit */
        ASSERT(__StackLimit >= __HeapLimit, "The stacks are too big to fit into memory")

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

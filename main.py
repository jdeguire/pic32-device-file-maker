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
#
# #####
#
# main.py
#
# This is the top-level module to run if you want to generate device-specific files for Microchip
# Technology's PIC32 and SAM series of microcontroller devices. It uses a device database that comes
# with Microchip IDEs to generate device headers, linker scripts, and startup code. It will pop up a
# file dialog asking you where this database is located. If you have MPLAB X installed, look for a
# "packs" directory in there or look under your user directory ("C:/Users/your_name") for a
# ".mchp_packs" directory. Harmony 3 might also come with its own packs.
#
# At this time, this will generate files only for the Arm Cortex-M devices. The MIPS and Cortex-A
# devices might come later. The MIPS devices are not seeing further development and MIPS itself is
# basically dead (MIPS Technologies has moved to RISC-V). I don't really know enough about the 
# Cortex-A devices to generate the proper stuff for them, so I'd need to get some experience with
# them before doing that.
#
# These files are meant to be used with a supporting toolchain, such as Clang or an appropriate GCC.
# You could maybe use these with XC32, but if you're going to use that then just use the files it
# already comes with.
#
# I do NOT guarantee that these files will be compatible with code that uses XC32. That is, things
# like linker or register definitions may look different here versus what is provided with XC32.
# Any similarity to Microchip's device files is either coincidental or the result of functional
# requirements. This code, presumably like Microchip's/Atmel's code, uses Arm CMSIS 6 as a template
# and so there will probably be a lot of similarities because of that.
#
# This project uses the default XML parsers in Python, which are vulnerable to certain attacks
# relying on XML entities referecing other entities multiple times. Specifically, the attacks are
# called "Billion Laughs" and "Quadratic Blowup". Therefore, you should ensure that the packs files
# you give to this module are really from Microchip and not some malicious user. See the info here:
# https://docs.python.org/3/library/xml.html#module-xml. That page has a link to a package called
# "defusedxml" you can use if you want to be safer. You should just need to get it from PIP and
# update the import statement for ElementTree below and in other modules to use it.
#

from atdf_reader import AtdfReader
import device_info
from file_makers import *
import os
from pathlib import Path
import shutil
import tkinter
import tkinter.filedialog
from typing import IO


def get_dir_from_dialog(title: str | None = None, mustexist: bool = True) -> str:
    '''Open a file dialog asking the user to open a directory, returning what the user selects or
    None if the dialog is cancelled.

    The arguments let the caller specify a title for the dialog box and whether or not the choosen
    directory must already exist. 
    '''
    tk_root = tkinter.Tk()
    tk_root.withdraw()

    return tkinter.filedialog.askdirectory(title=title, mustexist=mustexist)

def get_atdf_paths_from_dir(packs_dir: str) -> list[Path]:
    '''Return a list of Path objects in which each Path points to a file with the '.atdf' extension.
    '''
    atdf_paths = []
    packs_path = Path(packs_dir)
    for rootname, _, filenames in os.walk(packs_path):
        for name in filenames:
            p = Path(rootname, name)
# TODO: This is hardcoded to just a couple of devices for now. Remove this later.
#       We could probably do some basic filtering here, like removing "PIC32M" stuff.
#            if '.atdf' == p.suffix:
            if 'pic32cz8110ca80208.atdf' == name.lower()  or 'atsame54p20a.atdf' == name.lower():
                atdf_paths.append(p)

    return atdf_paths

def create_all_processors_header(hdr: IO[str],
                                 basename: str,
                                 device_families: dict[str, list[str]]
                                 ) -> None:
    '''Make a big header file that encompasses all of the devices for which this app has made files.

    This lets a user include a single header file that will find the correct device header file
    based on macros instead of requiring a user to always remember to include the device-specific
    header file. The inputs are the file-like object to which the data will be written, the base
    name of the file without path or extension, and a dict of device families to lists of devices.
    ''' 
    # Write the header block with copyright info.
    hdr.write('/*\n')
    hdr.write(strings.get_generated_by_string(' * '))
    hdr.write(' * \n')
    hdr.write(strings.get_non_cmsis_apache_license(' * '))
    hdr.write(' */\n\n')

    # Include guard
    hdr.write(f'#ifndef {basename.upper()}_H_\n')
    hdr.write(f'#define {basename.upper()}_H_\n\n')

    first_family = True
    for family,devices in device_families.items():
        if not family.startswith('cortexm_'):
            continue

        family = family.split('_', 1)[1]

        if first_family:
            hdr.write(f'#if defined(__{family})\n')
        else:
            hdr.write(f'#elif defined(__{family})\n')
        
        first_family = False

        first_dev = True
        for d in devices:
            name = d.upper()

            if first_dev: 
                hdr.write(f'#  if defined(__{name}__)\n')
            else:
                hdr.write(f'#  elif defined(__{name}__)\n')
            
            first_dev = False

            hdr.write(f'#    include "proc/{d.lower()}.h"\n')
        
        hdr.write('#  else\n')
        hdr.write(f'#    error Unknown device for {family} family!\n')
        hdr.write('#  endif\n')

    hdr.write('#else\n')
    hdr.write('#  error Unknown device family!\n')
    hdr.write('#endif\n')

    hdr.write(f'\n#endif /* ifndef {basename.upper()}_H_ */\n')

def remove_file_tag(file_line: str, tagname: str) -> tuple[str, str]:
    '''Remove a tag, such as {LICENSE: ... } and {DEST: ... } from the given line, return the rest
    of the contents within the braces after being trimmed of whitespace and the stuff that was 
    before the tag.
    '''
    tag = file_line.split(f'{{{tagname}:', 1)     # Split start of tag
    tag[1] = tag[1].split('}', 1)[0]            # Remove '}' from end of tag
    tag[1] = tag[1].strip()                     # Removing leading and trailing whitespace
    return (tag[1], tag[0])

def copy_premade_files(src_dir: str, dest_dir: str) -> None:
    '''Copy the premade files from the premade src directory to their appropriate destinations.

    This currently will not go into subdirectories. 
    
    Each premade file can optionally have tags at the top of them to indicate some extra info. The
    "{DEST:...}" tag indicates the destination and the "{LICENSE:...}" tag indicates that a license
    needs to be added to that location. There can be only one tag per line.
    '''
    file_list: list[str] = [f for f in os.listdir(src_dir) if os.path.isfile(os.path.join(src_dir, f))]

    for f in file_list:
        contents = ''
        file_dest = f

        with open(os.path.join(src_dir, f), 'r', encoding='utf-8') as f_in:
            for l in f_in:
                if '{DEST:' in l:
                    file_dest, _ = remove_file_tag(l, 'DEST')
                elif '{LICENSE:' in l:
                    license_type, prefix = remove_file_tag(l, 'LICENSE')
                    prefix += ' '

                    contents += strings.get_generated_by_string(prefix)
                    contents += prefix + '\n'
                    if 'NON-CMSIS' in license_type:
                        contents += strings.get_non_cmsis_apache_license(prefix)
                    elif 'CMSIS' in license_type:
                        contents += strings.get_cmsis_apache_license(prefix)
                    contents += prefix + '\n'
                else:
                    contents += l

        outpath = os.path.normpath(dest_dir + '/' + file_dest)
        os.makedirs(os.path.dirname(outpath), exist_ok = True)

        with open(outpath, 'w', encoding='utf-8', newline='\n') as f_out:
            f_out.write(contents)
        

if '__main__' == __name__:
# TODO: Remove this hardcoded path when I'm doing testing.
#    packs_dir = get_dir_from_dialog(title='Open packs directory')
    packs_dir = '/home/jesse/projects/packs'
    if not packs_dir:
        exit(0)

    print(f'Got file path {packs_dir}')
    print('-----')

    our_path = Path(os.path.abspath(os.path.dirname(__file__)))
    output_path = our_path / 'pic32-device-files'
    if os.path.exists(output_path):
        shutil.rmtree(output_path)

    peripherals_to_make: dict[str, device_info.PeripheralGroup] = {}
    peripheral_header_prefix = 'periph/'
    fuses_header_prefix = 'fuses/'

    device_families: dict[str, list[str]] = {}

    # Make the files specific to each device and collect their perpiherals so we can make
    # those later. 
    for p in get_atdf_paths_from_dir(packs_dir):
        atdf = AtdfReader(p)

        if not atdf.get_device_cpu().startswith('cortex-m'):
            continue

        print(f'Creating files for device {atdf.get_device_name()} ({atdf.get_device_cpu()})')

        devinfo = atdf.get_all_device_info()

        # Linker script
        #
        ld_path = output_path / 'cortex-m' / 'lib' / 'proc' / devinfo.name.lower()
        ld_name = 'default.ld'
        ld_loc = ld_path / ld_name

        os.makedirs(ld_path, exist_ok = True)

        with open(ld_loc, 'w', encoding='utf-8', newline='\n') as ld:
            cortexm_linker_script_maker.run(devinfo, ld)

        # C device-specifc header file
        #
        dev_header_path = output_path / 'cortex-m' / 'include' / 'proc'
        dev_header_name = devinfo.name.lower() + '.h'
        dev_header_loc = dev_header_path / dev_header_name

        os.makedirs(dev_header_path, exist_ok = True)

        with open(dev_header_loc, 'w', encoding='utf-8', newline='\n') as hdr:
            cortexm_c_device_header_maker.run(devinfo, hdr, peripheral_header_prefix, 
                                              fuses_header_prefix)

        # Device fuses are a special peripheral, so look for those and handle them here. Assume
        # each device has at most one fuse peripheral called FUSES for now. You can find the special
        # handling this app does for fuses by searching for 'fuses' with the single quotes.
        #
        for periph in devinfo.peripherals:
            if 'fuses' == periph.name.lower():
                fuses_header_path = output_path / 'cortex-m' / 'include' / 'proc' / fuses_header_prefix
                fuses_header_name = devinfo.name.lower() + '.h'
                fuses_header_loc = fuses_header_path / fuses_header_name

                os.makedirs(fuses_header_path, exist_ok = True)

                with open(fuses_header_loc, 'w', encoding='utf-8', newline='\n') as hdr:
                    basename = devinfo.name.lower() + '_fuses'
                    cortexm_c_periph_header_maker.run(basename, periph, hdr)

        # Make a dict of peripherals we need to make. Doing this ensures we make each unique
        # peripheral only once. We do not need to make core peripherals because they are already
        # defined in CMSIS headers.
        #
        for periph in devinfo.peripherals:
            if 'fuses' != periph.name.lower()  and  periph.id  and  'system_ip' not in periph.id.lower():
                full_name = 'cortexm_' + periph.name + '_' + periph.id

                if full_name not in peripherals_to_make:
                    peripherals_to_make[full_name] = periph

        # C interrupt vectors file
        #
        vectors_src_path = output_path / 'cortex-m' / 'lib' / 'proc' / devinfo.name.lower()
        vectors_src_name = 'vectors.c'
        vectors_src_loc = vectors_src_path / vectors_src_name

        os.makedirs(vectors_src_path, exist_ok = True)

        with open(vectors_src_loc, 'w', encoding='utf-8', newline='\n') as vec:
            proc_header_name = 'which_pic32.h'
            cortexm_c_vectors_maker.run(proc_header_name, devinfo.interrupts, vec)

        # Clang configuration file
        #
        config_path = output_path / 'cortex-m' / 'config'
        config_name = devinfo.name.lower() + '.cfg'
        config_loc = config_path / config_name

        os.makedirs(config_path, exist_ok = True)

        with open(config_loc, 'w', encoding='utf-8', newline='\n') as cfg:
            default_ld_loc = os.path.relpath(ld_loc, config_path)
            cortexm_config_file_maker.run(devinfo, cfg, default_ld_loc)


        # Gather device names and families we can use to make an all-encompassing processor header
        # file. That is, instead of including the individual processor header in your project, you
        # can be lazy and include this one to let it figure out what processor you have.
        #
        family = 'cortexm_' + devinfo.family.upper()
        if family in device_families:
            device_families[family].append(devinfo.name)
        else:
            device_families[family] = [devinfo.name]

        # TODO: We need to implement startup code, but that can probably be made common to all devices.
        #       This is especially true if we can put the vectors into their own file.
    # End for-loop

    # Make all of the peripheral implementation C headers. These are shared among various devices.
    #
    for key,val in peripherals_to_make.items():
        if key.startswith('cortexm_'):
            periph_name = key.split('_', 1)[1].lower()
            print(f'Creating peripheral header for {periph_name}')

            periph_header_path = output_path / 'cortex-m' / 'include' / 'proc' / peripheral_header_prefix
            periph_header_name = periph_name + '.h'
            periph_header_loc = periph_header_path / periph_header_name

            os.makedirs(periph_header_path, exist_ok = True)

            with open(periph_header_loc, 'w', encoding='utf-8', newline='\n') as hdr:
                cortexm_c_periph_header_maker.run(periph_name, val, hdr)

    # Make the all-encompassing processor header file.
    #
    big_proc_header_path = output_path / 'cortex-m' / 'include'
    big_proc_header_base = 'which_pic32'
    big_proc_header_name = big_proc_header_base + '.h'
    big_proc_header_loc = big_proc_header_path / big_proc_header_name

    os.makedirs(big_proc_header_path, exist_ok = True)

    print('Creating big processor header')
    with open(big_proc_header_loc, 'w', encoding='utf-8', newline='\n') as hdr:
        create_all_processors_header(hdr, big_proc_header_base, device_families)

    # Copy the premade files to their proper destinations.
    #
    premade_src = our_path / 'premade'
    premade_dst = output_path
    print(f'Copying premade files')
    copy_premade_files(premade_src.as_posix(), premade_dst.as_posix())

    exit(0)

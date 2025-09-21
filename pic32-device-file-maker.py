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

import argparse
from atdf_reader import AtdfReader
from device_info import DeviceInfo, PeripheralGroup
from file_makers import *
import multiprocessing
import os
from pathlib import Path
import shutil


def get_atdf_paths_from_dir(packs_dir: str) -> list[Path]:
    '''Return a list of Path objects in which each Path points to a file with the '.atdf' extension.
    '''
    atdf_paths = {}
    packs_path = Path(packs_dir)
    for rootname, _, filenames in os.walk(packs_path):
        for name in filenames:
            p = Path(rootname, name)

            if '.atdf' != p.suffix:
                continue

            # All PIC32M devices are MIPS. We are not supporting those right now, so they're easy
            # to filter out here.
            if name.lower().startswith('pic32m')  or  name.lower().startswith('32m'):
                continue

            # Overwrite previous path if one was already found for this device. This avoids
            # duplicate entries when multiple pack versions are installed.
            atdf_paths[name] = p

    return list(atdf_paths.values())


def parse_atdf_file_at_path(atdf_path: Path) -> DeviceInfo:
    '''Open a single .atdf file and parse it into a DeviceInfo structure.
    '''
    print(f'Parsing file {atdf_path}', flush=True)
    return AtdfReader(atdf_path).get_all_device_info()


def get_device_infos_from_atdf_paths(atdf_paths: list[Path], jobs: int = 0) -> list[DeviceInfo]:
    '''Parse all of the ATDF files in the list and return corresponding DeviceInfo structures.

    This will skip over unsupported architectures and so the output list might have fewer elements
    than the input list. Use 'jobs' to control how many processes this spawns. The default is to
    spawn one per process CPU (as returned by os.cpu_count()).
    '''
    devinfos: list[DeviceInfo] = []

    max_jobs: int | None = os.cpu_count()

    # Pick a reasonable default if the number of CPUs cannot be determined.
    if max_jobs is None:
        max_jobs = 4

    if jobs <= 0  or  jobs > max_jobs:
        jobs = max_jobs

    with multiprocessing.Pool(processes=jobs) as pool:
        devinfos = pool.map(parse_atdf_file_at_path, atdf_paths, chunksize=6)

    return devinfos


def open_for_writing(outfile: Path):
    '''Open a file for writing with UTF-8 encoding and Unix line ending, creating the file and any
    intermediate directories to it if needed.

    This is really just a convenient wrapper around os.makedirs() and open() because this file uses
    both of those a lot.
    '''
    if outfile.is_dir():
        raise RuntimeError(f'Path {outfile} must be a file, not a directory.')

    os.makedirs(outfile.parent, exist_ok = True)

    return open(outfile, 'w', encoding='utf-8', newline='\n')



def copy_premade_files(args: argparse.Namespace) -> None:
    '''Copy the premade files from the premade src directory to their appropriate destinations.

    This contains a hardcoded list of files and directories to copy, so you will need to update this
    function if you change what is in the 'premade' subdirectory.
    '''
    our_path = Path(os.path.abspath(os.path.dirname(__file__)))
    premade_src = our_path / 'premade'
    premade_dst = args.output_dir

    file_paths: dict[Path, Path] = {
        premade_src / 'apache_license.txt': premade_dst / 'LICENSE',
        premade_src / 'arm_legacy/': premade_dst / 'arm' / 'include' / 'arm_legacy/'
    }

    for src, dst in file_paths.items():
        if src.is_dir():
            shutil.copytree(src, dst, dirs_exist_ok = True)
        else:
            shutil.copy(src, dst)


def get_command_line_arguments() -> argparse.Namespace:
    '''Return a object containing command line arugments for this app.

    If an error occurs or a command line arugment requests help text or version info, then this will
    exit the program after printing the appropriate info instead of returning.
    '''
    epilog_str: str = 'The files are put into a "pic32-device-files" subdirectory of the output directory.'

    version_str = 'PIC32 Device File Maker ' + version.FILE_MAKER_VERSION
    version_str += f' ({strings.get_this_git_repo_location()})'

    parser = argparse.ArgumentParser(
                            description='Creates device-specific files to support PIC32 devices',
                            epilog=epilog_str,
                            formatter_class=argparse.RawDescriptionHelpFormatter)

    # The '-h, --help" options are automatically added. The 'version' action on the '--version'
    # option is special and will exit after printing the version string.
    parser.add_argument('packs_dir', type=Path,
                        help='path to the packs directory containing Microchip device info')
    parser.add_argument('--define-macro', '-D', action='append', metavar='MACRO',
                        help='define a macro to be included in device configuration files')
    parser.add_argument('--output-dir', type=Path, default=Path(os.getcwd()), metavar='DIR',
                        help='where to put the created device files (default is current working dir)')
    parser.add_argument('--parse-jobs', type=int, default=0, metavar='JOBS',
                        help='how many processes to use for parsing device files (default is one per CPU)')
    parser.add_argument('--version', action='version',
                        version=version_str)

    # The command-line arguments added above will be a part of the returned object as member
    # variables. For example, 'args.output_dir' holds the argument for '--output_dir'.
    return parser.parse_args()


if '__main__' == __name__:
    args = get_command_line_arguments()

    # Put our output in a subdirectory specific to this script. This should prevent someone from
    # accidentally blowing away their home directory by making that their output directory.
    args.output_dir = args.output_dir / 'pic32-device-files'

    if os.path.exists(args.output_dir):
        shutil.rmtree(args.output_dir)

    lib_proc_prefix = args.output_dir / 'arm' / 'proc'
    include_proc_prefix = args.output_dir / 'arm' / 'include' / 'proc'

    peripheral_header_pathname = 'periph'
    fuses_header_pathname = 'fuses'

    peripherals_to_make: dict[str, PeripheralGroup] = {}
    device_families: dict[str, list[str]] = {}

    atdf_paths = get_atdf_paths_from_dir(args.packs_dir)
    devinfo_list = get_device_infos_from_atdf_paths(atdf_paths, args.parse_jobs)

    # Make the files specific to each device and collect their perpiherals so we can make
    # those later. 
    for devinfo in devinfo_list:
        if not (devinfo.cpu.startswith('cortex')  or  devinfo.cpu.startswith('arm')):
            continue

        print(f'Creating files for device {devinfo.name} ({devinfo.cpu})')

        # Linker script
        #
        if devinfo.cpu.startswith('cortex-m'):
            ld_path = lib_proc_prefix / devinfo.name.lower() / 'default.ld'
            with open_for_writing(ld_path) as ld:
                arm_mcu_linker_script_maker.run(devinfo, ld)

        # C device-specifc header file
        #
        dev_header_path = include_proc_prefix / (devinfo.name.lower() + '.h')
        with open_for_writing(dev_header_path) as hdr:
            arm_c_device_header_maker.run(devinfo, hdr, peripheral_header_pathname, 
                                              fuses_header_pathname)

        # Make a dict of peripherals we need to make. Doing this ensures we make each unique
        # peripheral only once. We do not need to make core peripherals because they are already
        # defined in CMSIS headers.
        #
        # Device fuses are a special peripheral, so look for those and handle them here. Assume
        # each device has at most one fuse peripheral called FUSES for now. You can find the special
        # handling this app does for fuses by searching for 'fuses' with the single quotes.
        #
        for periph in devinfo.peripherals:
            if 'fuses' == periph.name.lower():
                fuses_header_path = (include_proc_prefix / fuses_header_pathname / (devinfo.name.lower() + '.h'))
                with open_for_writing(fuses_header_path) as hdr:
                    basename = devinfo.name.lower() + '_fuses'
                    arm_c_periph_header_maker.run(basename, periph, hdr)
            elif periph.id  and  'system_ip' not in periph.id.lower():
                name = periph.name.lower()
                id = periph.id.lower()
                ver = periph.version.lower().replace(' ', '_')

                if ver:
                    full_name = f'{name}_{id}_{ver}'
                else:
                    full_name = f'{name}_{id}'

                if full_name not in peripherals_to_make:
                    peripherals_to_make[full_name] = periph

        # C device startup file
        #
        if devinfo.cpu.startswith('cortex-m'):
            startup_src_path = lib_proc_prefix / devinfo.name.lower() / 'startup.c'
            with open_for_writing(startup_src_path) as vec:
                proc_header_name = 'which_pic32.h'
                arm_mcu_c_startup_maker.run(proc_header_name, devinfo.interrupts, vec)

        # Clang configuration file
        #
        config_path = args.output_dir / 'config' / (devinfo.name.lower() + '.cfg')
        with open_for_writing(config_path) as cfg:
            default_ld_path = Path(os.path.relpath(ld_path, config_path.parent))
            arm_config_file_maker.run(devinfo, cfg, default_ld_path, args.define_macro)

        # Gather device names and families we can use to make an all-encompassing processor header
        # file. That is, instead of including the individual processor header in your project, you
        # can be lazy and include this one to let it figure out what processor you have. Family
        # names for "PIC32" devices are not always consistent, so use the first portion of the name
        # instead, like "PIC32CM" or "PIC32CZ". The specialty devices (CEC__, MEC__, etc.) are not
        # consistent with their family names, so just lump them all together.
        #
        family = devinfo.family.upper()
        if family.startswith('PIC32'):
            family = devinfo.name[:7].upper()
        elif not family.startswith('SAM'):
            family = '_'

        if family in device_families:
            device_families[family].append(devinfo.name)
        else:
            device_families[family] = [devinfo.name]

    # End for-loop

    # Make all of the peripheral implementation C headers. These are shared among various devices.
    #
    for periph_name, periph_group in peripherals_to_make.items():
        print(f'Creating peripheral header for {periph_name}')

        periph_header_path = include_proc_prefix / peripheral_header_pathname / (periph_name + '.h')
        with open_for_writing(periph_header_path) as hdr:
            arm_c_periph_header_maker.run(periph_name, periph_group, hdr)

    # Make the all-encompassing processor header file.
    #
    print('Creating big processor header')
    big_proc_header_path = args.output_dir / 'arm' / 'include' / 'which_pic32.h'
    with open_for_writing(big_proc_header_path) as hdr:
        all_devices_header_maker.run(hdr, big_proc_header_path.stem, device_families)

    # Copy the premade files to their proper destinations.
    #
    print(f'Copying premade files')
    copy_premade_files(args)

    exit(0)

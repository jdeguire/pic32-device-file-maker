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
from file_makers import *
import os
from pathlib import Path
import shutil
import tkinter
import tkinter.filedialog


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
            if '.atdf' == p.suffix:
                atdf_paths.append(p)

    return atdf_paths

def remake_dirs(dir):
    '''Remove and make the given directory and its subdirectories.
    
    Use this to remove build directories so that a clean build is done.'''
    if os.path.exists(dir):
        shutil.rmtree(dir)

    os.makedirs(dir)


if '__main__' == __name__:
# TODO: Should I move DeviceInfo into the file_makers module?
# TODO: Remove this hardcoded path when I'm doing testing.
#    packs_dir = get_dir_from_dialog(title='Open packs directory')
    packs_dir = '/home/jesse/projects/packs'
    if not packs_dir:
        exit(0)

    print(f'Got file path {packs_dir}')
    print('-----')

    our_path = Path(os.path.abspath(os.path.dirname(__file__)))
    output_path = our_path / 'pic32-device-files'
    remake_dirs(output_path)

    atdf_paths = get_atdf_paths_from_dir(packs_dir)
    for p in atdf_paths:
        atdf = AtdfReader(p)

# TODO: This is hardcoded to the PIC32CZ CA80 for now. Enable this for other stuff later.
#        if atdf.get_device_arch().startswith('cortex-m'):
        if atdf.get_device_name() == 'PIC32CZ8110CA80208'  or  atdf.get_device_name() == 'ATSAME54P20A':
            print(f'Creating files for device {atdf.get_device_name()} ({atdf.get_device_arch()})')

            devinfo = atdf.get_all_device_info()

            # Linker script
            #
            ld_path = output_path / 'lib' / 'cortex-m' / 'proc'
            ld_name = devinfo.name.lower() + '.ld'
            ld_loc = ld_path / ld_name

            os.makedirs(ld_path, exist_ok = True)

            with open(ld_loc, 'w', encoding='utf-8', newline='\n') as ld:
                cortexm_linker_script_maker.run(devinfo, ld)

            # C device-specifc header file
            #
            dev_header_path = output_path / 'include' / 'cortex-m' / 'proc'
            dev_header_name = devinfo.name.lower() + '.h'
            dev_header_loc = dev_header_path / dev_header_name

            os.makedirs(dev_header_path, exist_ok = True)

            with open(dev_header_loc, 'w', encoding='utf-8', newline='\n') as hdr:
                cortexm_c_device_header_maker.run(devinfo, hdr)


            # TODO: Remove this escape hatch later. This is here to exit a little more quickly while testing.
            if atdf.get_device_name() == 'ATSAME54P20A':
                break
        # else:
        #     print(f'Device {atdf.get_device_name()} has unsupported arch {atdf.get_device_arch()}')

    exit(0)

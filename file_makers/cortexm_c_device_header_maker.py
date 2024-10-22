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
import textwrap
from typing import IO


def run(devinfo: DeviceInfo, outfile: IO[str]) -> None:
    '''Make a C header file for the given device assuming is a a PIC or SAM Cortex-M device.
    '''
    outfile.write(_get_file_prologue(devinfo.name))


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

    # extern "C"
    prologue += '#ifdef __cplusplus\n'
    prologue += 'extern "c" {\n'
    prologue += '#endif\n\n'

    return prologue

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
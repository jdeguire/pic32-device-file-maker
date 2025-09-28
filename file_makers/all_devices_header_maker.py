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

'''all_devices_header_maker.py

Contains a single public function to make a C header file encompassing all in a list of devices. 
Instead of having to include the specific device header file in a module, a user can simply include
this all-encompassing file. This will contain lots of macro checks to determine which device-specific
header should be included.
'''

from . import strings
from typing import IO


def run(hdr: IO[str], basename: str, device_families: dict[str, list[str]]) -> None:
    '''Make a big header file that encompasses all of the devices in the given dictionary.

    The inputs are the file-like object to which the data will be written, the base
    name of the file without path or extension, and a dict of device families to lists of devices.
    ''' 
    # Write the header block with copyright info.
    hdr.write('/*\n')
    hdr.write(strings.get_generated_by_string(' * '))
    hdr.write(' * \n')
    hdr.write(strings.get_cmsis_license(' * '))
    hdr.write(' */\n\n')

    # Include guard
    hdr.write(f'#ifndef {basename.upper()}_H_\n')
    hdr.write(f'#define {basename.upper()}_H_\n\n')

    first_family = True
    for family, devices in device_families.items():
        # This is a special "catch-all" family, so handle this afterward.
        if '_' == family:
            continue

        if first_family:
            hdr.write(f'#if defined(__{family})\n')
        else:
            hdr.write(f'#elif defined(__{family})\n')
        
        first_family = False

        first_dev = True
        for d in devices:
            if first_dev: 
                hdr.write(f'#  if defined(__{d.upper()}__)\n')
            else:
                hdr.write(f'#  elif defined(__{d.upper()}__)\n')
            
            first_dev = False

            hdr.write(f'#    include "proc/{d.lower()}.h"\n')
        
        hdr.write('#  else\n')
        hdr.write(f'#    error Unknown device for {family} family!\n')
        hdr.write('#  endif\n')

    # Handle specialty devices like the CEC, MEC, and so on, series. These are not consistent in
    # their family naming, so we lump them together.
    for device in device_families['_']:
        hdr.write(f'#elif defined(__{device.upper()}__)\n')
        hdr.write(f'#  include "proc/{device.lower()}.h"\n')

    hdr.write('#else\n')
    hdr.write('#  error Unknown device or family!\n')
    hdr.write('#endif\n')

    hdr.write(f'\n#endif /* ifndef {basename.upper()}_H_ */\n')

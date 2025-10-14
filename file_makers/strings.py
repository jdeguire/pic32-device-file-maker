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

'''file_makers/strings.py

This file contains miscellaneous strings that will be common to many files made by this
application, such as copyright strings.
'''

from . import version
import datetime

# If you edit this project, be sure to add your copyright here too so that it appears in the created
# files. I followed this on Stack Exchange to figure out how I should add my name to an Apache
# License, so I presume you would do something simiar: 
# https://opensource.stackexchange.com/questions/9199/how-to-label-and-license-derivative-works-made-under-apache-license-version-2-0
#
# Basically, just add "Copyright (c) <year>, <your name>" on a new line at the end of the list.
#
_this_copyright: list[str] = [
    f'Copyright (c) {datetime.date.today().year}, Jesse DeGuire',
]

_this_git_location: str = 'https://github.com/jdeguire/pic32-device-file-maker'

_apache_license: list[str] = [
    'SPDX-License-Identifier: Apache-2.0',
    '',
    'Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file', 
    'except in compliance with the License. You may obtain a copy of the License at',
    '',
    'http://www.apache.org/licenses/LICENSE-2.0',
    '',
    'Unless required by applicable law or agreed to in writing, software distributed under the',
    'License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,',
    'either express or implied. See the License for the specific language governing permissions',
    'and limitations under the License'
]

_mchp_bsd_license: list[str] = [
    'Copyright (c) 2025, Microchip Technology Inc. and its subsidiaries ("Microchip")',
    'All rights reserved.',
    '',
    'This software is developed by Microchip Technology Inc. and its subsidiaries ("Microchip").',
    '',
    'Redistribution and use in source and binary forms, with or without modification, are',
    'permitted provided that the following conditions are met:',
    '',
    '1.  Redistributions of source code must retain the above copyright notice, this list of',
    '    conditions and the following disclaimer.',
    '2.  Redistributions in binary form must reproduce the above copyright notice, this list of',
    '    conditions and the following disclaimer in the documentation and/or other materials',
    '    provided with the distribution.',
    '3.  Microchip\'s name may not be used to endorse or promote products derived from this',
    '    software without specific prior written permission.',
    '',
    'THIS SOFTWARE IS PROVIDED BY MICROCHIP "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING,',
    'BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR PURPOSE ARE',
    'DISCLAIMED. IN NO EVENT SHALL MICROCHIP BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,',
    'EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING BUT NOT LIMITED TO PROCUREMENT OF SUBSTITUTE',
    'GOODS OR SERVICES; LOSS OF USE, DATA OR PROFITS; OR BUSINESS INTERRUPTION) HOWSOEVER CAUSED AND',
    'ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE',
    'OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE',
    'POSSIBILITY OF SUCH DAMAGE.'
]

_arm_cmsis6_copyright: str = 'Copyright (c) 2009-2023 Arm Limited. All rights reserved.'
_mchp_xc32_copyright: str = 'Copyright (c) 2025 Microchip Technology Inc. and its subsidiaries.'

_arm_cmsis6_adapted_from: str = \
    'Copied and adapted from code in Arm CMSIS 6 (https://github.com/ARM-software/CMSIS_6).'
_mchp_xc32_adapted_from: str = \
    'Portions were adapted from device code provided by the Microchip MPLAB(R) XC32 toolchain.'


COPYRIGHT_DEFAULT = 0
COPYRIGHT_CMSIS = 1
COPYRIGHT_MCHP = 2


def get_cmsis_license(comment_prefix: str, extra_copyrights: int = COPYRIGHT_DEFAULT) -> str:
    '''Return a string containing an Apache license that includes copyright info for Arm's CMSIS in
    addition to copyright info for this project.

    The argument is a string that will be prepended to every line of the output so that it is output
    as a comment in whatever language you are using. For example, you would use '// ' for C and C++.
    There is an additional option to also include Microchip copyright info. Use this when basing
    code on CMSIS and Microchip Apache licensed stuff.
    '''
    output: str = ''
    
    if extra_copyrights & COPYRIGHT_CMSIS:
        output += comment_prefix + _arm_cmsis6_copyright + '\n'

    if extra_copyrights & COPYRIGHT_MCHP:
        output += comment_prefix + _mchp_xc32_copyright + '\n'

    for line in _this_copyright:
        output += comment_prefix + line + '\n'

    output += comment_prefix + '\n'

    for line in _apache_license:
        output += comment_prefix + line + '\n'
    
    if extra_copyrights:
        output += comment_prefix + '\n'

    if extra_copyrights & COPYRIGHT_CMSIS:
        output += comment_prefix + _arm_cmsis6_adapted_from + '\n'

    if extra_copyrights & COPYRIGHT_MCHP:
        output += comment_prefix + _mchp_xc32_adapted_from + '\n'

    return output


def get_mchp_bsd_license(comment_prefix: str) -> str:
    '''Return a string containing a 3-clause BSD license that includes Microchip copyright info.

    The argument is a string that will be prepended to every line of the output so that it is output
    as a comment in whatever language you are using. For example, you would use '// ' for C and C++.
    '''
    output: str = comment_prefix + _mchp_xc32_adapted_from + '\n\n'

    for line in _mchp_bsd_license:
        output += comment_prefix + line + '\n'

    return output


def get_generated_by_string(comment_prefix: str) -> str:
    '''Return a string indicating the file was generated by this application with an optional date
    of generation.
    '''
    output: str = comment_prefix + 'Generated by pic32-device-file-maker '
    output += version.FILE_MAKER_VERSION
    
    output += '\n' + comment_prefix + '(' + _this_git_location + ')\n'

    return output


def get_this_git_repo_location() -> str:
    return _this_git_location

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

from datetime import date

# If you edit this project, be sure to add your copyright here too so that it appears in the created
# files. I followed this on Stack Exchange to figure out how I should add my name to an Apache
# License, so I presume you would do something simiar: 
# https://opensource.stackexchange.com/questions/9199/how-to-label-and-license-derivative-works-made-under-apache-license-version-2-0
#
# Basically, just add "Copyright (c) <year>, <your name>" on a new line at the end of the list.
#
_this_copyright: list[str] = [
    'Copyright (c) 2024, Jesse DeGuire',
]

_this_git_location: str = 'https://github.com/jdeguire/pic32-device-file-maker'

_this_version: str = 'v0.01'


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

_arm_cmsis6_copyright: str = 'Copyright (c) 2009-2023 Arm Limited. All rights reserved.'

_arm_cmsis6_adapted_from: str = \
    'Copied and adapted from code in Arm CMSIS 6 (https://github.com/ARM-software/CMSIS_6).'



def get_cmsis_apache_license(comment_prefix: str) -> str:
    '''Return a string containing an Apache license and other copyright info for Arm's CMSIS.

    The argument is a string that will be prepended to every line of the output so that it is output
    as a comment in whatever language you are using. For example, you would use '// ' for C and C++.
    '''
    output: str = comment_prefix + _arm_cmsis6_copyright + '\n'

    for line in _this_copyright:
        output += comment_prefix + line + '\n'

    output += comment_prefix + '\n'

    for line in _apache_license:
        output += comment_prefix + line + '\n'
    
    output += comment_prefix + '\n'

    output += comment_prefix + _arm_cmsis6_adapted_from + '\n'

    return output

def get_generated_by_string(comment_prefix: str, include_date: bool = False) -> str:
    '''Return a string indicating the file was generated by this application with an optional date
    of generation.
    '''
    output: str = comment_prefix + 'Generated by pic32-device-file-maker ' + _this_version

    if include_date:
        output += ' on ' + date.today().isoformat()
    
    output += '\n' + comment_prefix + '(' + _this_git_location + ')\n'

    return output
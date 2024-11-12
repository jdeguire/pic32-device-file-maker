#! /usr/bin/env python3
#
# I guess this needs to be here to make this directory a package.
# This needs to be a package so I can do relative imports bewteen files in there, I think.
# This is new to me, so I'm figuring this out as I go along. Wheeeee!
# This project is also a way to for me to learn more Python, so this is good to learn!
#
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

# If you want to do "from <package> import *", then you have to define __all__ in this file to
# tell Python what modules you want it to grab. This is handy for ensuring that private files and
# __init__.py are not imported.
#
# One could use some code here to grab whatever is in this package directory, but for now there is
# no harm in just explicity naming the modules. Notice that the ".py" extension is NOT included.

from . import cortexm_c_device_header_maker
from . import cortexm_c_periph_header_maker
from . import cortexm_c_vectors_maker
from . import cortexm_config_file_maker
from . import cortexm_linker_script_maker
from . import strings
from . import version

__all__ = [
    'cortexm_c_device_header_maker',
    'cortexm_c_periph_header_maker',
    'cortexm_c_vectors_maker',
    'cortexm_config_file_maker',
    'cortexm_linker_script_maker',
    'strings',
    'version'
]

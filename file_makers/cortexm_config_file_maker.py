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

'''cortexm_config_file_maker.py

Contains a single public function to make a target configuration file for a single Arm Cortex-M
device. A configuration file would be passed to Clang using the "-config=" option to provide it the
options needed for the desired target.
'''

from device_info import *
import os
from . import strings
import textwrap
from typing import IO


_FPU_NONE = 0
_FPU_SP = 1
_FPU_DP = 2

_L1CACHE_NONE = 0
_L1CACHE_DATA = 1
_L1CACHE_INST = 2


def run(devinfo: DeviceInfo, outfile: IO[str], default_ld_path: str) -> None:
    '''Make a Clang target configuration file for the given device assuming it is a PIC or SAM
    Cortex-M device.
    '''
    outfile.write(_get_file_prologue())
    outfile.write(_get_common_options())
    outfile.write('\n# Base target arch options.\n')
    outfile.write(_get_target_arch_options(devinfo))
    outfile.write('\n')

    outfile.write('# Point to device-specific lib directory.\n')
    outfile.write('# This is where the vectors code is located.\n')
    outfile.write(f'-L <CFGDIR>/{os.path.dirname(default_ld_path)}\n\n')

    outfile.write('# Set default linker script.\n')
    outfile.write('# This is used only if -T is not specified at link time.\n')
    outfile.write(f'-Wl,--default-script=<CFGDIR>/{default_ld_path}\n\n')

    outfile.write('# Useful target-specific macros.\n')
    macros = _get_target_macros(devinfo)
    for macro,value in macros.items():
        if value:
            outfile.write(f'-D{macro}={value}\n')
        else:
            outfile.write(f'-D{macro}\n')

    # This file does not have an epilogue.


def _get_file_prologue() -> str:
    '''Return a string with the file prologue, which contains the license info and a reference to
    this project.
    '''
    prologue: str = ''

    # Write the header block with copyright info.
    prologue += strings.get_generated_by_string('# ')
    prologue += '# \n'
    prologue += strings.get_non_cmsis_apache_license('# ')
    prologue += '# \n'

    return prologue

def _get_common_options() -> str:
    '''Return a string with options common to all Cortex-M devices, such as sysroot and include
    directories.
    '''
    return textwrap.dedent('''
        # The compiler is built with the build option CLANG_CONFIG_FILE_SYSTEM_DIR to tell Clang
        # where to look by default for these config files.
        # Clang supports "multilibs" to link against different libraries based on compiler options.
        # The options here are matched to the ones in "multilib.yaml" in the sysroot to determine
        # which multilib variant to link against.

        # Specify a sysroot so hopefully Clang will look only in its install location rather than
        # trying to find headers and stuff in actual system directories. This is also where
        # "multilib.yaml" is located.
        --sysroot=<CFGDIR>/../cortex-m

        # Specify system include directories
        -isystem <CFGDIR>/../cortex-m/CMSIS/Core/Include
        -isystem <CFGDIR>/../cortex-m/include

        # Ensure we are using the linker and runtimes bundled with this toolchain. Clang can try to
        # use the system runtime and linker, which we do not want.
        -rtlib=compiler-rt
        -fuse-ld=lld
        ''')


def _get_target_arch_options(devinfo: DeviceInfo) -> str:
    '''Return a string containing the options specifying the target and its architecture.
    '''
    arch_name: str = _get_arch_from_cpu_name(devinfo.cpu)
    fpu_width: int = _get_fpu_width(devinfo)
    fpu_name: str = _get_fpu_name(arch_name, fpu_width)
    mve_ext: str = _get_mve_support(arch_name, fpu_width)

    target_str: str = '-target arm-none-eabi\n'

    arch_str = f'-march={arch_name}'
    if mve_ext:
        arch_str += f'+{mve_ext}'
    arch_str += '\n'

    fpu_str: str = f'-mfpu={fpu_name}\n'

    # MVE uses the FPU registers, so that needs the hard float ABI even if normal FPU instructions
    # are not present.
    abi_str: str = ''
    if 'none' == fpu_name  and  not mve_ext:
        abi_str = '-mfloat-abi=soft\n'
    else:
        abi_str = '-mfloat-abi=hard\n'

    cmse_str: str = ''
    if _has_cmse_extension(arch_name):
        cmse_str = '-mcmse\n'

    return target_str + arch_str + fpu_str + abi_str + cmse_str


def _get_target_macros(devinfo: DeviceInfo) -> dict[str, str]:
    '''Return a set of target-specific macros that would be useful to reference in C and C++
    code for the devices.

    These include macros for the device name, series, architecture, and so on. The key of the dict
    is the macro name and the value is the macro value. The value can be empty for macros with no
    explicit value.
    '''
    macros: dict[str, str] = {'__PIC32' : '',
                              '__PIC32__' : ''}

    name = devinfo.name.upper()
    series = devinfo.series.upper()
    family = devinfo.family.upper()
    macros[f'__{name}__'] = ''
    macros[f'__{name}'] = ''
    macros[f'__{series}__'] = ''
    macros[f'__{series}'] = ''
    macros[f'__{family}__'] = ''
    macros[f'__{family}'] = ''

    if name.startswith('SAM'):
        # Add the "ATSAM" variant of the name for compability. Our ATDF Reader pulls off the "AT"
        # because some devices use it and some don't.
        macros[f'__AT{name}__'] = ''
        macros[f'__AT{name}'] = ''
    elif name.startswith('PIC32'):
        # Add macros with "PIC32C" and "PIC32CX" in them, as an example. These might already be
        # covered by the family and series above, in which case these will effectively do nothing.
        macros[f'__{name[:6]}__'] = ''
        macros[f'__{name[:6]}'] = ''
        macros[f'__{name[:7]}__'] = ''
        macros[f'__{name[:7]}'] = ''

    l1cache = _get_target_l1cache(devinfo)
    if _L1CACHE_NONE != l1cache:
        macros[f'__PIC32_HAS_L1CACHE'] = ''

        if l1cache & _L1CACHE_DATA:
            macros[f'__PIC32_HAS_L1DCACHE'] = ''
        if l1cache & _L1CACHE_INST:
            macros[f'__PIC32_HAS_L1ICACHE'] = ''
    
    fpu_width = _get_fpu_width(devinfo)
    if _FPU_DP & fpu_width:
        macros[f'__PIC32_HAS_FPU64'] = ''
    if _FPU_SP & fpu_width:
        macros[f'__PIC32_HAS_FPU32'] = ''

    macros['__PIC32_DEVICE_NAME'] = '"' + name + '"'
    macros['__PIC32_DEVICE_NAME__'] = '"' + name + '"'

    macros['__PIC32_PIN_COUNT'] = str(devinfo.pincount)
    macros['__PIC32_PIN_COUNT__'] = str(devinfo.pincount)

    cpu_name = devinfo.cpu
    arch = _get_arch_from_cpu_name(cpu_name)
    fpu_name = _get_fpu_name(arch, fpu_width)
    macros['__PIC32_CPU_NAME'] = '"' + cpu_name + '"'
    macros['__PIC32_CPU_NAME__'] = '"' + cpu_name + '"'
    macros['__PIC32_FPU_NAME'] = '"' + fpu_name + '"'
    macros['__PIC32_FPU_NAME__'] = '"' + fpu_name + '"'
    macros['__PIC32_ARCH'] = '"' + arch + '"'
    macros['__PIC32_ARCH__'] = '"' + arch + '"'

    return macros


def _get_arch_from_cpu_name(cpuname: str) -> str:
    '''Get the Arm ISA version, such as "armv7em", from its CPU name, such as "cortex-m7".
    '''
    # Presume the "cortex-" part is there and remove it to make the matching a bit easier to read.
    cpu = cpuname.lower().split('-', 1)[1]

    match cpu:
        case 'm0' | 'm0plus' | 'm1':
            return 'armv6m'
        case 'm3':
            return 'armv7m'
        case 'm4' | 'm7':
            return 'armv7em'
        case 'm23':
            return 'armv8m.base'
        case 'm33' | 'm35' | 'm35p':
            return 'armv8m.main'
        case 'm52' | 'm55' | 'm85':
            return 'armv8.1m.main'
        case _:
            raise ValueError(f'Unknown CPU name {cpuname}!') 


def _get_fpu_name(arch: str, fpu_width: int) -> str:
    '''Return the FPU extension name to be passed to the compiler or "none" if the device
    does not support an FPU.
    '''
    if _FPU_NONE == fpu_width:
        return 'none'

    match arch:
        case 'armv7em':
            if _FPU_DP & fpu_width:
                return 'fpv5-d16'
            else:
                return 'fpv4-sp-d16'
        case 'armv8m.main':
            if _FPU_DP & fpu_width:
                raise ValueError(f'Arch {arch} unexpectedly has a double-precision FPU!')
            else:
                return 'fpv5-sp-d16'
        case 'armv8.1m.main':
            if _FPU_DP & fpu_width:
                return 'fp-armv8-fullfp16-d16'
            else:
                raise ValueError(f'Arch {arch} unexpectedly has a single-precision FPU!')
        case _:
            raise ValueError(f'Arch {arch} unexpectedly has an FPU!')


def _get_mve_support(arch: str, fpu_width: int) -> str:
    '''Return the MVE (M-Profile Vector Extensions) name to be passed to the compiler or an empty
    string if the device dose not support MVE.
    '''
    mve: str = ''

    # The first ISA to support MVE is ARMv8.1-M.main. Assume that further point releases, like v8.2,
    # will also support it in the main profile
    if 'armv8.' in arch  and  'main' in arch:
        if _FPU_DP & fpu_width:
            mve = 'mve.fp+fp.dp'
        elif _FPU_SP & fpu_width:
            mve = 'mve.fp'
        else:
            mve = 'mve'

    return mve


def _has_cmse_extension(arch: str) -> bool:
    '''Return True if the device supports the Cortex-M Security Extensions.
    '''
    return 'armv8' in arch


def _get_fpu_width(devinfo: DeviceInfo) -> int:
    '''Return a value to indicate the width of the types supported by the device's FPU.

    This returns one of the _FPU_xxx values at the top of this file. The return value can be
    bitwise-ANDed with those value to check for support for different widths.
    '''
    width: int = _FPU_NONE

    for param in devinfo.parameters:
        if '__FPU_PRESENT' == param.name  and  0 != int(param.value):
            width |= _FPU_SP
        elif '__FPU_DP' == param.name  and  0 != int(param.value):
            width |= _FPU_DP

    return width


def _get_target_l1cache(devinfo: DeviceInfo) -> int:
    '''Return a value indicating if the target has an L1 cache and what type if is.

    This returns one of the _L1CACHE_xxx values at the top of this file. The return value can be
    bitwise-ANDed with those value to check for the presence of the different L1 caches.
    '''
    cache_type: int = _L1CACHE_NONE

    for param in devinfo.parameters:
        if '__DCACHE_PRESENT' == param.name  and  0 != int(param.value):
            cache_type |= _L1CACHE_DATA
        elif '__ICACHE_PRESENT' == param.name  and  0 != int(param.value):
            cache_type |= _L1CACHE_INST

    return cache_type

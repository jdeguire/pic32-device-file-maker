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

from pathlib import Path
from device_info import *
from . import strings
import textwrap
from typing import IO


_FPU_NONE = 0
_FPU_SP = 1
_FPU_DP = 2

_L1CACHE_NONE = 0
_L1CACHE_DATA = 1
_L1CACHE_INST = 2


def run(devinfo: DeviceInfo, outfile: IO[str], default_ld_path: Path, extra_macros: list[str]) -> None:
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
    outfile.write(f'-L "<CFGDIR>/{default_ld_path.parent.as_posix()}"\n\n')

    outfile.write(f'# Tell Clang to look in the device-specifc directory for some files.\n')
    outfile.write(f'# In particular, we put crt0.o in here since that is device-speciifc.\n')
    outfile.write(f'-B "<CFGDIR>/{default_ld_path.parent.as_posix()}"\n\n')

    outfile.write('# Set default linker script.\n')
    outfile.write('# This is used only if -T is not specified at link time.\n')
    outfile.write(f'-Wl,--default-script="<CFGDIR>/{default_ld_path.as_posix()}"\n\n')

    outfile.write('# Useful target-specific macros.\n')
    macros = _get_target_macros(devinfo)
    for macro,value in macros.items():
        if value:
            outfile.write(f'-D{macro}={value}\n')
        else:
            outfile.write(f'-D{macro}\n')

    # Any extra macros provided need to be in the format expected by Clang's '-D' option.
    if extra_macros:
        outfile.write('\n# Additional macros.\n')
        for macro in extra_macros:
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
        --sysroot="<CFGDIR>/../cortex-m"

        # Specify system include directories. The C++ includes need to be specified first beucase
        # they use #include_next to redirect to the C headers as needed. The C++ headers check
        # for __cplusplus to be defined and so this should be fine for C-only projects.
        -isystem "<CFGDIR>/../cortex-m/include/c++/v1"
        -isystem "<CFGDIR>/../cortex-m/include"
        -isystem "<CFGDIR>/../CMSIS/Core/Include"

        # Ensure we are using the linker and runtimes bundled with this toolchain. Clang can try to
        # use the system runtime and linker, which we do not want. libc++ is statically linked
        # against libc++abi because there is no option like these to specify that.
        -rtlib=compiler-rt
        -fuse-ld=lld
        -stdlib=libc++
        -unwindlib=libunwind
        ''')


def _get_target_arch_options(devinfo: DeviceInfo) -> str:
    '''Return a string containing the options specifying the target and its architecture.
    '''
    cpu_name: str = devinfo.cpu
    arch_name: str = _get_arch_from_cpu_name(cpu_name)
    fpu_width: int = _get_fpu_width(devinfo)
    fpu_name: str = _get_fpu_name(cpu_name, fpu_width)
    mve_ext: str = _get_mve_support(arch_name, fpu_width)

    target_str: str = '-target arm-none-eabi\n'

    arch_str = f'-march={arch_name}{mve_ext}'
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
        # Add macros that omit the "PIC" part. This keeps some compatibility with XC32.
        macros[f'__{name[3:]}__'] = ''
        macros[f'__{name[3:]}'] = ''

    fpu_width = _get_fpu_width(devinfo)
    cpu_name = devinfo.cpu
    arch = _get_arch_from_cpu_name(cpu_name)
    fpu_name = _get_fpu_name(cpu_name, fpu_width)

    macros['__PIC32_DEVICE_NAME'] = '"' + name + '"'
    macros['__PIC32_DEVICE_NAME__'] = '"' + name + '"'

    macros['__PIC32_PIN_COUNT'] = str(devinfo.pincount)
    macros['__PIC32_PIN_COUNT__'] = str(devinfo.pincount)

    macros['__PIC32_CPU_NAME'] = '"' + cpu_name + '"'
    macros['__PIC32_CPU_NAME__'] = '"' + cpu_name + '"'
    macros['__PIC32_FPU_NAME'] = '"' + fpu_name + '"'
    macros['__PIC32_FPU_NAME__'] = '"' + fpu_name + '"'
    macros['__PIC32_ARCH'] = '"' + arch + '"'
    macros['__PIC32_ARCH__'] = '"' + arch + '"'

    l1cache = _get_target_l1cache(devinfo)
    if _L1CACHE_NONE != l1cache:
        macros['__PIC32_HAS_L1CACHE'] = ''

        if l1cache & _L1CACHE_DATA:
            macros['__PIC32_HAS_L1DCACHE'] = ''
        if l1cache & _L1CACHE_INST:
            macros['__PIC32_HAS_L1ICACHE'] = ''
    
    if _FPU_DP & fpu_width:
        macros['__PIC32_HAS_FPU64'] = ''
    if _FPU_SP & fpu_width:
        macros['__PIC32_HAS_FPU32'] = ''
    if 'fullfp16' in fpu_name:
        macros['__PIC32_HAS_FPU16'] = ''

    return macros


def _get_arch_from_cpu_name(cpu_name: str) -> str:
    '''Get the Arm ISA version, such as "armv7em", from its CPU name, such as "cortex-m7".
    '''
    # Presume the "cortex-" part is there and remove it to make the matching a bit easier to read.
    cpu = cpu_name.lower().split('-', 1)[1]

    # You can find the architecture name pretty easily by just looking up the CPU name online.
    # Wikipedia has a page for Cortex-M with tables to show the archicture. What gets passed to
    # the compiler is the architecture name without any dashes. For example, a Cortex-M7 will always
    # be Armv7E-M and so you'd pass "armv7em" to the compiler.
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
            raise ValueError(f'Unknown CPU name {cpu_name}!') 


def _get_fpu_name(cpu_name: str, fpu_width: int) -> str:
    '''Return the FPU extension name to be passed to the compiler or "none" if the device
    does not support an FPU.
    '''
    if _FPU_NONE == fpu_width:
        return 'none'

    # Presume the "cortex-" part is there and remove it to make the matching a bit easier to read.
    cpu = cpu_name.lower().split('-', 1)[1]

    # Finding the FPU name can be tricky. Your best bet is to find the "Cortex-M__ Technical Reference
    # Manual" and look up the FPU info in there. That will tell you if the FPU can support half-,
    # single-, or double-precision math and the FPU version (ex: "FPv5"). Some CPUs can optionally
    # choose from multiple FPU implementations. The Technical Reference Manual may also refer you
    # to an Architecture Reference Manual for more info.
    #
    # The best way I've found for seeing what you can pass to the compiler is to look in LLVM's source
    # code. The file "llvm/llvm/include/llvm/TargetParser/ARMTargetParser.def" has a list of FPU and
    # CPU names you can use to figure out the name of the FPU for your device.
    match cpu:
        case 'm4':
            if _FPU_DP & fpu_width:
                raise ValueError(f'CPU {cpu_name} unexpectedly has a double-precision FPU!')
            else:
                return 'fpv4-sp-d16'
        case 'm7':
            if _FPU_DP & fpu_width:
                return 'fpv5-d16'
            else:
                return 'fpv5-sp-d16'
        case 'm33' | 'm35' | 'm35p':
            if _FPU_DP & fpu_width:
                raise ValueError(f'CPU {cpu_name} unexpectedly has a double-precision FPU!')
            else:
                return 'fpv5-sp-d16'
        case 'm52' | 'm55' | 'm85':
            if _FPU_DP & fpu_width:
                return 'fp-armv8-fullfp16-d16'
            else:
                return 'fp-armv8-fullfp16-sp-d16'
        case _:
            raise ValueError(f'Arch {cpu_name} unexpectedly has an FPU!')


def _get_mve_support(arch: str, fpu_width: int) -> str:
    '''Return the MVE (M-Profile Vector Extensions) name to be passed to the compiler or an empty
    string if the device dose not support MVE.
    '''
    mve: str = ''

    # The first ISA to support MVE is ARMv8.1-M.main. Assume that further point releases, like v8.2,
    # will also support it in the main profile.
    # This is not a separate compiler flag, but rather this is appended to the architecture name.
    if 'armv8.' in arch  and  'main' in arch:
        if _FPU_DP & fpu_width:
            mve = '+mve.fp+fp.dp'
        elif _FPU_SP & fpu_width:
            mve = '+mve.fp'
        else:
            mve = '+mve'

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

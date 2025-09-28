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

'''arm_mcu_c_startup_maker.py

Contains a single public function to make a C file containing startup code and vector table
declarations for a single Arm Cortex-M device.
This is based on the sample startup code found in Arm CMSIS 6 at
https://github.com/ARM-software/CMSIS_6/blob/main/CMSIS/Core/Template/Device_M/Source/startup_Device.c.
'''

from device_info import *
from . import strings
import textwrap
from typing import IO


def run(proc_header_name: str, interrupts: list[DeviceInterrupt], outfile: IO[str]) -> None:
    '''Make a C vector definition file for the given device assuming it is a PIC or SAM Cortex-M
    device.

    The proc_header_name is the name of a header file this can include to get processor-specific
    info. This can be the processor-specifc header file or an all-encompassing header that will
    figure out which processor-specific header to use based on macros. This should include the
    extension but not the full path.
    '''
    outfile.write(_get_file_prologue(proc_header_name))
    outfile.write('\n')
    outfile.write(_get_default_handlers())
    outfile.write('\n\n')
    outfile.write(_get_handler_declarations(interrupts))
    outfile.write('\n\n')
    outfile.write(_get_vector_table(interrupts))
    outfile.write('\n\n')

    outfile.write(_get_startup_feature_functions())
    outfile.write(_get_data_init_functions())
    outfile.write(_get_llvm_libc_functions())
    outfile.write(_get_reset_handler())

    # This file does not have an epilogue.


def _get_file_prologue(proc_header_name: str) -> str:
    '''Return a string with the file prologue, which contains the license info, a reference to
    this project, and some other declarations.
    '''
    header: str = ''

    # Write the header block with copyright info.
    header += '/*\n'
    header += strings.get_generated_by_string(' * ')
    header += ' * \n'
    header += strings.get_cmsis_license(' * ', strings.COPYRIGHT_CMSIS | strings.COPYRIGHT_MCHP)
    header += ' */\n'

    decls: str = f'''
        #include <{proc_header_name}>
        #include <stdint.h>

        /* Vector table typedef */
        typedef void(*VECTOR_TABLE_Type)(void);

        /* These are provided by the device linker script.
           These names are aliases defined by CMSIS for the linker symbols. */
        extern uint32_t __INITIAL_SP;
        extern uint32_t __STACK_LIMIT;
        #if defined (__ARM_FEATURE_CMSE) && (__ARM_FEATURE_CMSE == 3U)
        extern uint32_t __STACK_SEAL;
        #endif

        extern void __libc_init_array(void);    // Defined in libc at llvm/libc/startup/baremetal/init.cpp
        extern int main(void);
        extern void exit(int status);

        /* Define these to run code during startup.  The _on_reset() function is run almost
           immediately, so the cache and FPU will not be usable unless they are enabled in
           _on_reset(). The _on_bootstrap() function is run just before main is called and so
           everything should be initialized.
           */
        extern void __attribute__((weak)) _on_reset(void);
        extern void __attribute__((weak)) _on_bootstrap(void);

        /* Define this to run code upon entering the default interrupt handler. Any interrupts you do
           not create handlers for call the default handler. Trying to define Default_Handler() yourself
           like with other interrupt or fault handlers does not seem to work, so define this function
           instead as a workaround. Return non-zero if the default interrupt handler should return.
           Otherwise, it will spin forever after this function returns.
           */
        extern int __attribute__((weak)) _on_default_handler(void);
        '''

    return header + textwrap.dedent(decls)


def _get_default_handlers() -> str:
    '''Return a string containing definitions for the default interrupt handler and the Hard Fault
    interrupt handler.
    '''
    handlers: str = '''
        /* ----- Default Handlers: Provide your own definitions to override these. ----- */
        // Default Hard Fault Handler
        void __attribute__((noreturn, weak)) HardFault_Handler(void)
        {
        #ifdef __DEBUG
            __BKPT(0);
        #endif
            while(1)
            {}
        }

        // Testing has shown that we need this indirect jump to Default_Handler() to allow users
        // to override Default_Handler(). It seems like a function that is aliased cannot be
        // overridden even if the aliased function is weak.
        void Default_Handler(void);
        void Default_Handler_Jump(void)
        {
            Default_Handler();
        }
        
        // Default Handler For Other Exceptions and Interrupts
        void __attribute__((noreturn, weak)) Default_Handler(void)
        {
        #ifdef __DEBUG
            __BKPT(0);
        #endif
            while(1)
            {}
        }

        // Default Handler For Reserved Interrupt Vectors
        void __attribute__((noreturn, weak)) Reserved_Handler(void)
        {
        #ifdef __DEBUG
            __BKPT(0);
        #endif
            while(1)
            {}
        }

        void __attribute((noreturn, section(".reset"))) Reset_Handler(void);
        '''

    return textwrap.dedent(handlers)


def _get_handler_declarations(interrupts: list[DeviceInterrupt]) -> str:
    '''Return a string containing weak declarations for the interrupt and exception handlers not
    already covered by _get_default_handlers().

    Most of these will be weak aliases of the Default_Handler(). The idea is that users will create
    their own definitions in their code, which will override these weak versions.
    '''
    decl_str: str = '/* ----- Exception and Interrupt Handlers ----- */\n'
    decl_str += '/* Provide your own definitions to override these. */\n'

    for intr in interrupts:
        # Skip these because we already defined them in _get_default_handlers().
        if 'HardFault' == intr.name  or  'Reset' == intr.name:
            continue

        func_str = f'{intr.name}_Handler'
        decl_str += f'void {func_str:<32}(void) __attribute__((weak, alias("Default_Handler_Jump")));\n'

    return decl_str


def _get_vector_table(interrupts: list[DeviceInterrupt]) -> str:
    '''Return a string containing the definition of the vector table for this device.

    The vector table is an array of function pointers, but the very first entry is the initial top
    of the stack to be loaded into the stack pointer register.
    '''
    intr_decls: list[str] = []
    intr_decls.append('    (VECTOR_TABLE_Type)&__INITIAL_SP,   /*     Initial Stack Pointer */')

    current_index = interrupts[0].index

    for intr in interrupts:
        # Fill in gaps with the reserved handler.
        while current_index < intr.index:
            intr_decls.append('    Reserved_Handler,                /*     Reserved */')
            current_index += 1
        
        entry = f'{intr.name}_Handler,'
        intr_decls.append(f'    {entry:<32} /* {intr.index :3} {intr.caption} */')

        current_index += 1

    # +1 for initial stack value.
    num_entries = current_index - interrupts[0].index + 1

    vec_table_decl =  f'extern const VECTOR_TABLE_Type __VECTOR_TABLE[{num_entries}];\n'
    vec_table_decl += f'       const VECTOR_TABLE_Type __VECTOR_TABLE[{num_entries}] '
    vec_table_decl +=  '__attribute__((used, retain, section(".vectors"))) = {\n'
    vec_table_decl += '\n'.join(intr_decls)
    vec_table_decl += '\n};'

    return vec_table_decl


def _get_startup_feature_functions() -> str:
    '''Return a string containing functions to enable device features like the FPU or cache at
    startup.
    '''
    funcs: str = '''
        /* Enable the FPU for devices that have one. This is also used for devices that support the 
           M-Profile Vector Extensions because that uses the 16 double-precision FPU registers as 8
           128-bit vector registers.
           */
        #if (defined(__ARM_FP) && (0 != __ARM_FP))  ||  (defined(__ARM_FEATURE_MVE) && (__ARM_FEATURE_MVE > 0))
        void __attribute__((weak, section(".reset.startup"))) _EnableFpu(void)
        {
            SCB->CPACR |= 0x00F00000;
            __DSB();
            __ISB();

            // Initialize the FPSCR register to clear out status info from before a warn reset.
            // If present, set FPSCR.LTPSIZE to 4. This relates to the Low Overhead Branch extension.
        #  if defined(FPU_FPDSCR_LTPSIZE_Msk)
            __set_FPSCR(0x040000);
        #  else
            __set_FPSCR(0);
        #  endif
        }
        #endif

        /* Enable the Cortex-M Cache Controller with default values. This is used to supplement
           Cortex-M devices that do not have a CPU cache.
           */
        #if defined(ID_CMCC)
        void __attribute__((weak, section(".reset.startup"))) _EnableCmccCache(void)
        {
            CMCC_REGS->CMCC_CTRL |= CMCC_CTRL_CEN_Msk;
        }
        #endif

        /* Enable the Cortex-M CPU instruction and data caches. This applies to CPUs with built-in
           caches.
           */
        #if __ICACHE_PRESENT == 1  ||  __DCACHE_PRESENT == 1
        void __attribute__((weak, section(".reset.startup"))) _EnableCpuCache(void)
        {
            // These invalidate the caches before enabling them.
        #if __ICACHE_PRESENT == 1
            SCB_EnableICache();
        #endif
        #if __DCACHE_PRESENT == 1
            SCB_EnableDCache();
        #endif
        }
        #endif

        /* Enable branch prediction and the Low Overhead Branch extension if either are present.
           */
        #if defined(SCB_CCR_LOB_Msk) || defined(SCB_CCR_BP_Msk)
        void __attribute__((weak, section(".reset.startup"))) _EnableBranchCaches(void)
        {
        #  if defined(SCB_CCR_LOB_Msk)
            /* Enable Loop and branch info cache */
            SCB->CCR |= SCB_CCR_LOB_Msk;
        #  endif
        #  if defined(SCB_CCR_BP_Msk)
            /* Enable Branch Prediction */
            SCB->CCR |= SCB_CCR_BP_Msk;
        #  endif
            __DSB();
            __ISB();
        }
        #endif
        '''

    return textwrap.dedent(funcs)

def _get_data_init_functions() -> str:
    '''Return a string containing functions used to initialize data sections and call C++ 
    constructors.
    '''
    funcs: str = '''
        /* Initialize data found in the .data, .tdata, .tbss, and .bss sections. The .tdata and 
           .tbss sections are for thread-local storage. Those are placed between .data and .bss so
           we can initialize the thread-local sections as though they were part of the .data and
           .bss sections. This is sufficient to let libraries declare members as thread-local in
           a single-threaded app.
           */
        void __attribute__((weak, section(".reset.startup"))) _InitData(void)
        {
            // These are defined in the linker script. These span the normal and thread-local
            // sections so they can be initialized as one.
            extern uint32_t __data_start;
            extern uint32_t __data_source;
            extern uint32_t __data_end;
            extern uint32_t __bss_start;
            extern uint32_t __bss_end;

            uint32_t *src = &__data_source;
            uint32_t *dst = &__data_start;
            while(dst < &__data_end)
            {
                *dst++ = *src++;
            }

            uint32_t *bss = &__bss_start;
            while(bss < &__bss_end)
            {
                *bss++ = 0;
            }
        }
        '''

    return textwrap.dedent(funcs)


def _get_llvm_libc_functions() -> str:
    '''Return a string containing functions that need to be defined because they are referenced
    by LLVM-libc.
    
    Yes, these should probably be in some support library rather than here in the startup module.
    Putting them here simplifies the build setup and gives users one file to modify if they want
    to make custom funcions. Since these are weak symbols, users should be able to override them
    with their own implementations if needed.
    '''
    funcs: str = '''
        /* These next two functions are called by LLVM-libc's exit() function. The first would
           normally run global and static local C++ object destructors and any functions registered
           with atexit(). The second would do any extra cleanup work needed by an application at
           exit. 
           
           A baremetal program will normally never exit like a regular software program would, so
           these do not normally need to do much.
           */
        void __attribute__((weak, section(".reset.libc"))) __cxa_finalize(void *dso)
        {
        }

        void __attribute__((noreturn, weak, section(".reset.libc"))) __llvm_libc_exit(int status)
        {
        #ifdef __DEBUG
            __BKPT(0);
        #endif

            /* Nothing left to do but spin here forever. */
            while(1) {}
        }

        /* Provide an errno variable used by LLVM-libc's math functions. This assumes that the
           baremetal app can use a single global errno value. Multithreaded apps might want to
           provide their own implementation that has thread-local errno values.
           */
        int * __attribute__((weak, section(".reset.libc"))) __llvm_libc_errno()
        {
            static int errno_impl;
            return &errno_impl;
        }

        /* Return a pointer to a thread control block. This is used only to access thread-local
           storage, so this default version will return a pointer with the offset to thread-local
           storage baked in. The ARM ABI specs say this should not clobber R1-R3, but here we're
           relying on the compiler to not mess with those. See this link for some good info:
           https://kb.segger.com/Thread-Local_Storage#No_OS_/_Single_Thread_System
           */
        void * __attribute__((weak, section(".reset.libc"))) __aeabi_read_tp(void)
        {
            // On 32-bit ARM, the thread storage pointer is 8 bytes into the thread control
            // block, so just subtract off 8. It's 16 bytes on AArch64.
            extern const uint8_t __tls_base;
            return (void *)&__tls_base - 8;
        }
        '''

    return textwrap.dedent(funcs)

def _get_reset_handler() -> str:
    '''Return a string containing the reset handler function for Cortex-M devices.
    '''
    reset: str = '''
        /* The entry point at which the CPU starts execution. The address of this function is in the
           vector table and the CPU fetches it upon power up or reset.
           */
        void __attribute((noreturn, section(".reset"))) Reset_Handler(void)
        {
            /* Initialize the stack pointers. MSP is initialized by the CPU on reset from the first entry
               in the vector table, but do it here in case this app was jumped-to from a bootloader. */
            __set_MSP((uint32_t)(&__INITIAL_SP));
            __set_PSP((uint32_t)(&__INITIAL_SP));

        #if (__ARM_ARCH >= 8)
            /* Initialize stack limit registers for Armv8-M Main devices. */
            __set_MSPLIM((uint32_t)(&__STACK_LIMIT));
            __set_PSPLIM((uint32_t)(&__STACK_LIMIT));
        #endif

            /* Add stack sealing for Armv8-M based processors. To use this, copy the default linker
               script for the target device. Update the __STACKSEAL_SIZE near the top and uncomment
               the ".stackseal" section near the end. */
        #if defined (__ARM_FEATURE_CMSE) && (__ARM_FEATURE_CMSE == 3U)
            __TZ_set_STACKSEAL_S((uint32_t *)(&__STACK_SEAL));
        #endif

            if(_on_reset)
                _on_reset();

        #if (defined(__ARM_FP) && (0 != __ARM_FP))  ||  (defined(__ARM_FEATURE_MVE) && (__ARM_FEATURE_MVE > 0))
            _EnableFpu();
        #endif
        #if __ICACHE_PRESENT == 1  ||  __DCACHE_PRESENT == 1
            _EnableCpuCache();
        #endif
        #if defined(SCB_CCR_LOB_Msk) || defined(SCB_CCR_BP_Msk)
            _EnableBranchCaches();
        #endif
        #if defined(ID_CMCC)
            _EnableCmccCache();
        #endif

            /* Set the vector table base address, if supported by this device. */
        #if defined (__VTOR_PRESENT) && (__VTOR_PRESENT == 1U)
            SCB->VTOR = (uint32_t)(&__VECTOR_TABLE[0]);
        #endif

            _InitData();
            __libc_init_array();

            if(_on_bootstrap)
                _on_bootstrap();

            /* The app is ready to go, call main. */
            exit(main());
        }
        '''
    
    return textwrap.dedent(reset)

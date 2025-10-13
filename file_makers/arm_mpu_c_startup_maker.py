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

'''arm_mpu_c_startup_maker.py

Contains a single public function to make a C file containing startup code and vector table
declarations for a single Arm Cortex-M device.
This is based on the sample startup code found in Arm CMSIS 6 at
https://github.com/ARM-software/CMSIS_6/blob/main/CMSIS/Core/Template/Device_M/Source/startup_Device.c.
'''

from device_info import *
from . import strings
import textwrap
from typing import IO


def run(proc_header_name: str, outfile: IO[str]) -> None:
    '''Make a C startup code file for the given device assuming it is a SAM ARM-based MPU.

    The proc_header_name is the name of a header file this can include to get processor-specific
    info. This can be the processor-specifc header file or an all-encompassing header that will
    figure out which processor-specific header to use based on macros. This should include the
    extension but not the full path.
    '''
    outfile.write(_get_file_prologue(proc_header_name))
    outfile.write('\n')
    outfile.write(_get_default_handlers())
    outfile.write('\n\n')
    outfile.write(_get_vector_table())
    outfile.write('\n\n')

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

        /* Defined in the linker scripts and are the tops of stacks for the different processor
           modes. The first one is for the "System" and "User" modes. The reset handler puts the
           processor into System mode before jumping to main().
           */
        extern uint32_t __StackTop;
        extern uint32_t __fiq_stack;
        extern uint32_t __irq_stack;
        extern uint32_t __svc_stack;
        extern uint32_t __abt_stack;
        extern uint32_t __und_stack;

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
        '''

    return header + textwrap.dedent(decls)


def _get_default_handlers() -> str:
    '''Return a string containing definitions for default interrupt and fault handlers.
    '''
    handlers: str = '''
        /* ----- Default Handlers: Provide your own definitions to override these. ----- */
        // Default Undefined Instruction Handler
        void __attribute__((noreturn, weak)) Undef_Handler(void)
        {
        #ifdef __DEBUG
            __BKPT(0);
        #endif
            while(1)
            {}
        }

        // Default Software Interrupt Handler
        void __attribute__((noreturn, weak)) SVC_Handler(void)
        {
        #ifdef __DEBUG
            __BKPT(0);
        #endif
            while(1)
            {}
        }

        // Default Prefetch Abort Handler
        void __attribute__((noreturn, weak)) PAbt_Handler(void)
        {
        #ifdef __DEBUG
            __BKPT(0);
        #endif
            while(1)
            {}
        }

        // Default Data Abort Handler
        void __attribute__((noreturn, weak)) DAbt_Handler(void)
        {
        #ifdef __DEBUG
            __BKPT(0);
        #endif
            while(1)
            {}
        }

        // Default Handler for normal interrupt requests
        void __attribute__((noreturn, weak)) IRQ_Handler(void)
        {
        #ifdef __DEBUG
            __BKPT(0);
        #endif
            while(1)
            {}
        }

        // Default Handler for fast interrupt requests
        void __attribute__((noreturn, weak)) FIQ_Handler(void)
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


def _get_vector_table() -> str:
    '''Return a string containing the definition of the vector table for ARM MPUs.

    The vector table for ARM MPUs is very simple, containing only 8 entries. The first entry is for
    the reset handler, a few others are for fault/abort handlers, and two are for interrupts. One
    of the spaces is unused, so we will put the binary size in there. A program loader can use that
    to know how big the program is.
    '''
    vec_table_decl =  f'''
        /* This is the ARM MPU vector table and is placed at the start of the program area.
           The first vector is the reset handler, so a bootloader can simply jump to the start
           of program space to start the app. The reset handler will copy this to address 0x00
           as required by the CPU after remapping 0x00 to the internal SRAM.

           The sixth vector slot is not used, so the size of the program is placed there. A
           bootloader can determine how much program data it needs to load. This trick is used by
           the onboard boot ROM when loading the second stage bootloader.
        */
        void __attribute__((section(".vectors"), used, retain, naked) Vectors(void)
        {{
            __asm__ volatile("ldr pc, =%0 \n\t"
                             "ldr pc, =%1 \n\t"
                             "ldr pc, =%2 \n\t"
                             "ldr pc, =%3 \n\t"
                             "ldr pc, =%4 \n\t"
                             ".word __fixed_size \n\t"
                             "ldr pc, =%5 \n\t"
                             "ldr pc, =%6 \n\t"
                             :  /* No Outputs */
                             :  "i" (Reset_Handler), 
                                "i" (Undef_Handler),
                                "i" (SVC_Handler),
                                "i" (PAbt_Handler),
                                "i" (DAbt_Handler),
                                "i" (IRQ_Handler),
                                "i" (FIQ_Handler)
                             :  "memory");
        }}
        '''

    return textwrap.dedent(vec_table_decl)


def _get_data_init_functions() -> str:
    '''Return a string containing functions used to initialize data sections.
    '''
    funcs: str = '''
        /* The ARM CPU expects the vector table to be at address 0x00, so we have to copy it from
           the start of program space to built-in SRAM. Normally, 0x00 is where the boot ROM resides,
           but the reset handler will remap SRAM to address 0x00 before jumping to main().
           */
        void __attribute__((weak, section(".reset.startup"))) _CopyVectors(void)
        {
            // These are defined in the linker script.
            extern uint32_t __vectors_source;
            extern uint32_t __svectors;
            extern uint32_t __evectors;

            uint32_t *src = &__vectors_source;
            uint32_t *dst = &__svectors;
            while(dst < &__evectors)
            {
                *dst++ = *src++;
            }
        }

        /* Zero out data found in the .bss and .tbss sections, the latter being for thread-local
           storage. Non-zero data is stored in the .data and .tdata (thread-local) sections, but
           those are already copied into RAM by the bootloader that loaded this application.
           */
        void __attribute__((weak, section(".reset.startup"))) _ZeroData(void)
        {
            // These are defined in the linker script. These span the normal and thread-local
            // sections so they can be initialized as one.
            extern uint32_t __bss_start;
            extern uint32_t __bss_end;

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
            /* Disable interrupts. */
            __set_CPSR(CPSR_I_Msk | CPSR_F_Msk | __get_CPSR());

            /* Reset SCTLR settings:
                -- Disable I and D caches
                -- Disable MMU
                -- Disable branch predictor if present
                -- Vector table is at 0x00, not 0xFFFF0000  */
            uint32_t sctlr = __get_SCTLR();
            sctlr &= ~(SCTLR_I_Msk | SCTLR_C_Msk | SCTLR_M_Msk | SCTLR_Z_Msk | SCTLR_V_Msk);
            __set_SCTLR(sctlr);

            /* Set the stack pointers for each processor mode to the tops of the stacks while keeping
               interrupts disabled. These symbols are defined in the linker script and the mask is
               used to keep the stacks 8-byte aligned. */
            __set_mode(CPSR_I_Msk | CPSR_F_Msk | CPSR_M_FIQ);
            __set_SP((uint32_t)&__fiq_stack & 0x07);
            __set_mode(CPSR_I_Msk | CPSR_F_Msk | CPSR_M_IRQ);
            __set_SP((uint32_t)&__irq_stack & 0x07);
            __set_mode(CPSR_I_Msk | CPSR_F_Msk | CPSR_M_SVC);
            __set_SP((uint32_t)&__svc_stack & 0x07);
            __set_mode(CPSR_I_Msk | CPSR_F_Msk | CPSR_M_ABT);
            __set_SP((uint32_t)&__abt_stack & 0x07);
            __set_mode(CPSR_I_Msk | CPSR_F_Msk | CPSR_M_UND);
            __set_SP((uint32_t)&__und_stack & 0x07);
            __set_mode(CPSR_I_Msk | CPSR_F_Msk | CPSR_M_SYS);
            __set_SP((uint32_t)&__StackTop & 0x07);

            /* The processor is now in "System" mode. */
            
            if(_on_reset)
                _on_reset();

        #if defined(__ARM_FP)  &&  0 != __ARM_FP
            __FPU_Enable();
        #endif

            _CopyVectors();
            _ZeroData();

            /* Remap the built-in SRAM from its normal address to 0x00, which is normally where the
               boot ROM is located. The SRAM is still accessible from its original address. */
        #if defined(AXIMX_REMAP_MASK)
            AXIMX_REGS->AXIMX_REMAP = AXIMX_REMAP_MASK);
        #elif defined(MATRIX_MRCR_MASK)
            MATRIX_REGS->MATRIX_MRCR = MATRIX_MRCR_MASK;
        #else
        #  warning Remap regs not found for this device.
        #endif

            __libc_init_array();

            if(_on_bootstrap)
                _on_bootstrap();

            /* The app is ready to go, call main. */
            exit(main());
        }
        '''

    return textwrap.dedent(reset)

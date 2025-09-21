/*
 * Copyright (c) 2009-2024 Arm Limited. All rights reserved.
 * Copyright (c) 2025, Jesse DeGuire
 * 
 * SPDX-License-Identifier: Apache-2.0
 * 
 * Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file
 * except in compliance with the License. You may obtain a copy of the License at
 * 
 * http://www.apache.org/licenses/LICENSE-2.0
 * 
 * Unless required by applicable law or agreed to in writing, software distributed under the
 * License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
 * either express or implied. See the License for the specific language governing permissions
 * and limitations under the License
 * 
 * Copied and adapted from code in Arm CMSIS 6 for Cortex-A devices. CMSIS 6 can be found on
 * GitHub at https://github.com/ARM-software/CMSIS_6.
 */

/* CMSIS does not support devices prior to the Cortex(R) branding, so this adapts some of the macros
   and functions provided by CMSIS for these older devices. This file was originally created for use
   with the ARM926EJ-S (ARMv5), but this should be usable with both ARMv4 and ARMv6 devices. You will
   need to consult the Technical Reference Manual for your device's CPU to check which registers and
   fields apply to your device.

   Some symbols with "CMSIS" in the name are kept here for compatiblity with code that uses CMSIS.
   */

#ifndef __ARM_LEGACY_ARM_CLANG_H
#define __ARM_LEGACY_ARM_CLANG_H

#pragma clang system_header   /* treat file as system include file */

#if (__ARM_ACLE >= 200)
  #include <arm_acle.h>
#else
  #error Compiler must support ACLE V2.0
#endif /* (__ARM_ACLE >= 200) */

/* Fallback for __has_builtin */
#ifndef __has_builtin
  #define __has_builtin(x) (0)
#endif

/* Compiler specific defines */
#ifndef   __ASM
  #define __ASM                                  __asm
#endif
#ifndef   __INLINE
  #define __INLINE                               inline
#endif
#ifndef   __STATIC_INLINE
  #define __STATIC_INLINE                        static inline
#endif
#ifndef   __STATIC_FORCEINLINE
  #define __STATIC_FORCEINLINE                   __attribute__((always_inline)) static inline
#endif
#ifndef   __NO_RETURN
  #define __NO_RETURN                            __attribute__((__noreturn__))
#endif
#ifndef   CMSIS_DEPRECATED
  #define CMSIS_DEPRECATED                       __attribute__((deprecated))
#endif
#ifndef   ARM_DEPRECATED
  #define ARM_DEPRECATED                         __attribute__((deprecated))
#endif
#ifndef   __USED
  #define __USED                                 __attribute__((used))
#endif
#ifndef   __WEAK
  #define __WEAK                                 __attribute__((weak))
#endif
#ifndef   __PACKED
  #define __PACKED                               __attribute__((packed, aligned(1)))
#endif
#ifndef   __PACKED_STRUCT
  #define __PACKED_STRUCT                        struct __attribute__((packed, aligned(1)))
#endif
#ifndef   __PACKED_UNION
  #define __PACKED_UNION                         union __attribute__((packed, aligned(1)))
#endif
#ifndef   __UNALIGNED_UINT16_WRITE
  #pragma clang diagnostic push
  #pragma clang diagnostic ignored "-Wpacked"
  __PACKED_STRUCT T_UINT16_WRITE { uint16_t v; };
  #pragma clang diagnostic pop
  #define __UNALIGNED_UINT16_WRITE(addr, val)    (void)((((struct T_UINT16_WRITE *)(void *)(addr))->v) = (val))
#endif
#ifndef   __UNALIGNED_UINT16_READ
  #pragma clang diagnostic push
  #pragma clang diagnostic ignored "-Wpacked"
  __PACKED_STRUCT T_UINT16_READ { uint16_t v; };
  #pragma clang diagnostic pop
  #define __UNALIGNED_UINT16_READ(addr)          (((const struct T_UINT16_READ *)(const void *)(addr))->v)
#endif
#ifndef   __UNALIGNED_UINT32_WRITE
  #pragma clang diagnostic push
  #pragma clang diagnostic ignored "-Wpacked"
  __PACKED_STRUCT T_UINT32_WRITE { uint32_t v; };
  #pragma clang diagnostic pop
  #define __UNALIGNED_UINT32_WRITE(addr, val)    (void)((((struct T_UINT32_WRITE *)(void *)(addr))->v) = (val))
#endif
#ifndef   __UNALIGNED_UINT32_READ
  #pragma clang diagnostic push
  #pragma clang diagnostic ignored "-Wpacked"
  __PACKED_STRUCT T_UINT32_READ { uint32_t v; };
  #pragma clang diagnostic pop
  #define __UNALIGNED_UINT32_READ(addr)          (((const struct T_UINT32_READ *)(const void *)(addr))->v)
#endif
#ifndef   __ALIGNED
  #define __ALIGNED(x)                           __attribute__((aligned(x)))
#endif
#ifndef   __RESTRICT
  #define __RESTRICT                             __restrict
#endif
#ifndef   __COMPILER_BARRIER
  #define __COMPILER_BARRIER()                   __ASM volatile("":::"memory")
#endif
#ifndef __NO_INIT
  #define __NO_INIT                              __attribute__ ((section (".noinit")))
#endif
#ifndef __ALIAS
  #define __ALIAS(x)                             __attribute__ ((alias(x)))
#endif

/* ##########################  Core Instruction Access  ######################### */

/* Define macros for porting to both thumb1 and thumb2.
 * For thumb1, use low register (r0-r7), specified by constraint "l"
 * Otherwise, use general registers, specified by constraint "r" */
#if defined (__thumb__) && !defined (__thumb2__)
#define __CMSIS_GCC_OUT_REG(r) "=l" (r)
#define __CMSIS_GCC_RW_REG(r) "+l" (r)
#define __CMSIS_GCC_USE_REG(r) "l" (r)
#define __ARM_GCC_OUT_REG(r) "=l" (r)
#define __ARM_GCC_RW_REG(r) "+l" (r)
#define __ARM_GCC_USE_REG(r) "l" (r)
#else
#define __CMSIS_GCC_OUT_REG(r) "=r" (r)
#define __CMSIS_GCC_RW_REG(r) "+r" (r)
#define __CMSIS_GCC_USE_REG(r) "r" (r)
#define __ARM_GCC_OUT_REG(r) "=r" (r)
#define __ARM_GCC_RW_REG(r) "+r" (r)
#define __ARM_GCC_USE_REG(r) "r" (r)
#endif

/**
  \brief   No Operation
  \details No Operation does nothing. This instruction can be used for code alignment purposes.
 */
#define __NOP()         __ASM volatile ("nop")


/**
  \brief   Wait For Interrupt
  \details Wait For Interrupt is a hint instruction that suspends execution until one of a number of events occurs.
 */
#define __WFI()         __set_WFI(0)


/**
  \brief    Instruction Synchronization Barrier
  \details  Flushes the CPU prefetch buffer to force re-fetching instructions.
            ARMv6: This is implemented as a write to a CP15 register and is called PrefetchFlush.
            Older: This was called an Instruction Memory Barrier (IMB) and was implementation-specific.
                   This follows Section 2.7.4 in Part A of the ARMv5TE Reference Manual, which says
                   that a restricted form of IMB can simply be an instruction other than B, BL, or
                   BLX that updates the PC. A "full" IMB may also need to flush caches.

            You can use either __ISB() for forward compatibility with CMSIS, _IMB(), or
            __PrefetchFlush().
 */
#if __ARM_ARCH >= 6
#  define __ISB()         __set_PFBF(0)
#else
#  define __ISB()         __ASM volatile("# PC load to flush prefetch \n\t"   \
                                         "ldr pc, =1f  \n"                    \
                                         "1:          \n\t"                   \
                                         "nop         \n\t"                   \
                                         ::: "memory")
#endif

#define __IMB()           __ISB()
#define __PrefetchFlush() __ISB()


/**
  \brief   Data Synchronization Barrier
  \details It completes when all explicit memory accesses before this instruction complete.
           This is implemented as a write to a CP15 register.
 */
#define __DSB()         __set_DSB(0)


/**
  \brief   Data Memory Barrier
  \details Prevents the CPU from reordering memory accesses across this instruction.
           ARMv6: This is implemented as a write to a CP15 register.
           Older: There is no instruction to do this, so this is a compiler barrier only.
 */
#if __ARM_ARCH >= 6
#  define __DMB()       __set_DMB(0)
#else
#  define __DMB()       __COMPILER_BARRIER()
#endif


/**
  \brief   Reverse byte order (32 bit)
  \details Reverses the byte order in unsigned integer value. For example, 0x12345678 becomes 0x78563412.
  \param [in]    value  Value to reverse
  \return               Reversed value
 */
__STATIC_FORCEINLINE uint32_t __REV(uint32_t value)
{
  return __builtin_bswap32(value);
}


/**
  \brief   Reverse byte order (16 bit)
  \details Reverses the byte order within each halfword of a word. For example, 0x12345678 becomes 0x34127856.
  \param [in]    value  Value to reverse
  \return               Reversed value
 */
__STATIC_FORCEINLINE uint32_t __REV16(uint32_t value)
{
  uint32_t result;

  __ASM ("rev16 %0, %1" : __CMSIS_GCC_OUT_REG (result) : __CMSIS_GCC_USE_REG (value) );
  return (result);
}


/**
  \brief   Reverse byte order (16 bit)
  \details Reverses the byte order in a 16-bit value and returns the signed 16-bit result. For example, 0x0080 becomes 0x8000.
  \param [in]    value  Value to reverse
  \return               Reversed value
 */
__STATIC_FORCEINLINE int16_t __REVSH(int16_t value)
{
  return (int16_t)__builtin_bswap16(value);
}


/**
  \brief   Rotate Right in unsigned value (32 bit)
  \details Rotate Right (immediate) provides the value of the contents of a register rotated by a variable number of bits.
  \param [in]    op1  Value to rotate
  \param [in]    op2  Number of Bits to rotate
  \return               Rotated value
 */
__STATIC_FORCEINLINE uint32_t __ROR(uint32_t op1, uint32_t op2)
{
  op2 %= 32U;
  if (op2 == 0U)
  {
    return op1;
  }
  return (op1 >> op2) | (op1 << (32U - op2));
}


/**
  \brief   Breakpoint
  \details Causes the processor to enter Debug state.
           Debug tools can use this to investigate system state when the instruction at a particular address is reached.
  \param [in]    value  is ignored by the processor.
                 If required, a debugger can use it to store additional information about the breakpoint.
 */
#define __BKPT(value) __ASM volatile ("bkpt "#value)


/**
  \brief   Reverse bit order of value
  \details Reverses the bit order of the given value.
  \param [in]    value  Value to reverse
  \return               Reversed value
 */
__STATIC_FORCEINLINE uint32_t __RBIT(uint32_t value)
{
  uint32_t result;

#if (__ARM_ARCH_ISA_THUMB >= 2)
   __ASM ("rbit %0, %1" : "=r" (result) : "r" (value) );
#else
  uint32_t s = (4U /*sizeof(v)*/ * 8U) - 1U; /* extra shift needed at end */

  result = value;                      /* r will be reversed bits of v; first get LSB of v */
  for (value >>= 1U; value != 0U; value >>= 1U)
  {
    result <<= 1U;
    result |= value & 1U;
    s--;
  }
  result <<= s;                        /* shift when v's highest bits are zero */
#endif
  return (result);
}


/**
  \brief   Count leading zeros
  \details Counts the number of leading zeros of a data value.
  \param [in]  value  Value to count the leading zeros
  \return             number of leading zeros in value
 */
__STATIC_FORCEINLINE uint8_t __CLZ(uint32_t value)
{
  /* Even though __builtin_clz produces a CLZ instruction on ARM, formally
     __builtin_clz(0) is undefined behaviour, so handle this case specially.
     This guarantees ARM-compatible results if happening to compile on a non-ARM
     target, and ensures the compiler doesn't decide to activate any
     optimisations using the logic "value was passed to __builtin_clz, so it
     is non-zero".
     ARM GCC 7.3 and possibly earlier will optimise this test away, leaving a
     single CLZ instruction.
   */
  if (value == 0U)
  {
    return 32U;
  }
  return __builtin_clz(value);
}


#if ((__ARM_FEATURE_SAT    >= 1) && \
     (__ARM_ARCH_ISA_THUMB >= 2)    )
/* __ARM_FEATURE_SAT is wrong for Armv8-M Baseline devices */
/**
  \brief   Signed Saturate
  \details Saturates a signed value.
  \param [in]  value  Value to be saturated
  \param [in]    sat  Bit position to saturate to (1..32)
  \return             Saturated value
 */
#define __SSAT(value, sat) __ssat(value, sat)


/**
  \brief   Unsigned Saturate
  \details Saturates an unsigned value.
  \param [in]  value  Value to be saturated
  \param [in]    sat  Bit position to saturate to (0..31)
  \return             Saturated value
 */
#define __USAT(value, sat) __usat(value, sat)

#else /* (__ARM_FEATURE_SAT >= 1) */
/**
  \brief   Signed Saturate
  \details Saturates a signed value.
  \param [in]  value  Value to be saturated
  \param [in]    sat  Bit position to saturate to (1..32)
  \return             Saturated value
 */
__STATIC_FORCEINLINE int32_t __SSAT(int32_t val, uint32_t sat)
{
  if ((sat >= 1U) && (sat <= 32U))
  {
    const int32_t max = (int32_t)((1U << (sat - 1U)) - 1U);
    const int32_t min = -1 - max ;
    if (val > max)
    {
      return (max);
    }
    else if (val < min)
    {
      return (min);
    }
  }
  return (val);
}


/**
  \brief   Unsigned Saturate
  \details Saturates an unsigned value.
  \param [in]  value  Value to be saturated
  \param [in]    sat  Bit position to saturate to (0..31)
  \return             Saturated value
 */
__STATIC_FORCEINLINE uint32_t __USAT(int32_t val, uint32_t sat)
{
  if (sat <= 31U)
  {
    const uint32_t max = ((1U << sat) - 1U);
    if (val > (int32_t)max)
    {
      return (max);
    }
    else if (val < 0)
    {
      return (0U);
    }
  }
  return ((uint32_t)val);
}
#endif /* (__ARM_FEATURE_SAT >= 1) */


#if (__ARM_FEATURE_LDREX >= 1)
/**
  \brief   Remove the exclusive lock
  \details Removes the exclusive lock which is created by LDREX.
 */
__STATIC_FORCEINLINE void __CLREX(void)
{
  __ASM volatile ("clrex" ::: "memory");
}


/**
  \brief   LDR Exclusive (8 bit)
  \details Executes a exclusive LDR instruction for 8 bit value.
  \param [in]    ptr  Pointer to data
  \return             value of type uint8_t at (*ptr)
 */
__STATIC_FORCEINLINE uint8_t __LDREXB(volatile uint8_t *addr)
{
  uint32_t result;

  __ASM volatile ("ldrexb %0, %1" : "=r" (result) : "Q" (*addr) );
  return ((uint8_t) result);    /* Add explicit type cast here */
}


/**
  \brief   STR Exclusive (8 bit)
  \details Executes a exclusive STR instruction for 8 bit values.
  \param [in]  value  Value to store
  \param [in]    ptr  Pointer to location
  \return          0  Function succeeded
  \return          1  Function failed
 */
__STATIC_FORCEINLINE uint32_t __STREXB(uint8_t value, volatile uint8_t *addr)
{
  uint32_t result;

  __ASM volatile ("strexb %0, %2, %1" : "=&r" (result), "=Q" (*addr) : "r" ((uint32_t)value) );
  return (result);
}
#endif /* (__ARM_FEATURE_LDREX >= 1) */


#if (__ARM_FEATURE_LDREX >= 2)
/**
  \brief   LDR Exclusive (16 bit)
  \details Executes a exclusive LDR instruction for 16 bit values.
  \param [in]    ptr  Pointer to data
  \return        value of type uint16_t at (*ptr)
 */
__STATIC_FORCEINLINE uint16_t __LDREXH(volatile uint16_t *addr)
{
  uint32_t result;

  __ASM volatile ("ldrexh %0, %1" : "=r" (result) : "Q" (*addr) );
  return ((uint16_t)result);    /* Add explicit type cast here */
}


/**
  \brief   STR Exclusive (16 bit)
  \details Executes a exclusive STR instruction for 16 bit values.
  \param [in]  value  Value to store
  \param [in]    ptr  Pointer to location
  \return          0  Function succeeded
  \return          1  Function failed
 */
__STATIC_FORCEINLINE uint32_t __STREXH(uint16_t value, volatile uint16_t *addr)
{
  uint32_t result;

  __ASM volatile ("strexh %0, %2, %1" : "=&r" (result), "=Q" (*addr) : "r" ((uint32_t)value) );
  return (result);
}
#endif /* (__ARM_FEATURE_LDREX >= 2) */


#if (__ARM_FEATURE_LDREX >= 4)
/**
  \brief   LDR Exclusive (32 bit)
  \details Executes a exclusive LDR instruction for 32 bit values.
  \param [in]    ptr  Pointer to data
  \return        value of type uint32_t at (*ptr)
 */
__STATIC_FORCEINLINE uint32_t __LDREXW(volatile uint32_t *addr)
{
  uint32_t result;

  __ASM volatile ("ldrex %0, %1" : "=r" (result) : "Q" (*addr) );
  return (result);
}


/**
  \brief   STR Exclusive (32 bit)
  \details Executes a exclusive STR instruction for 32 bit values.
  \param [in]  value  Value to store
  \param [in]    ptr  Pointer to location
  \return          0  Function succeeded
  \return          1  Function failed
 */
__STATIC_FORCEINLINE uint32_t __STREXW(uint32_t value, volatile uint32_t *addr)
{
  uint32_t result;

  __ASM volatile ("strex %0, %2, %1" : "=&r" (result), "=Q" (*addr) : "r" (value) );
  return (result);
}
#endif /* (__ARM_FEATURE_LDREX >= 4) */


#if (__ARM_ARCH_ISA_THUMB >= 2)
/**
  \brief   Rotate Right with Extend (32 bit)
  \details Moves each bit of a bitstring right by one bit.
           The carry input is shifted in at the left end of the bitstring.
  \param [in]    value  Value to rotate
  \return               Rotated value
 */
__STATIC_FORCEINLINE uint32_t __RRX(uint32_t value)
{
  uint32_t result;

  __ASM volatile ("rrx %0, %1" : "=r" (result) : "r" (value));
  return (result);
}


/**
  \brief   LDRT Unprivileged (8 bit)
  \details Executes a Unprivileged LDRT instruction for 8 bit value.
  \param [in]    ptr  Pointer to data
  \return             value of type uint8_t at (*ptr)
 */
__STATIC_FORCEINLINE uint8_t __LDRBT(volatile uint8_t *ptr)
{
  uint32_t result;

  __ASM volatile ("ldrbt %0, %1" : "=r" (result) : "Q" (*ptr) );
  return ((uint8_t)result);    /* Add explicit type cast here */
}


/**
  \brief   LDRT Unprivileged (16 bit)
  \details Executes a Unprivileged LDRT instruction for 16 bit values.
  \param [in]    ptr  Pointer to data
  \return        value of type uint16_t at (*ptr)
 */
__STATIC_FORCEINLINE uint16_t __LDRHT(volatile uint16_t *ptr)
{
  uint32_t result;

  __ASM volatile ("ldrht %0, %1" : "=r" (result) : "Q" (*ptr) );
  return ((uint16_t)result);    /* Add explicit type cast here */
}


/**
  \brief   LDRT Unprivileged (32 bit)
  \details Executes a Unprivileged LDRT instruction for 32 bit values.
  \param [in]    ptr  Pointer to data
  \return        value of type uint32_t at (*ptr)
 */
__STATIC_FORCEINLINE uint32_t __LDRT(volatile uint32_t *ptr)
{
  uint32_t result;

  __ASM volatile ("ldrt %0, %1" : "=r" (result) : "Q" (*ptr) );
  return (result);
}


/**
  \brief   STRT Unprivileged (8 bit)
  \details Executes a Unprivileged STRT instruction for 8 bit values.
  \param [in]  value  Value to store
  \param [in]    ptr  Pointer to location
 */
__STATIC_FORCEINLINE void __STRBT(uint8_t value, volatile uint8_t *ptr)
{
  __ASM volatile ("strbt %1, %0, #0" : "=Q" (*ptr) : "r" ((uint32_t)value) );
}


/**
  \brief   STRT Unprivileged (16 bit)
  \details Executes a Unprivileged STRT instruction for 16 bit values.
  \param [in]  value  Value to store
  \param [in]    ptr  Pointer to location
 */
__STATIC_FORCEINLINE void __STRHT(uint16_t value, volatile uint16_t *ptr)
{
  __ASM volatile ("strht %1, %0" : "=Q" (*ptr) : "r" ((uint32_t)value) );
}


/**
  \brief   STRT Unprivileged (32 bit)
  \details Executes a Unprivileged STRT instruction for 32 bit values.
  \param [in]  value  Value to store
  \param [in]    ptr  Pointer to location
 */
__STATIC_FORCEINLINE void __STRT(uint32_t value, volatile uint32_t *ptr)
{
  __ASM volatile ("strt %1, %0, #0" : "=Q" (*ptr) : "r" (value) );
}
#endif /* (__ARM_ARCH_ISA_THUMB >= 2) */


/* ###########################  Core Function Access  ########################### */

/**
  \brief   Enable IRQ Interrupts
  \details Enables IRQ interrupts by clearing CPSR<I>.
           Can only be executed in Privileged modes.
 */
__STATIC_FORCEINLINE void __enable_irq(void)
{
#if __ARM_ARCH >= 6
  __ASM volatile ("cpsie i" : : : "memory");
#else
  uint32_t sr;
  __ASM volatile ("mrs  %0, cpsr \n\t"
                  "bic  %0, %0, #0x80 \n\t"      // Clear <I> flag (bit 7)
                  "msr  cpsr_c, %0 \n\t"
                  : "=r"(sr)
                  : /* No inputs */
                  : "memory");
#endif
}


/**
  \brief   Disable IRQ Interrupts
  \details Disables IRQ interrupts by setting CPSR<I>.
           Can only be executed in Privileged modes.
 */
__STATIC_FORCEINLINE void __disable_irq(void)
{
#if __ARM_ARCH >= 6
  __ASM volatile ("cpsid i" : : : "memory");
#else
  uint32_t sr;
  __ASM volatile ("mrs  %0, cpsr \n\t"
                  "orr  %0, %0, #0x80 \n\t"      // Set <I> flag (bit 7)
                  "msr  cpsr_c, %0 \n\t"
                  : "=r"(sr)
                  : /* No inputs */
                  : "memory");
#endif
}

/**
  \brief   Enable FIQ
  \details Enables FIQ interrupts by clearing CPSR<F>.
           Can only be executed in Privileged modes.
 */
__STATIC_FORCEINLINE void __enable_fiq(void)
{
#if __ARM_ARCH >= 6
  __ASM volatile ("cpsie f" : : : "memory");
#else
  uint32_t sr;
  __ASM volatile ("mrs  %0, cpsr \n\t"
                  "bic  %0, %0, #0x40 \n\t"      // Clear <F> flag (bit 6)
                  "msr  cpsr_c, %0 \n\t"
                  : "=r"(sr)
                  : /* No inputs */
                  : "memory");
#endif
}


/**
  \brief   Disable FIQ
  \details Disables FIQ interrupts by setting CPSR<F>.
           Can only be executed in Privileged modes.
 */
__STATIC_FORCEINLINE void __disable_fiq(void)
{
#if __ARM_ARCH >= 6
  __ASM volatile ("cpsid f" : : : "memory");
#else
  uint32_t sr;
  __ASM volatile ("mrs  %0, cpsr \n\t"
                  "orr  %0, %0, #0x40 \n\t"      // Set <F> flag (bit 6)
                  "msr  cpsr_c, %0 \n\t"
                  : "=r"(sr)
                  : /* No inputs */
                  : "memory");
#endif
}


/**
  \brief   Enable IRQ and FIQ
  \details Enables IRQ and FIQ interrupts by clearing CPSR<F> and CPSR<I>.
           Can only be executed in Privileged modes.
 */
__STATIC_FORCEINLINE void __enable_irq_fiq(void)
{
#if __ARM_ARCH >= 6
  __ASM volatile ("cpsie if" : : : "memory");
#else
  uint32_t sr;
  __ASM volatile ("mrs  %0, cpsr \n\t"
                  "bic  %0, %0, #0xC0 \n\t"      // Clear <F> and <I> flags
                  "msr  cpsr_c, %0 \n\t"
                  : "=r"(sr)
                  : /* No inputs */
                  : "memory");
#endif
}


/**
  \brief   Disable IRQ and FIQ
  \details Disables IRQ and FIQ interrupts by clearing CPSR<F> and CPSR<I>..
           Can only be executed in Privileged modes.
 */
__STATIC_FORCEINLINE void __disable_irq_fiq(void)
{
#if __ARM_ARCH >= 6
  __ASM volatile ("cpsid if" : : : "memory");
#else
  uint32_t sr;
  __ASM volatile ("mrs  %0, cpsr \n\t"
                  "orr  %0, %0, #0xC0 \n\t"      // Set <F> and <I> flags
                  "msr  cpsr_c, %0 \n\t"
                  : "=r"(sr)
                  : /* No inputs */
                  : "memory");
#endif
}


/**
  \brief   Get FPSID
  \details Returns the current value of the Floating Point System ID Register.
  \return               Floating Point System ID Register register value
 */
__STATIC_FORCEINLINE uint32_t __get_FPSID(void)
{
#if (defined(__ARM_FP) && (__ARM_FP >= 1))
  uint32_t fpsid;
  __ASM volatile ("fmrx %0, fpsid" : "=r" (fpsid) : : "memory")
  return fpsid;
#else
  return (0U);
#endif
}


/**
  \brief   Get FPSCR
  \details Returns the current value of the Floating Point Status/Control register.
  \return               Floating Point Status/Control register value
 */
__STATIC_FORCEINLINE uint32_t __get_FPSCR(void)
{
#if (defined(__ARM_FP) && (__ARM_FP >= 1))
  uint32_t fpscr;
  __ASM volatile ("fmrx %0, fpscr" : "=r" (fpscr) : : "memory")
  return fpscr;
#else
  return (0U);
#endif
}


/**
  \brief   Set FPSCR
  \details Assigns the given value to the Floating Point Status/Control register.
  \param [in]    fpscr  Floating Point Status/Control value to set
 */
__STATIC_FORCEINLINE void __set_FPSCR(uint32_t fpscr)
{
#if (defined(__ARM_FP) && (__ARM_FP >= 1))
  __ASM volatile ("fmxr fpscr, %0" : : "r"(fpscr) : "memory")
#else
  (void)fpscr;
#endif
}



/* ###################  Compiler specific Intrinsics  ########################### */

#if (defined (__ARM_FEATURE_DSP) && (__ARM_FEATURE_DSP == 1))
  #define     __SADD8                 __builtin_arm_sadd8
  #define     __QADD8                 __builtin_arm_qadd8
  #define     __SHADD8                __builtin_arm_shadd8
  #define     __UADD8                 __builtin_arm_uadd8
  #define     __UQADD8                __builtin_arm_uqadd8
  #define     __UHADD8                __builtin_arm_uhadd8
  #define     __SSUB8                 __builtin_arm_ssub8
  #define     __QSUB8                 __builtin_arm_qsub8
  #define     __SHSUB8                __builtin_arm_shsub8
  #define     __USUB8                 __builtin_arm_usub8
  #define     __UQSUB8                __builtin_arm_uqsub8
  #define     __UHSUB8                __builtin_arm_uhsub8
  #define     __SADD16                __builtin_arm_sadd16
  #define     __QADD16                __builtin_arm_qadd16
  #define     __SHADD16               __builtin_arm_shadd16
  #define     __UADD16                __builtin_arm_uadd16
  #define     __UQADD16               __builtin_arm_uqadd16
  #define     __UHADD16               __builtin_arm_uhadd16
  #define     __SSUB16                __builtin_arm_ssub16
  #define     __QSUB16                __builtin_arm_qsub16
  #define     __SHSUB16               __builtin_arm_shsub16
  #define     __USUB16                __builtin_arm_usub16
  #define     __UQSUB16               __builtin_arm_uqsub16
  #define     __UHSUB16               __builtin_arm_uhsub16
  #define     __SASX                  __builtin_arm_sasx
  #define     __QASX                  __builtin_arm_qasx
  #define     __SHASX                 __builtin_arm_shasx
  #define     __UASX                  __builtin_arm_uasx
  #define     __UQASX                 __builtin_arm_uqasx
  #define     __UHASX                 __builtin_arm_uhasx
  #define     __SSAX                  __builtin_arm_ssax
  #define     __QSAX                  __builtin_arm_qsax
  #define     __SHSAX                 __builtin_arm_shsax
  #define     __USAX                  __builtin_arm_usax
  #define     __UQSAX                 __builtin_arm_uqsax
  #define     __UHSAX                 __builtin_arm_uhsax
  #define     __USAD8                 __builtin_arm_usad8
  #define     __USADA8                __builtin_arm_usada8
  #define     __SSAT16                __builtin_arm_ssat16
  #define     __USAT16                __builtin_arm_usat16
  #define     __UXTB16                __builtin_arm_uxtb16
  #define     __UXTAB16               __builtin_arm_uxtab16
  #define     __SXTB16                __builtin_arm_sxtb16
  #define     __SXTAB16               __builtin_arm_sxtab16
  #define     __SMUAD                 __builtin_arm_smuad
  #define     __SMUADX                __builtin_arm_smuadx
  #define     __SMLAD                 __builtin_arm_smlad
  #define     __SMLADX                __builtin_arm_smladx
  #define     __SMLALD                __builtin_arm_smlald
  #define     __SMLALDX               __builtin_arm_smlaldx
  #define     __SMUSD                 __builtin_arm_smusd
  #define     __SMUSDX                __builtin_arm_smusdx
  #define     __SMLSD                 __builtin_arm_smlsd
  #define     __SMLSDX                __builtin_arm_smlsdx
  #define     __SMLSLD                __builtin_arm_smlsld
  #define     __SMLSLDX               __builtin_arm_smlsldx
  #define     __SEL                   __builtin_arm_sel
  #define     __QADD                  __builtin_arm_qadd
  #define     __QSUB                  __builtin_arm_qsub

  #if __ARM_ARCH >= 6
    #define __PKHBT(ARG1,ARG2,ARG3) \
    __extension__ \
    ({                          \
      uint32_t __RES, __ARG1 = (ARG1), __ARG2 = (ARG2); \
      __ASM ("pkhbt %0, %1, %2, lsl %3" : "=r" (__RES) :  "r" (__ARG1), "r" (__ARG2), "I" (ARG3)  ); \
      __RES; \
     })
  
    #define __PKHTB(ARG1,ARG2,ARG3) \
    __extension__ \
    ({                          \
      uint32_t __RES, __ARG1 = (ARG1), __ARG2 = (ARG2); \
      if (ARG3 == 0) \
        __ASM ("pkhtb %0, %1, %2" : "=r" (__RES) :  "r" (__ARG1), "r" (__ARG2)  ); \
      else \
        __ASM ("pkhtb %0, %1, %2, asr %3" : "=r" (__RES) :  "r" (__ARG1), "r" (__ARG2), "I" (ARG3)  ); \
      __RES; \
     })
  
    __STATIC_FORCEINLINE uint32_t __SXTB16_RORn(uint32_t op1, uint32_t rotate)
    {
        uint32_t result;
        if (__builtin_constant_p(rotate) && ((rotate == 8U) || (rotate == 16U) || (rotate == 24U)))
        {
            __ASM volatile("sxtb16 %0, %1, ROR %2" : "=r"(result) : "r"(op1), "i"(rotate));
        }
        else
        {
            result = __SXTB16(__ROR(op1, rotate));
        }
        return result;
    }
  
    __STATIC_FORCEINLINE uint32_t __SXTAB16_RORn(uint32_t op1, uint32_t op2, uint32_t rotate)
    {
        uint32_t result;
        if (__builtin_constant_p(rotate) && ((rotate == 8U) || (rotate == 16U) || (rotate == 24U)))
        {
            __ASM volatile("sxtab16 %0, %1, %2, ROR %3" : "=r"(result) : "r"(op1), "r"(op2), "i"(rotate));
        }
        else
        {
            result = __SXTAB16(op1, __ROR(op2, rotate));
        }
        return result;
    }
  
    __STATIC_FORCEINLINE int32_t __SMMLA (int32_t op1, int32_t op2, int32_t op3)
    {
      int32_t result;
    
      __ASM volatile ("smmla %0, %1, %2, %3" : "=r" (result): "r"  (op1), "r" (op2), "r" (op3) );
      return (result);
    }
  #endif /* __ARM_ARCH >= 6 */

#endif /* (defined (__ARM_FEATURE_DSP) && (__ARM_FEATURE_DSP == 1)) */



/* ###########################  Core Function Access  ########################### */

/** \brief  Get CPSR Register
    \return               CPSR Register value
 */
__STATIC_FORCEINLINE uint32_t __get_CPSR(void)
{
  uint32_t result;
  __ASM volatile("MRS %0, cpsr" : "=r" (result) );
  return(result);
}

/** \brief  Set CPSR Register
    \param [in]    cpsr  CPSR value to set
 */
__STATIC_FORCEINLINE void __set_CPSR(uint32_t cpsr)
{
  __ASM volatile ("MSR cpsr, %0" : : "r" (cpsr) : "cc", "memory");
}

/** \brief  Get Mode
    \return                Processor Mode
 */
__STATIC_FORCEINLINE uint32_t __get_mode(void)
{
  return (__get_CPSR() & 0x1FU);
}

/** \brief  Set Mode
    \param [in]    mode  Mode value to set
 */
__STATIC_FORCEINLINE void __set_mode(uint32_t mode)
{
  __ASM volatile("MSR  cpsr_c, %0" : : "r" (mode) : "memory");
}

/** \brief  Get Stack Pointer
    \return Stack Pointer value
 */
__STATIC_FORCEINLINE uint32_t __get_SP(void)
{
  uint32_t result;
  __ASM volatile("MOV  %0, sp" : "=r" (result) : : "memory");
  return result;
}

/** \brief  Set Stack Pointer
    \param [in]    stack  Stack Pointer value to set
 */
__STATIC_FORCEINLINE void __set_SP(uint32_t stack)
{
  __ASM volatile("MOV  sp, %0" : : "r" (stack) : "memory");
}

/** \brief  Get USR/SYS Stack Pointer
    \return USR/SYS Stack Pointer value
 */
__STATIC_FORCEINLINE uint32_t __get_SP_usr(void)
{
  uint32_t cpsr;
  uint32_t result;
  __ASM volatile(
    "MRS     %0, cpsr   \n"
    "CPS     #0x1F      \n" // no effect in USR mode
    "MOV     %1, sp     \n"
    "MSR     cpsr_c, %0 \n" // no effect in USR mode
    :  "=r"(cpsr), "=r"(result) : : "memory"
    );
  __ISB();
  return result;
}

/** \brief  Set USR/SYS Stack Pointer
    \param [in]    topOfProcStack  USR/SYS Stack Pointer value to set
 */
__STATIC_FORCEINLINE void __set_SP_usr(uint32_t topOfProcStack)
{
  uint32_t cpsr;
  __ASM volatile(
    "MRS     %0, cpsr   \n"
    "CPS     #0x1F      \n" // no effect in USR mode
    "MOV     sp, %1     \n"
    "MSR     cpsr_c, %0 \n" // no effect in USR mode
    : "=r"(cpsr) : "r" (topOfProcStack) : "memory"
    );
  __ISB();
}

/** \brief  Get FPEXC
    \return               Floating Point Exception Control register value
 */
__STATIC_FORCEINLINE uint32_t __get_FPEXC(void)
{
#if (__FPU_PRESENT == 1)
  uint32_t result;
  __ASM volatile("FMRX %0, fpexc" : "=r" (result) : : "memory");
  return(result);
#else
  return(0);
#endif
}

/** \brief  Set FPEXC
    \param [in]    fpexc  Floating Point Exception Control value to set
 */
__STATIC_FORCEINLINE void __set_FPEXC(uint32_t fpexc)
{
#if (__FPU_PRESENT == 1)
  __ASM volatile ("FMXR fpexc, %0" : : "r" (fpexc) : "memory");
#endif
}

/*
 * Include common core functions to access Coprocessor 15 registers
 */

#define __get_CP(cp, op1, Rt, CRn, CRm, op2) __ASM volatile("MRC p" # cp ", " # op1 ", %0, c" # CRn ", c" # CRm ", " # op2 : "=r" (Rt) : : "memory" )
#define __set_CP(cp, op1, Rt, CRn, CRm, op2) __ASM volatile("MCR p" # cp ", " # op1 ", %0, c" # CRn ", c" # CRm ", " # op2 : : "r" (Rt) : "memory" )

#if defined(__ARM_ARCH_5TE__)  ||  __ARM_ARCH >= 6
#  define __get_CP64(cp, op1, Rt, CRm)         __ASM volatile("MRRC p" # cp ", " # op1 ", %Q0, %R0, c" # CRm  : "=r" (Rt) : : "memory" )
#  define __set_CP64(cp, op1, Rt, CRm)         __ASM volatile("MCRR p" # cp ", " # op1 ", %Q0, %R0, c" # CRm  : : "r" (Rt) : "memory" )
#endif

#include "arm_cp15.h"

/** \brief  Enable Floating Point Unit
 */
__STATIC_INLINE void __FPU_Enable(void)
{
#if (__FPU_PRESENT == 1)
#  if __ARM_ARCH >= 6
  // Permit access to VFP registers by modifying CPACR
  const uint32_t cpacr = __get_CPACR();
  __set_CPACR(cpacr | 0x00F00000ul);
  __ISB();
#  endif

  // Enable VFP
  const uint32_t fpexc = __get_FPEXC();
  __set_FPEXC(fpexc | 0x40000000ul);

  __ASM volatile(
    // Initialise VFP registers to 0
    "        MOV     R2,#0             \n"
    "        FMDRR   D0, R2,R2         \n"
    "        FMDRR   D1, R2,R2         \n"
    "        FMDRR   D2, R2,R2         \n"
    "        FMDRR   D3, R2,R2         \n"
    "        FMDRR   D4, R2,R2         \n"
    "        FMDRR   D5, R2,R2         \n"
    "        FMDRR   D6, R2,R2         \n"
    "        FMDRR   D7, R2,R2         \n"
    "        FMDRR   D8, R2,R2         \n"
    "        FMDRR   D9, R2,R2         \n"
    "        FMDRR   D10,R2,R2         \n"
    "        FMDRR   D11,R2,R2         \n"
    "        FMDRR   D12,R2,R2         \n"
    "        FMDRR   D13,R2,R2         \n"
    "        FMDRR   D14,R2,R2         \n"
    "        FMDRR   D15,R2,R2         \n"
    : : : "cc", "r2"
  );

  // Initialise FPSCR to a known state
  const uint32_t fpscr = __get_FPSCR();
  __set_FPSCR(fpscr & 0x00086060ul);
#endif /* __FPU_PRESENT == 1 */
}

#endif /* __ARM_LEGACY_ARM_CLANG_H */

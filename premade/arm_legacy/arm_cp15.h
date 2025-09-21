/*
 * Copyright (c) 2009-2023 Arm Limited. All rights reserved.
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

#ifndef __ARM_LEGACY_ARM_CP15_H
#define __ARM_LEGACY_ARM_CP15_H

#if defined (__clang__)
  #pragma clang system_header    /* treat file as system include file */
#endif

//
// c0: ID Registers
//

/** \brief  Get MAINID
    \return Main ID register value
 */
__STATIC_FORCEINLINE uint32_t __get_MAINID(void)
{
  uint32_t result;
  __get_CP(15, 0, result, 0, 0, 0);
  return result;
}

/** \brief  Get CACHETYPE
    \return Cache Type register value
 */
__STATIC_FORCEINLINE uint32_t __get_CACHETYPE(void)
{
  uint32_t result;
  __get_CP(15, 0, result, 0, 0, 1);
  return result;
}

/** \brief  Get TCMSTATUS
    \return TCM Status register value
 */
__STATIC_FORCEINLINE uint32_t __get_TCMSTATUS(void)
{
  uint32_t result;
  __get_CP(15, 0, result, 0, 0, 2);
  return result;
}

/** \brief  Get TLBTYPE
    \return TLB Type register value
 */
__STATIC_FORCEINLINE uint32_t __get_TLBTYPE(void)
{
  uint32_t result;
  __get_CP(15, 0, result, 0, 0, 3);
  return result;
}

/** \brief  Get MPUTYPE
    \return MPU Type register value
 */
__STATIC_FORCEINLINE uint32_t __get_MPUTYPE(void)
{
  uint32_t result;
  __get_CP(15, 0, result, 0, 0, 4);
  return result;
}


//
// c1: Control Register
//

/** \brief  Set SCTLR

    This function assigns the given value to the System Control Register.

    \param [in]    sctlr  System Control Register value to set
 */
__STATIC_FORCEINLINE void __set_SCTLR(uint32_t sctlr)
{
  __set_CP(15, 0, sctlr, 1, 0, 0);
}

/** \brief  Get SCTLR
    \return               System Control Register value
 */
__STATIC_FORCEINLINE uint32_t __get_SCTLR(void)
{
  uint32_t result;
  __get_CP(15, 0, result, 1, 0, 0);
  return result;
}

/** \brief  Get ACTLR (ARMv6 only)
    \return               Auxiliary Control register value
 */
__STATIC_FORCEINLINE uint32_t __get_ACTLR(void)
{
  uint32_t result;
  __get_CP(15, 0, result, 1, 0, 1);
  return(result);
}

/** \brief  Set ACTLR (ARMv6 only)
    \param [in]    actlr  Auxiliary Control value to set
 */
__STATIC_FORCEINLINE void __set_ACTLR(uint32_t actlr)
{
  __set_CP(15, 0, actlr, 1, 0, 1);
}

/** \brief  Get CPACR (ARMv6 only)
    \return               Coprocessor Access Control register value
 */
__STATIC_FORCEINLINE uint32_t __get_CPACR(void)
{
  uint32_t result;
  __get_CP(15, 0, result, 1, 0, 2);
  return result;
}

/** \brief  Set CPACR (ARMv6 only)
    \param [in]    cpacr  Coprocessor Access Control value to set
 */
__STATIC_FORCEINLINE void __set_CPACR(uint32_t cpacr)
{
  __set_CP(15, 0, cpacr, 1, 0, 2);
}


//
// c2: Translation Table Base Register (MMU) or region control bits (MPU)
//

/** \brief  Get TTBR0

    This function returns the value of the Translation Table Base Register 0 when using an MMU.

    \return               Translation Table Base Register 0 value
 */
__STATIC_FORCEINLINE uint32_t __get_TTBR0(void)
{
  uint32_t result;
  __get_CP(15, 0, result, 2, 0, 0);
  return result;
}

/** \brief  Set TTBR0

    This function assigns the given value to the Translation Table Base Register 0 when using an MMU.

    \param [in]    ttbr0  Translation Table Base Register 0 value to set
 */
__STATIC_FORCEINLINE void __set_TTBR0(uint32_t ttbr0)
{
  __set_CP(15, 0, ttbr0, 2, 0, 0);
}

/** \brief  Get TTBR1

    This function returns the value of the Translation Table Base Register 1 when using an MMU.

    \return               Translation Table Base Register 1 value
 */
__STATIC_FORCEINLINE uint32_t __get_TTBR1(void)
{
  uint32_t result;
  __get_CP(15, 0, result, 2, 0, 1);
  return result;
}

/** \brief  Set TTBR1

    This function assigns the given value to the Translation Table Base Register 1 when using an MMU.

    \param [in]    ttbr1  Translation Table Base Register 1 value to set
 */
__STATIC_FORCEINLINE void __set_TTBR1(uint32_t ttbr1)
{
  __set_CP(15, 0, ttbr1, 2, 0, 1);
}

/** \brief  Get TTBCTRL

    This function returns the value of the Translation Table Base Control Register when using an MMU.

    \return               Translation Table Base Control Register value
 */
__STATIC_FORCEINLINE uint32_t __get_TTBCTRL(void)
{
  uint32_t result;
  __get_CP(15, 0, result, 2, 0, 2);
  return result;
}

/** \brief  Set TTBCTRL

    This function assigns the given value to the Translation Table Base Control Register when using
    an MMU.

    \param [in]    ttbctrl  Translation Table Base Control Register value to set
 */
__STATIC_FORCEINLINE void __set_TTBCTRL(uint32_t ttbctrl)
{
  __set_CP(15, 0, ttbctrl, 2, 0, 2);
}

/** \brief  Get MPUDCC

    This function returns the value of the Data Cache Control register when using a memory
    protection unit.

    \return               MPU Data Cache Control register value
 */
__STATIC_FORCEINLINE uint32_t __get_MPUDCC(void)
{
  uint32_t result;
  __get_CP(15, 0, result, 2, 0, 0);
  return result;
}

/** \brief  Set MPUDCC

    This function assigns the given value to the Data Cache Control register when using a
    memory protection unit.

    \param [in]    dcc  MPU Data Cache Control register value to set
 */
__STATIC_FORCEINLINE void __set_MPUDCC(uint32_t dcc)
{
  __set_CP(15, 0, dcc, 2, 0, 0);
}

/** \brief  Get MPUICC

    This function returns the value of the Instruction Cache Control register when using a memory
    protection unit.

    \return               MPU Instruction Cache Control register value
 */
__STATIC_FORCEINLINE uint32_t __get_MPUICC(void)
{
  uint32_t result;
  __get_CP(15, 0, result, 2, 0, 1);
  return result;
}

/** \brief  Set MPUICC

    This function assigns the given value to the Instruction Cache Control register when using a
    memory protection unit.

    \param [in]    icc  MPU Instruction Cache Control register value to set
 */
__STATIC_FORCEINLINE void __set_MPUICC(uint32_t icc)
{
  __set_CP(15, 0, icc, 2, 0, 1);
}


//
// c3: Domain Access Control Register
//

/** \brief  Get DACR

    This function returns the value of the Domain Access Control Register when using the MMU.

    \return               Domain Access Control Register value
 */
__STATIC_FORCEINLINE uint32_t __get_DACR(void)
{
  uint32_t result;
  __get_CP(15, 0, result, 3, 0, 0);
  return result;
}

/** \brief  Set DACR

    This function assigns the given value to the Domain Access Control Register when using the MMU.

    \param [in]    dacr   Domain Access Control Register value to set
 */
__STATIC_FORCEINLINE void __set_DACR(uint32_t dacr)
{
  __set_CP(15, 0, dacr, 3, 0, 0);
}

/** \brief  Get MPUWBC

    This function returns the value of the Write Buffer Control register when using a memory
    protection unit.

    \return               MPU Write Buffer Control register value
 */
__STATIC_FORCEINLINE uint32_t __get_MPUWBC(void)
{
  uint32_t result;
  __get_CP(15, 0, result, 3, 0, 0);
  return result;
}

/** \brief  Set MPUWBC

    This function assigns the given value to the Write Buffer Control register when using a
    memory protection unit.

    \param [in]    wbc  MPU Write Buffer Control register value to set
 */
__STATIC_FORCEINLINE void __set_MPUWBC(uint32_t wbc)
{
  __set_CP(15, 0, wbc, 3, 0, 0);
}


//
// c4: Reserved on ARM9
//

//
// c5: Fault Status Registers
//

/** \brief  Get DFSR
    \return               Data Fault Status Register value
 */
__STATIC_FORCEINLINE uint32_t __get_DFSR(void)
{
  uint32_t result;
  __get_CP(15, 0, result, 5, 0, 0);
  return result;
}

/** \brief  Set DFSR
    \param [in]    dfsr  Data Fault Status value to set
 */
__STATIC_FORCEINLINE void __set_DFSR(uint32_t dfsr)
{
  __set_CP(15, 0, dfsr, 5, 0, 0);
}

/** \brief  Get IFSR
    \return               Instruction Fault Status Register value
 */
__STATIC_FORCEINLINE uint32_t __get_IFSR(void)
{
  uint32_t result;
  __get_CP(15, 0, result, 5, 0, 1);
  return result;
}

/** \brief  Set IFSR
    \param [in]    ifsr  Instruction Fault Status value to set
 */
__STATIC_FORCEINLINE void __set_IFSR(uint32_t ifsr)
{
  __set_CP(15, 0, ifsr, 5, 0, 1);
}


//
// c6: Fault Address Registers
//

/** \brief  Get DFAR
    \return Data Fault Address Register value
 */
__STATIC_FORCEINLINE uint32_t __get_DFAR(void)
{
  uint32_t result;
  __get_CP(15, 0, result, 6, 0, 0);
  return result;
}

/** \brief  Set DFAR
    \param [in]    far  Data Fault Address value to set
 */
__STATIC_FORCEINLINE void __set_DFAR(uint32_t far)
{
  __set_CP(15, 0, far, 6, 0, 0);
}

/** \brief  Get WFAR
    \return Watchpoint Fault Address Register value
 */
__STATIC_FORCEINLINE uint32_t __get_WFAR(void)
{
  uint32_t result;
  __get_CP(15, 0, result, 6, 0, 1);
  return result;
}

/** \brief  Set WFAR
    \param [in]    far  Watchpoint Fault Address value to set
 */
__STATIC_FORCEINLINE void __set_WFAR(uint32_t far)
{
  __set_CP(15, 0, far, 6, 0, 1);
}

/** \brief  Get IFAR
    \return Instruction Fault Address Register value
 */
__STATIC_FORCEINLINE uint32_t __get_IFAR(void)
{
  uint32_t result;
  __get_CP(15, 0, result, 6, 0, 2);
  return result;
}

/** \brief  Set IFAR
    \param [in]    far  Instruction Fault Address value to set
 */
__STATIC_FORCEINLINE void __set_IFAR(uint32_t far)
{
  __set_CP(15, 0, far, 6, 0, 2);
}


//
// c7: Cache Operations Registers
//

/** \brief  Wait for interrupt

   Drain write buffers then put processor to sleep until an interrupt wakes it up.
 */
__STATIC_FORCEINLINE void __set_WFI(uint32_t value)
{
  __set_CP(15, 0, value, 7, 0, 4);
}

/** \brief  Set ICIALLU

  Instruction Cache Invalidate All
 */
__STATIC_FORCEINLINE void __set_ICIALLU(uint32_t value)
{
  __set_CP(15, 0, value, 7, 5, 0);
}

/** \brief  Set ICIMVAC

  Instruction Cache Invalidate
 */
__STATIC_FORCEINLINE void __set_ICIMVAC(uint32_t value)
{
  __set_CP(15, 0, value, 7, 5, 1);
}

/** \brief  Set PFBF

  Prefetch buffer flush. Newer ARM ISAs have an ISB instruction to do this. This is on ARMv6 only. 
  */
__STATIC_FORCEINLINE void __set_PFBF(uint32_t value)
{
  __set_CP(15, 0, value, 7, 5, 4);
}

/** \brief  Set ISB

  This is another name for __set_PFBF(). This matches the ISB instruction in later ISAs that does
  more or less the same thing.
 */
__STATIC_FORCEINLINE void __set_ISB(uint32_t value)
{
  __set_CP(15, 0, value, 7, 5, 4);
}

/** \brief  Set BPIALL.

  Branch Predictor Invalidate All
 */
__STATIC_FORCEINLINE void __set_BPIALL(uint32_t value)
{
  __set_CP(15, 0, value, 7, 5, 6);
}

/** \brief  Set ICISW

  Invalidate ICache single entry (Set/Way)
 */
__STATIC_FORCEINLINE void __set_ICISW(uint32_t value)
{
  __set_CP(15, 0, value, 7, 6, 2);
}

/** \brief  Set DCIALLU

  Data Cache Invalidate All
 */
__STATIC_FORCEINLINE void __set_DCIALLU(uint32_t value)
{
  __set_CP(15, 0, value, 7, 6, 0);
}

/** \brief  Set DCIMVAC

  Invalidate DCache single entry (MVA)
 */
__STATIC_FORCEINLINE void __set_DCIMVAC(uint32_t value)
{
  __set_CP(15, 0, value, 7, 6, 1);
}

/** \brief  Set DCISW

  Invalidate DCache single entry (Set/Way)
 */
__STATIC_FORCEINLINE void __set_DCISW(uint32_t value)
{
  __set_CP(15, 0, value, 7, 6, 2);
}

/** \brief  Set DCIALLU

  Instruction and Data Cache Invalidate All
 */
__STATIC_FORCEINLINE void __set_IDCIALLU(uint32_t value)
{
  __set_CP(15, 0, value, 7, 7, 0);
}

/** \brief  Set DCCMVAC

  Clean DCache single entry (MVA)
 */
__STATIC_FORCEINLINE void __set_DCCMVAC(uint32_t value)
{
  __set_CP(15, 0, value, 7, 10, 1);
}

/** \brief  Set DCCSW

  Clean DCache single entry (Set/Way)
 */
__STATIC_FORCEINLINE void __set_DCCSW(uint32_t value)
{
  __set_CP(15, 0, value, 7, 10, 2);
}

/** \brief  Set DCTC

  Test and clean DCache, setting Z in CPSR to 1 when the cache contains no dirty lines.
 */
__STATIC_FORCEINLINE void __set_DCTC(void)
{
  __ASM volatile("MRC p15, 0, r15, c7, c10, 3" ::: "memory");
}

/** \brief  Set DSB

   Drains the internal write buffer and blocks until complete. This also blocks until all cache, TLB,
   and branch predictor operations have completed. Newer ARM ISAs have a DSB instruction to do this.
 */
__STATIC_FORCEINLINE void __set_DSB(uint32_t value)
{
  __set_CP(15, 0, value, 7, 10, 4);
}

/** \brief  Set DWB
 
   In ARMv5 and older, a DSB operation was called "drain write buffer". This is the same as
   __set_DSB().
 */
__STATIC_FORCEINLINE void __set_DWB(uint32_t value)
{
  __set_CP(15, 0, value, 7, 10, 4);
}

/** \brief  Set DMB

   Create a memory barrier so that memory accesses are not reordered past this instruction.
   Newer ARM ISAs have a DMB instruction to do this. This is on ARMv6 only.
 */
__STATIC_FORCEINLINE void __set_DMB(uint32_t value)
{
  __set_CP(15, 0, value, 7, 10, 5);
}


/** \brief  Set ICPFMVAC

  Prefetch ICache line (MVA)
 */
__STATIC_FORCEINLINE void __set_ICPFMVAC(uint32_t value)
{
  __set_CP(15, 0, value, 7, 13, 1);
}


/** \brief  Set DCCIMVAC

  Clean and invalidate DCache entry (MVA)
 */
__STATIC_FORCEINLINE void __set_DCCIMVAC(uint32_t value)
{
  __set_CP(15, 0, value, 7, 14, 1);
}

/** \brief  Set DCTCI

  Test and clean DCache, setting Z in CPSR to 1 when the cache contains no dirty lines.
  The cache is then invalidated when the entire cache has been cleaned.
 */
__STATIC_FORCEINLINE void __set_DCTCI(void)
{
  __ASM volatile("MRC p15, 0, r15, c7, c14, 3" ::: "memory");
}


/** \brief  Set DCCISW

  Clean and invalidate DCache entry (Set/Way)
 */
__STATIC_FORCEINLINE void __set_DCCISW(uint32_t value)
{
  __set_CP(15, 0, value, 7, 14, 2);
}


//
// c8: TLB Operations Registers
//

/** \brief  Set TLBIALL

  TLB Invalidate All
 */
__STATIC_FORCEINLINE void __set_TLBIALL(uint32_t value)
{
  __set_CP(15, 0, value, 8, 7, 0);
}

/** \brief  Set TLBIMVA

  TLB Invalidate single entry with the given modified virtual address
 */
__STATIC_FORCEINLINE void __set_TLBIMVA(uint32_t value)
{
  __set_CP(15, 0, value, 8, 7, 1);
}

/** \brief  Set TLBIASID

  TLB Invalidate single entry with the given ASID
 */
__STATIC_FORCEINLINE void __set_TLBIASID(uint32_t value)
{
  __set_CP(15, 0, value, 8, 7, 2);
}


//
// c9: Cache Lockdown and TCM Region Registers
//

/** \brief  Get DCLDR
    \return DCache Lockdown Register value
 */
__STATIC_FORCEINLINE uint32_t __get_DCLDR(void)
{
  uint32_t result;
  __get_CP(15, 0, result, 9, 0, 0);
  return result;
}

/** \brief  Set DCLDR
    \param [in]    dcldr  DCache Lockdown Register value to set
 */
__STATIC_FORCEINLINE void __set_DCLDR(uint32_t dcldr)
{
  __set_CP(15, 0, dcldr, 9, 0, 0);
}

/** \brief  Get ICLDR
    \return ICache Lockdown Register value
 */
__STATIC_FORCEINLINE uint32_t __get_ICLDR(void)
{
  uint32_t result;
  __get_CP(15, 0, result, 9, 0, 1);
  return result;
}

/** \brief  Set ICLDR
    \param [in]    dcldr  ICache Lockdown Register value to set
 */
__STATIC_FORCEINLINE void __set_ICLDR(uint32_t icldr)
{
  __set_CP(15, 0, icldr, 9, 0, 1);
}

/** \brief  Get DTCMRR
    \return Data TCM Region Register value
 */
__STATIC_FORCEINLINE uint32_t __get_DTCMRR(void)
{
  uint32_t result;
  __get_CP(15, 0, result, 9, 1, 0);
  return result;
}

/** \brief  Set DTCMRR
    \param [in]    rr  Data TCM Region Register value to set
 */
__STATIC_FORCEINLINE void __set_DTCMRR(uint32_t rr)
{
  __set_CP(15, 0, rr, 9, 1, 0);
}

/** \brief  Get ITCMRR
    \return Instruction TCM Region Register value
 */
__STATIC_FORCEINLINE uint32_t __get_ITCMRR(void)
{
  uint32_t result;
  __get_CP(15, 0, result, 9, 1, 1);
  return result;
}

/** \brief  Set ITCMRR
    \param [in]    rr  Instruction TCM Region Register value to set
 */
__STATIC_FORCEINLINE void __set_ITCMRR(uint32_t rr)
{
  __set_CP(15, 0, rr, 9, 1, 1);
}


//
// c10: TLB Lockdown Register
//

/** \brief  Get TLBLDR
    \return TLB Lockdown Register value
 */
__STATIC_FORCEINLINE uint32_t __get_TLBLDR(void)
{
  uint32_t result;
  __get_CP(15, 0, result, 10, 0, 0);
  return result;
}

/** \brief  Set TLBLDR
    \param [in]    tlbldr  TLB Lockdown Register value to set
 */
__STATIC_FORCEINLINE void __set_TLBLDR(uint32_t tlbldr)
{
  __set_CP(15, 0, tlbldr, 10, 0, 0);
}


//
// c11: Used for L1 DMA on devices that have it.
//

//
// c12: Reserved on ARMv6 and older
//

//
// c13: Fast Context Switch Extension Registers
//

/** \brief  Get FCSEPID
    \return Fast Context Switch Extension Process ID register value
 */
__STATIC_FORCEINLINE uint32_t __get_FCSEPID(void)
{
  uint32_t result;
  __get_CP(15, 0, result, 13, 0, 0);
  return result;
}

/** \brief  Set CTXID
    \param [in]    pid  Fast Context Switch Extension Process ID value to set
 */
__STATIC_FORCEINLINE void __set_FCSEPID(uint32_t pid)
{
  __set_CP(15, 0, pid, 13, 0, 0);
}

/** \brief  Get FCSECTX
    \return Fast Context Switch Extension Context ID register value
 */
__STATIC_FORCEINLINE uint32_t __get_FCSECTX(void)
{
  uint32_t result;
  __get_CP(15, 0, result, 13, 0, 1);
  return result;
}

/** \brief  Set FCSECTX
    \param [in]    ctx  Fast Context Switch Extension Context ID value to set
 */
__STATIC_FORCEINLINE void __set_FCSECTX(uint32_t ctx)
{
  __set_CP(15, 0, ctx, 13, 0, 0);
}


//
// c14: Reserved on ARMv6 and older
//

//
// c15: Implementation-specific Test and Debug Registers
//

#endif /* __ARM_LEGACY_ARM_CP15_H */

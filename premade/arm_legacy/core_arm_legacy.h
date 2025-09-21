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

#ifndef __ARM_LEGACY_CORE_ARM_H_GENERIC
#define __ARM_LEGACY_CORE_ARM_H_GENERIC

#if defined (__clang__)
  #pragma clang system_header   /* treat file as system include file */
#endif

#ifdef __cplusplus
 extern "C" {
#endif

#if defined(__clang__)
#  include "arm_clang.h"
#elif defined(__GNUC__)
#  include "arm_gcc.h"
#else
#  error Unrecognized compiler. Clang and GCC are supported.
#endif

#if defined (__VFP_FP__) && !defined(__SOFTFP__)
  #if defined (__FPU_PRESENT) && (__FPU_PRESENT == 1U)
    #define __FPU_USED       1U
  #else
    #error "Compiler generates FPU instructions for a device without an FPU (check __FPU_PRESENT)"
    #define __FPU_USED       0U
  #endif
#else
  #define __FPU_USED         0U
#endif

#ifdef __cplusplus
}
#endif

#endif /* __ARM_LEGACY_CORE_ARM_H_GENERIC */

#ifndef __ARM_LEGACY_ARM_GENERIC

#ifndef __ARM_LEGACY_CORE_ARM_H_DEPENDANT
#define __ARM_LEGACY_CORE_ARM_H_DEPENDANT

#if defined (__clang__)
  #pragma clang system_header   /* treat file as system include file */
#endif

#ifdef __cplusplus
 extern "C" {
#endif

 /* check device defines and use defaults */
#if defined __CHECK_DEVICE_DEFINES
  #ifndef __FPU_PRESENT
    #define __FPU_PRESENT             0U
    #warning "__FPU_PRESENT not defined in device header file; using default!"
  #endif
#endif

/* IO definitions (access restrictions to peripheral registers) */
#ifdef __cplusplus
  #define   __I     volatile             /*!< \brief Defines 'read only' permissions */
#else
  #define   __I     volatile const       /*!< \brief Defines 'read only' permissions */
#endif
#define     __O     volatile             /*!< \brief Defines 'write only' permissions */
#define     __IO    volatile             /*!< \brief Defines 'read / write' permissions */

/* following defines should be used for structure members */
#define     __IM     volatile const      /*!< \brief Defines 'read only' structure member permissions */
#define     __OM     volatile            /*!< \brief Defines 'write only' structure member permissions */
#define     __IOM    volatile            /*!< \brief Defines 'read / write' structure member permissions */
#define RESERVED(N, T) T RESERVED##N;    // placeholder struct members used for "reserved" areas

 /*******************************************************************************
  *                 Register Abstraction
   Core Registers contain:
   - CPSR
   - CP15 Registers
  ******************************************************************************/

/* Core Register CPSR */
typedef union
{
  struct
  {
    uint32_t M:5;                        /*!< \brief bit:  0.. 4  Mode field */
    uint32_t T:1;                        /*!< \brief bit:      5  Thumb execution state bit */
    uint32_t F:1;                        /*!< \brief bit:      6  FIQ mask bit */
    uint32_t I:1;                        /*!< \brief bit:      7  IRQ mask bit */
    uint32_t A:1;                        /*!< \brief bit:      8  Asynchronous abort mask bit */
    uint32_t E:1;                        /*!< \brief bit:      9  Endianness execution state bit */
    RESERVED(0:6, uint32_t)
    uint32_t GE:4;                       /*!< \brief bit: 16..19  Greater than or Equal flags */
    RESERVED(1:4, uint32_t)
    uint32_t J:1;                        /*!< \brief bit:     24  Jazelle bit */
    RESERVED(2:2, uint32_t)
    uint32_t Q:1;                        /*!< \brief bit:     27  Saturation condition flag */
    uint32_t V:1;                        /*!< \brief bit:     28  Overflow condition code flag */
    uint32_t C:1;                        /*!< \brief bit:     29  Carry condition code flag */
    uint32_t Z:1;                        /*!< \brief bit:     30  Zero condition code flag */
    uint32_t N:1;                        /*!< \brief bit:     31  Negative condition code flag */
  } b;                                   /*!< \brief Structure used for bit  access */
  uint32_t w;                            /*!< \brief Type      used for word access */
} CPSR_Type;

/* CPSR Register Definitions */
#define CPSR_N_Pos                       31U                                    /*!< \brief CPSR: N Position */
#define CPSR_N_Msk                       (1UL << CPSR_N_Pos)                    /*!< \brief CPSR: N Mask */

#define CPSR_Z_Pos                       30U                                    /*!< \brief CPSR: Z Position */
#define CPSR_Z_Msk                       (1UL << CPSR_Z_Pos)                    /*!< \brief CPSR: Z Mask */

#define CPSR_C_Pos                       29U                                    /*!< \brief CPSR: C Position */
#define CPSR_C_Msk                       (1UL << CPSR_C_Pos)                    /*!< \brief CPSR: C Mask */

#define CPSR_V_Pos                       28U                                    /*!< \brief CPSR: V Position */
#define CPSR_V_Msk                       (1UL << CPSR_V_Pos)                    /*!< \brief CPSR: V Mask */

#define CPSR_Q_Pos                       27U                                    /*!< \brief CPSR: Q Position */
#define CPSR_Q_Msk                       (1UL << CPSR_Q_Pos)                    /*!< \brief CPSR: Q Mask */

#define CPSR_J_Pos                       24U                                    /*!< \brief CPSR: J Position */
#define CPSR_J_Msk                       (1UL << CPSR_J_Pos)                    /*!< \brief CPSR: J Mask */

#define CPSR_GE_Pos                      16U                                    /*!< \brief CPSR: GE Position */
#define CPSR_GE_Msk                      (0xFUL << CPSR_GE_Pos)                 /*!< \brief CPSR: GE Mask */

#define CPSR_E_Pos                       9U                                     /*!< \brief CPSR: E Position */
#define CPSR_E_Msk                       (1UL << CPSR_E_Pos)                    /*!< \brief CPSR: E Mask */

#define CPSR_A_Pos                       8U                                     /*!< \brief CPSR: A Position */
#define CPSR_A_Msk                       (1UL << CPSR_A_Pos)                    /*!< \brief CPSR: A Mask */

#define CPSR_I_Pos                       7U                                     /*!< \brief CPSR: I Position */
#define CPSR_I_Msk                       (1UL << CPSR_I_Pos)                    /*!< \brief CPSR: I Mask */

#define CPSR_F_Pos                       6U                                     /*!< \brief CPSR: F Position */
#define CPSR_F_Msk                       (1UL << CPSR_F_Pos)                    /*!< \brief CPSR: F Mask */

#define CPSR_T_Pos                       5U                                     /*!< \brief CPSR: T Position */
#define CPSR_T_Msk                       (1UL << CPSR_T_Pos)                    /*!< \brief CPSR: T Mask */

#define CPSR_M_Pos                       0U                                     /*!< \brief CPSR: M Position */
#define CPSR_M_Msk                       (0x1FUL << CPSR_M_Pos)                 /*!< \brief CPSR: M Mask */

#define CPSR_M_USR                       0x10U                                  /*!< \brief CPSR: M User mode (PL0) */
#define CPSR_M_FIQ                       0x11U                                  /*!< \brief CPSR: M Fast Interrupt mode (PL1) */
#define CPSR_M_IRQ                       0x12U                                  /*!< \brief CPSR: M Interrupt mode (PL1) */
#define CPSR_M_SVC                       0x13U                                  /*!< \brief CPSR: M Supervisor mode (PL1) */
#define CPSR_M_ABT                       0x17U                                  /*!< \brief CPSR: M Abort mode (PL1) */
#define CPSR_M_UND                       0x1BU                                  /*!< \brief CPSR: M Undefined mode (PL1) */
#define CPSR_M_SYS                       0x1FU                                  /*!< \brief CPSR: M System mode (PL1) */


/* CP15 Register SCTLR */
/* Some bits are used only on ARMv5 and older and others are supported on only ARMv6. Consult the
   Techinical Reference Manual for the CPU in your device (such as ARM926EJ-S) to see which bits
   are used. */
typedef union
{
  struct
  {
    uint32_t M:1;                        /*!< \brief bit:     0  MMU enable */
    uint32_t A:1;                        /*!< \brief bit:     1  Alignment check enable */
    uint32_t C:1;                        /*!< \brief bit:     2  Cache enable */
    uint32_t W:1;                        /*!< \brief bit:     3  Write buffer enable */
    uint32_t P:1;                        /*!< \brief bit:     4  Exception handlers use 32-bit mode */
    uint32_t D:1;                        /*!< \brief bit:     5  32-bit address exception checking */
    uint32_t L:1;                        /*!< \brief bit:     6  Enable late abort model */
    uint32_t B:1;                        /*!< \brief bit:     7  Endianness model */
    uint32_t S:1;                        /*!< \brief bit:     8  System protection bit */
    uint32_t R:1;                        /*!< \brief bit:     9  ROM protection bit */
    uint32_t F:1;                        /*!< \brief bit:    10  Implementation defined */
    uint32_t Z:1;                        /*!< \brief bit:    11  Branch prediction enable */
    uint32_t I:1;                        /*!< \brief bit:    12  Instruction cache enable */
    uint32_t V:1;                        /*!< \brief bit:    13  Vectors bit */
    uint32_t RR:1;                       /*!< \brief bit:    14  Round Robin select */
    uint32_t L4:1;                       /*!< \brief bit:    15  ARMv5T Thumb interworking */
    RESERVED(0:5, uint32_t)
    uint32_t FI:1;                       /*!< \brief bit:    21  Fast interrupts configuration enable */
    uint32_t U:1;                        /*!< \brief bit:    22  Alignment model */
    uint32_t XP:1;                       /*!< \brief bit:    23  Disable extended page tables */
    uint32_t VE:1;                       /*!< \brief bit:    24  Interrupt Vectors Enable */
    uint32_t EE:1;                       /*!< \brief bit:    25  Exception Endianness */
    uint32_t L2:1;                       /*!< \brief bit:    26  L2 cache enable */
    RESERVED(1:5, uint32_t)
  } b;                                   /*!< \brief Structure used for bit  access */
  uint32_t w;                            /*!< \brief Type      used for word access */
} SCTLR_Type;

#define SCTLR_L2_Pos                     26U                                    /*!< \brief SCTLR: L2 Position */
#define SCTLR_L2_Msk                     (1UL << SCTLR_L2_Pos)                  /*!< \brief SCTLR: L2 Mask */

#define SCTLR_EE_Pos                     25U                                    /*!< \brief SCTLR: EE Position */
#define SCTLR_EE_Msk                     (1UL << SCTLR_EE_Pos)                  /*!< \brief SCTLR: EE Mask */

#define SCTLR_VE_Pos                     24U                                    /*!< \brief SCTLR: VE Position */
#define SCTLR_VE_Msk                     (1UL << SCTLR_VE_Pos)                  /*!< \brief SCTLR: VE Mask */

#define SCTLR_XP_Pos                     23U                                    /*!< \brief SCTLR: XP Position */
#define SCTLR_XP_Msk                     (1UL << SCTLR_XP_Pos)                  /*!< \brief SCTLR: XP Mask */

#define SCTLR_U_Pos                      22U                                    /*!< \brief SCTLR: U Position */
#define SCTLR_U_Msk                      (1UL << SCTLR_U_Pos)                   /*!< \brief SCTLR: U Mask */

#define SCTLR_FI_Pos                     21U                                    /*!< \brief SCTLR: FI Position */
#define SCTLR_FI_Msk                     (1UL << SCTLR_FI_Pos)                  /*!< \brief SCTLR: FI Mask */

#define SCTLR_L4_Pos                     15U                                    /*!< \brief SCTLR: L4 Position */
#define SCTLR_L4_Msk                     (1UL << SCTLR_L4_Pos)                  /*!< \brief SCTLR: L4 Mask */

#define SCTLR_RR_Pos                     14U                                    /*!< \brief SCTLR: RR Position */
#define SCTLR_RR_Msk                     (1UL << SCTLR_RR_Pos)                  /*!< \brief SCTLR: RR Mask */

#define SCTLR_V_Pos                      13U                                    /*!< \brief SCTLR: V Position */
#define SCTLR_V_Msk                      (1UL << SCTLR_V_Pos)                   /*!< \brief SCTLR: V Mask */

#define SCTLR_I_Pos                      12U                                    /*!< \brief SCTLR: I Position */
#define SCTLR_I_Msk                      (1UL << SCTLR_I_Pos)                   /*!< \brief SCTLR: I Mask */

#define SCTLR_Z_Pos                      11U                                    /*!< \brief SCTLR: Z Position */
#define SCTLR_Z_Msk                      (1UL << SCTLR_Z_Pos)                   /*!< \brief SCTLR: Z Mask */

#define SCTLR_F_Pos                      10U                                    /*!< \brief SCTLR: F Position */
#define SCTLR_F_Msk                      (1UL << SCTLR_F_Pos)                   /*!< \brief SCTLR: F Mask */

#define SCTLR_R_Pos                      9U                                     /*!< \brief SCTLR: R Position */
#define SCTLR_R_Msk                      (1UL << SCTLR_R_Pos)                   /*!< \brief SCTLR: R Mask */

#define SCTLR_S_Pos                      8U                                     /*!< \brief SCTLR: S Position */
#define SCTLR_S_Msk                      (1UL << SCTLR_S_Pos)                   /*!< \brief SCTLR: S Mask */

#define SCTLR_B_Pos                      7U                                     /*!< \brief SCTLR: B Position */
#define SCTLR_B_Msk                      (1UL << SCTLR_B_Pos)                   /*!< \brief SCTLR: B Mask */

#define SCTLR_L_Pos                      6U                                     /*!< \brief SCTLR: L Position */
#define SCTLR_L_Msk                      (1UL << SCTLR_L_Pos)                   /*!< \brief SCTLR: L Mask */

#define SCTLR_D_Pos                      5U                                     /*!< \brief SCTLR: D Position */
#define SCTLR_D_Msk                      (1UL << SCTLR_D_Pos)                   /*!< \brief SCTLR: D Mask */

#define SCTLR_P_Pos                      4U                                     /*!< \brief SCTLR: P Position */
#define SCTLR_P_Msk                      (1UL << SCTLR_P_Pos)                   /*!< \brief SCTLR: P Mask */

#define SCTLR_W_Pos                      3U                                     /*!< \brief SCTLR: W Position */
#define SCTLR_W_Msk                      (1UL << SCTLR_W_Pos)                   /*!< \brief SCTLR: W Mask */

#define SCTLR_C_Pos                      2U                                     /*!< \brief SCTLR: C Position */
#define SCTLR_C_Msk                      (1UL << SCTLR_C_Pos)                   /*!< \brief SCTLR: C Mask */

#define SCTLR_A_Pos                      1U                                     /*!< \brief SCTLR: A Position */
#define SCTLR_A_Msk                      (1UL << SCTLR_A_Pos)                   /*!< \brief SCTLR: A Mask */

#define SCTLR_M_Pos                      0U                                     /*!< \brief SCTLR: M Position */
#define SCTLR_M_Msk                      (1UL << SCTLR_M_Pos)                   /*!< \brief SCTLR: M Mask */


/* CP15 Register ACTLR */
/* The contents of this are IMPLEMENTATION DEFINED on ARMv6 and older. */


/* CP15 Register CPACR */
/* This may not be present if you have an ARMv5 or older device. */
typedef union
{
  struct
  {
    uint32_t CP0:2;                      /*!< \brief bit:  0..1  Access rights for coprocessor 0 */
    uint32_t CP1:2;                      /*!< \brief bit:  2..3  Access rights for coprocessor 1 */
    uint32_t CP2:2;                      /*!< \brief bit:  4..5  Access rights for coprocessor 2 */
    uint32_t CP3:2;                      /*!< \brief bit:  6..7  Access rights for coprocessor 3 */
    uint32_t CP4:2;                      /*!< \brief bit:  8..9  Access rights for coprocessor 4 */
    uint32_t CP5:2;                      /*!< \brief bit:10..11  Access rights for coprocessor 5 */
    uint32_t CP6:2;                      /*!< \brief bit:12..13  Access rights for coprocessor 6 */
    uint32_t CP7:2;                      /*!< \brief bit:14..15  Access rights for coprocessor 7 */
    uint32_t CP8:2;                      /*!< \brief bit:16..17  Access rights for coprocessor 8 */
    uint32_t CP9:2;                      /*!< \brief bit:18..19  Access rights for coprocessor 9 */
    uint32_t CP10:2;                     /*!< \brief bit:20..21  Access rights for coprocessor 10 */
    uint32_t CP11:2;                     /*!< \brief bit:22..23  Access rights for coprocessor 11 */
    uint32_t CP12:2;                     /*!< \brief bit:24..25  Access rights for coprocessor 12 */
    uint32_t CP13:2;                     /*!< \brief bit:26..27  Access rights for coprocessor 13 */
    RESERVED(0:4, uint32_t)
  } b;                                   /*!< \brief Structure used for bit  access */
  uint32_t w;                            /*!< \brief Type      used for word access */
} CPACR_Type;

#define CPACR_CP_Pos_(n)                 (n*2U)                                 /*!< \brief CPACR: CPn Position */
#define CPACR_CP_Msk_(n)                 (3UL << CPACR_CP_Pos_(n))              /*!< \brief CPACR: CPn Mask */

#define CPACR_CP_NA                      0U                                     /*!< \brief CPACR CPn field: Access denied. */
#define CPACR_CP_PL1                     1U                                     /*!< \brief CPACR CPn field: Accessible from PL1 only. */
#define CPACR_CP_FA                      3U                                     /*!< \brief CPACR CPn field: Full access. */


/* CP15 Register DFSR */
typedef union
{
  struct
  {
    uint32_t FS0:4;                      /*!< \brief bit: 0.. 3  Fault Status bits bit 0-3 */
    uint32_t Domain:4;                   /*!< \brief bit: 4.. 7  Fault on which domain */
    RESERVED(0:2, uint32_t)
    uint32_t FS1:1;                      /*!< \brief bit:    10  Fault Status bits bit 4 */
    uint32_t WR:1;                       /*!< \brief bit:    11  Write bit */
    RESERVED(1:20, uint32_t)
  } b;                                   /*!< \brief Structure used for bit access  */
  uint32_t w;                            /*!< \brief Type      used for word access */
} DFSR_Type;

#define DFSR_WR_Pos                      11U                                    /*!< \brief DFSR: WR Position */
#define DFSR_WR_Msk                      (1UL << DFSR_WR_Pos)                   /*!< \brief DFSR: WR Mask */

#define DFSR_FS1_Pos                     10U                                    /*!< \brief DFSR: FS1 Position */
#define DFSR_FS1_Msk                     (1UL << DFSR_FS1_Pos)                  /*!< \brief DFSR: FS1 Mask */

#define DFSR_Domain_Pos                  4U                                     /*!< \brief DFSR: Domain Position */
#define DFSR_Domain_Msk                  (0xFUL << DFSR_Domain_Pos)             /*!< \brief DFSR: Domain Mask */

#define DFSR_FS0_Pos                     0U                                     /*!< \brief DFSR: FS0 Position */
#define DFSR_FS0_Msk                     (0xFUL << DFSR_FS0_Pos)                /*!< \brief DFSR: FS0 Mask */

#define DFSR_STATUS_Pos                  0U                                     /*!< \brief DFSR: STATUS Position */
#define DFSR_STATUS_Msk                  (0x3FUL << DFSR_STATUS_Pos)            /*!< \brief DFSR: STATUS Mask */


/* CP15 Register IFSR */
typedef union
{
  struct
  {
    uint32_t FS0:4;                      /*!< \brief bit: 0.. 3  Fault Status bits bit 0-3 */
    RESERVED(0:6, uint32_t)
    uint32_t FS1:1;                      /*!< \brief bit:    10  Fault Status bits bit 4 */
    RESERVED(1:21, uint32_t)
  } b;                                   /*!< \brief Structure used for bit access  */
  uint32_t w;                            /*!< \brief Type      used for word access */
} IFSR_Type;

#define IFSR_FS1_Pos                     10U                                    /*!< \brief IFSR: FS1 Position */
#define IFSR_FS1_Msk                     (1UL << IFSR_FS1_Pos)                  /*!< \brief IFSR: FS1 Mask */

#define IFSR_FS0_Pos                     0U                                     /*!< \brief IFSR: FS0 Position */
#define IFSR_FS0_Msk                     (0xFUL << IFSR_FS0_Pos)                /*!< \brief IFSR: FS0 Mask */

#define IFSR_STATUS_Pos                  0U                                     /*!< \brief IFSR: STATUS Position */
#define IFSR_STATUS_Msk                  (0x3FUL << IFSR_STATUS_Pos)            /*!< \brief IFSR: STATUS Mask */


/* CP15 DACR Register */
#define DACR_D_Pos_(n)                   (2U*n)                                 /*!< \brief DACR: Dn Position */
#define DACR_D_Msk_(n)                   (3UL << DACR_D_Pos_(n))                /*!< \brief DACR: Dn Mask */
#define DACR_Dn_NOACCESS                 0U                                     /*!< \brief DACR Dn field: No access */
#define DACR_Dn_CLIENT                   1U                                     /*!< \brief DACR Dn field: Client */
#define DACR_Dn_MANAGER                  3U                                     /*!< \brief DACR Dn field: Manager */


/**
  \brief     Mask and shift a bit field value for use in a register bit range.
  \param [in] field  Name of the register bit field.
  \param [in] value  Value of the bit field. This parameter is interpreted as an uint32_t type.
  \return           Masked and shifted value.
*/
#define _VAL2FLD(field, value)    (((uint32_t)(value) << field ## _Pos) & field ## _Msk)

/**
  \brief     Mask and shift a register value to extract a bit field value.
  \param [in] field  Name of the register bit field.
  \param [in] value  Value of register. This parameter is interpreted as an uint32_t type.
  \return           Masked and shifted bit field value.
*/
#define _FLD2VAL(field, value)    (((uint32_t)(value) & field ## _Msk) >> field ## _Pos)


 /*******************************************************************************
  *                Hardware Abstraction Layer
   Core Function Interface contains:
   - L1 Cache Functions
   - MMU Functions
  ******************************************************************************/

/* ##########################  L1 Cache functions  ################################# */

/** \brief Enable Caches by setting I and C bits in SCTLR register.
*/
__STATIC_FORCEINLINE void L1C_EnableCaches(void) {
  __set_SCTLR( __get_SCTLR() | SCTLR_I_Msk | SCTLR_C_Msk);
  __ISB();
}

/** \brief Disable Caches by clearing I and C bits in SCTLR register.
*/
__STATIC_FORCEINLINE void L1C_DisableCaches(void) {
  __set_SCTLR( __get_SCTLR() & (~SCTLR_I_Msk) & (~SCTLR_C_Msk));
  __ISB();
}

/** \brief  Enable Branch Prediction by setting Z bit in SCTLR register.
*/
__STATIC_FORCEINLINE void L1C_EnableBTAC(void) {
  __set_SCTLR( __get_SCTLR() | SCTLR_Z_Msk);
  __ISB();
}

/** \brief  Disable Branch Prediction by clearing Z bit in SCTLR register.
*/
__STATIC_FORCEINLINE void L1C_DisableBTAC(void) {
  __set_SCTLR( __get_SCTLR() & (~SCTLR_Z_Msk));
  __ISB();
}

/** \brief  Invalidate entire branch predictor array
*/
__STATIC_FORCEINLINE void L1C_InvalidateBTAC(void) {
  __set_BPIALL(0);
  __DSB();     //ensure completion of the invalidation
  __ISB();     //ensure instruction fetch path sees new state
}

/** \brief  Clean instruction cache line by address.
* \param [in] va Pointer to instructions to clear the cache for.
*/
__STATIC_FORCEINLINE void L1C_InvalidateICacheMVA(void *va) {
  __set_ICIMVAC((uint32_t)va);
  __DSB();     //ensure completion of the invalidation
  __ISB();     //ensure instruction fetch path sees new I cache state
}

/** \brief  Invalidate the whole instruction cache
*/
__STATIC_FORCEINLINE void L1C_InvalidateICacheAll(void) {
  __set_ICIALLU(0);
  __DSB();     //ensure completion of the invalidation
  __ISB();     //ensure instruction fetch path sees new I cache state
}

/** \brief  Clean data cache line by address.
* \param [in] va Pointer to data to clear the cache for.
*/
__STATIC_FORCEINLINE void L1C_CleanDCacheMVA(void *va) {
  __set_DCCMVAC((uint32_t)va);
  __DMB();     //ensure the ordering of data cache maintenance operations and their effects
}

/** \brief  Invalidate data cache line by address.
* \param [in] va Pointer to data to invalidate the cache for.
*/
__STATIC_FORCEINLINE void L1C_InvalidateDCacheMVA(void *va) {
  __set_DCIMVAC((uint32_t)va);
  __DMB();     //ensure the ordering of data cache maintenance operations and their effects
}

/** \brief  Clean and Invalidate data cache by address.
* \param [in] va Pointer to data to invalidate the cache for.
*/
__STATIC_FORCEINLINE void L1C_CleanInvalidateDCacheMVA(void *va) {
  __set_DCCIMVAC((uint32_t)va);
  __DMB();     //ensure the ordering of data cache maintenance operations and their effects
}

/** \brief  Apply cache maintenance to given cache level.
    \param [in] maint 0 - invalidate, 1 - clean, otherwise - invalidate and clean
 */
__STATIC_FORCEINLINE void __L1C_MaintainDCacheSetWay(uint32_t maint)
{
  // This matches the layout of the Dsize and Isize fields in the CP15 Cache Type register. 
  union
  {
    struct
    {
      uint16_t len:2;             // bytes per cache line = 1 << (len+3)
      uint16_t m:1;               // affects associativity calculation
      uint16_t assoc:3;           // associativity = 1 << assoc   (increased by half if m==1)
      uint16_t size:4;            // total cache size in bytes = 1 << (9 + size)
      uint16_t zero:1;            // keep as zero
      uint16_t p:1;               // used on ARMv6; not needed here
      uint16_t unused:4;
    };
    uint16_t val;
  } dsize;

  dsize.val = (__get_CACHETYPE() >> 12) & 0xFFF;

  uint32_t num_ways = 1 << dsize.assoc;
  if(dsize.m)
    num_ways += (num_ways >> 1);

  uint32_t num_sets = 1 << (dsize.size + 6 - dsize.assoc - dsize.len);

  // Cache operations that use sets and ways have an odd format. The way to use occupies the MSbits
  // of the value and so is shifted up by (32 - log2(associativity)). The set to use is shifted up
  // by log2(linesize).
  uint32_t shift_way = 32U - dsize.assoc - dsize.m;
  uint32_t shift_set = dsize.len + 3;

  for(int32_t way = num_ways-1; way >= 0; way--)
  {
    for(int32_t set = num_sets-1; set >= 0; set--)
    {
      uint32_t sw_value = (((uint32_t)way) << shift_way) | (((uint32_t)set) << shift_set);
      switch (maint)
      {
        case 0U: __set_DCISW(sw_value);  break;
        case 1U: __set_DCCSW(sw_value);  break;
        default: __set_DCCISW(sw_value); break;
      }
    }
  }
  __DMB();    //ensure the ordering of data cache maintenance operations and their effects
}

/** \brief  Invalidate the whole data cache.
 */
__STATIC_FORCEINLINE void L1C_InvalidateDCacheAll(void) {
  __set_DCIALLU(0);
  __DMB();    //ensure the ordering of data cache maintenance operations and their effects
}

/** \brief  Clean the whole data cache.
 */
__STATIC_FORCEINLINE void L1C_CleanDCacheAll(void) {
  __L1C_MaintainDCacheSetWay(1);
}

/** \brief  Clean and invalidate the whole data cache.
 */
__STATIC_FORCEINLINE void L1C_CleanInvalidateDCacheAll(void) {
  __L1C_MaintainDCacheSetWay(2);
}

/** \brief  Invalidate the whole instruction and data caches
 */
__STATIC_FORCEINLINE void L1C_InvalidateIandDCacheAll(void) {
  __set_IDCIALLU(0);
  __DSB();     //ensure completion of the invalidation
  __ISB();     //ensure instruction fetch path sees new cache states
}


/* ##########################  MMU functions  ###################################### */

//
// Section Descriptors
//

// Indicates this is a section descriptor
#define SECTION_DESCRIPTOR          (0x2)
#define SECTION_MASK                (0xFFFFFFFC)

// Bufferable
#define SECTION_B_MASK              (0xFFFFFFFB)
#define SECTION_B_SHIFT             (2)

// Cacheable
#define SECTION_C_MASK              (0xFFFFFFF7)
#define SECTION_C_SHIFT             (3)

// ARMv6: eXecute Never flag.
// Older: Implementation defined, check the Technical Reference Manual for your CPU.
#define SECTION_IMP_XN_MASK         (0xFFFFFFEF)
#define SECTION_IMP_XN_SHIFT        (4)
#define SECTION_XN_MASK             (0xFFFFFFEF)
#define SECTION_XN_SHIFT            (4)

// Memory domain
#define SECTION_DOMAIN_MASK         (0xFFFFFE1F)
#define SECTION_DOMAIN_SHIFT        (5)

// Implementation defined, check the Technical Reference Manual for your CPU.
#define SECTION_IMP_MASK            (0xFFFFFDFF)
#define SECTION_IMP_SHIFT           (9)

// Access permissions
#define SECTION_AP_MASK             (0xFFFFF3FF)
#define SECTION_AP_SHIFT            (10)

// ARMv6 only: Type EXtension field.
#define SECTION_TEXCB_MASK          (0xFFFF8FF3)
#define SECTION_TEX_MASK            (0xFFFF8FFF)
#define SECTION_TEX_SHIFT           (12)
#define SECTION_TEX0_SHIFT          (12)
#define SECTION_TEX1_SHIFT          (13)
#define SECTION_TEX2_SHIFT          (14)

// ARMv6 only: replaces the S and R bits that were in the SCTRL register in ARMv5 and older.
#define SECTION_APX_MASK            (0xFFFF7FFF)
#define SECTION_APX_SHIFT           (15)

// ARMv6 only: Set if this is "shared" memory.
#define SECTION_S_MASK              (0xFFFEFFFF)
#define SECTION_S_SHIFT             (16)

// ARMv6 only: 0 means this is a global descriptor; 1 means this is process-specific.
#define SECTION_NG_MASK             (0xFFFDFFFF)
#define SECTION_NG_SHIFT            (17)

// ARMv6 only: Set if this descriptor is for a supersection.
#define SECTION_SUPERSECT_MASK      (0xFFFBFFFF)
#define SECTION_SUPERSECT_SHIFT     (18)


//
// Page Level 1 Descriptors
//

// Indicates this is a coarse page descriptor
#define COARSE_PAGE_L1_DESCRIPTOR   (0x1)
#define COARSE_PAGE_L1_MASK         (0xFFFFFFFC)
#define PAGE_L1_DESCRIPTOR          (0x1)
#define PAGE_L1_MASK                (0xFFFFFFFC)

// Implementation defined
#define COARSE_PAGE_IMP_MASK        (0xFFFFFFE3)
#define COARSE_PAGE_IMP_SHIFT       (2)
#define PAGE_IMP_MASK               (0xFFFFFFE3)
#define PAGE_IMP_SHIFT              (2)

// Memory domain
#define COARSE_PAGE_DOMAIN_MASK     (0xFFFFFE1F)
#define COARSE_PAGE_DOMAIN_SHIFT    (5)
#define PAGE_DOMAIN_MASK            (0xFFFFFE1F)
#define PAGE_DOMAIN_SHIFT           (5)


// Indicates this is a fine page descriptor
// Fine page descriptors are available in ARMv5; not for ARMv6. 
#define FINE_PAGE_L1_DESCRIPTOR     (0x3)
#define FINE_PAGE_L1_MASK           (0xFFFFFFFC)

// Implementation defined
#define FINE_PAGE_IMP_MASK          (0xFFFFFFE3)
#define FINE_PAGE_IMP_SHIFT         (2)

// Memory domain
#define FINE_PAGE_DOMAIN_MASK       (0xFFFFFE1F)
#define FINE_PAGE_DOMAIN_SHIFT      (5)

//
// Page Level 2 Descriptors
//

// This is for second-level descriptors for 64kB "large" pages
#define PAGE_L2_64K_DESC            (0x1)
#define PAGE_L2_64K_MASK            (0xFFFFFFFC)

// This is for second-level descriptors for 4kB "small" pages
#define PAGE_L2_4K_DESC             (0x2)
#define PAGE_L2_4K_MASK             (0xFFFFFFFC)

// This is for second-level descriptors for 1kB "tiny" pages
// Tiny pages are available in ARMv5; not ARMv6.
#define PAGE_L2_1K_DESC             (0x3)
#define PAGE_L2_1K_MASK             (0xFFFFFFFC)

// Bufferable
#define PAGE_B_MASK                 (0xFFFFFFFB)
#define PAGE_B_SHIFT                (2)

// Cacheable
#define PAGE_C_MASK                 (0xFFFFFFF7)
#define PAGE_C_SHIFT                (3)

// Access Permissions
#define PAGE_AP_MASK                (0xFFFFFFCF)
#define PAGE_AP_SHIFT               (4)
#define PAGE_AP0_MASK               (0xFFFFFFCF)
#define PAGE_AP0_SHIFT              (4)
#define PAGE_AP1_MASK               (0xFFFFFF3F)
#define PAGE_AP1_SHIFT              (6)
#define PAGE_AP2_MASK               (0xFFFFFCFF)
#define PAGE_AP2_SHIFT              (8)
#define PAGE_AP3_MASK               (0xFFFFF3FF)
#define PAGE_AP3_SHIFT              (10)

// ARMv6 only: Type EXtension field for 64kB pages.
#define PAGE_64K_TEXCB_MASK          (0xFFFF8FF3)
#define PAGE_64K_TEX_MASK            (0xFFFF8FFF)
#define PAGE_64K_TEX_SHIFT           (12)
#define PAGE_64K_TEX0_SHIFT          (12)
#define PAGE_64K_TEX1_SHIFT          (13)
#define PAGE_64K_TEX2_SHIFT          (14)

// ARMv6 only: Type EXtension field for 4kB pages.
#define PAGE_4K_TEXCB_MASK          (0xFFFFFE33)
#define PAGE_4K_TEX_MASK            (0xFFFFFE3F)
#define PAGE_4K_TEX_SHIFT           (6)
#define PAGE_4K_TEX0_SHIFT          (6)
#define PAGE_4K_TEX1_SHIFT          (7)
#define PAGE_4K_TEX2_SHIFT          (8)

// ARMv6 only: eXecute Never flag for 4kB and 64kB pages.
#define PAGE_XN_4K_MASK             (0xFFFFFFFE)
#define PAGE_XN_4K_SHIFT            (0)
#define PAGE_XN_64K_MASK            (0xFFFF7FFF)
#define PAGE_XN_64K_SHIFT           (15)

// ARMv6 only: replaces the S and R bits that were in the SCTRL register in ARMv5 and older.
#define PAGE_APX_MASK               (0xFFFFFDFF)
#define PAGE_APX_SHIFT              (9)

// ARMv6 only: Set if this is "shared" memory.
#define PAGE_S_MASK                 (0xFFFFFBFF)
#define PAGE_S_SHIFT                (10)

// ARMv6 only: 0 means this is a global descriptor; 1 means this is process-specific.
#define PAGE_NG_MASK                (0xFFFFF7FF)
#define PAGE_NG_SHIFT               (11)

//
// Address offsets
//

#define OFFSET_1M                   (0x00100000)
#define OFFSET_64K                  (0x00010000)
#define OFFSET_4K                   (0x00001000)
#define OFFSET_1K                   (0x00000400)

//
// Fault desciptor
// This can be used at the first or second levels.
//

// Accessing this section or page will generate a fault.
#define DESCRIPTOR_FAULT            (0x00000000)


/** \brief  Create a 1MB Section

  \param [in]               ttb  Translation table base address
  \param [in]      base_address  Section base address
  \param [in]             count  Number of sections to create
  \param [in]     descriptor_l1  L1 descriptor (region attributes)

*/
__STATIC_INLINE void MMU_TTSection(uint32_t *ttb, uint32_t base_address, uint32_t count, uint32_t descriptor_l1)
{
  uint32_t offset;
  uint32_t entry;
  uint32_t i;

  offset = base_address >> 20;
  entry  = (base_address & 0xFFF00000) | descriptor_l1;

  //4 bytes aligned
  ttb = ttb + offset;

  for (i = 0; i < count; i++ )
  {
    //4 bytes aligned
    *ttb++ = entry;
    entry += OFFSET_1M;
  }
}

/** \brief  Create a 1k page entry

  \param [in]               ttb  L1 table base address
  \param [in]      base_address  1k base address
  \param [in]             count  Number of 1k pages to create
  \param [in]     descriptor_l1  L1 descriptor (region attributes)
  \param [in]            ttb_l2  L2 table base address
  \param [in]     descriptor_l2  L2 descriptor (region attributes)

*/
__STATIC_INLINE void MMU_TTPage1k(uint32_t *ttb, uint32_t base_address, uint32_t count, uint32_t descriptor_l1, uint32_t *ttb_l2, uint32_t descriptor_l2 )
{

  uint32_t offset, offset2;
  uint32_t entry, entry2;
  uint32_t i;

  offset = base_address >> 20;
  entry  = ((int)ttb_l2 & 0xFFFFF000) | descriptor_l1;

  //4 bytes aligned
  ttb += offset;
  //create l1_entry
  *ttb = entry;

  offset2 = (base_address & 0xFFC00) >> 10;
  ttb_l2 += offset2;
  entry2 = (base_address & 0xFFFFFC00) | descriptor_l2;
  for (i = 0; i < count; i++ )
  {
    //4 bytes aligned
    *ttb_l2++ = entry2;
    entry2 += OFFSET_1K;
  }
}

/** \brief  Create a 4k page entry

  \param [in]               ttb  L1 table base address
  \param [in]      base_address  4k base address
  \param [in]             count  Number of 4k pages to create
  \param [in]     descriptor_l1  L1 descriptor (region attributes)
  \param [in]            ttb_l2  L2 table base address
  \param [in]     descriptor_l2  L2 descriptor (region attributes)

*/
__STATIC_INLINE void MMU_TTPage4k(uint32_t *ttb, uint32_t base_address, uint32_t count, uint32_t descriptor_l1, uint32_t *ttb_l2, uint32_t descriptor_l2 )
{

  uint32_t offset, offset2;
  uint32_t entry, entry2;
  uint32_t i;

  offset = base_address >> 20;
  entry  = ((int)ttb_l2 & 0xFFFFFC00) | descriptor_l1;

  //4 bytes aligned
  ttb += offset;
  //create l1_entry
  *ttb = entry;

  offset2 = (base_address & 0xff000) >> 12;
  ttb_l2 += offset2;
  entry2 = (base_address & 0xFFFFF000) | descriptor_l2;
  for (i = 0; i < count; i++ )
  {
    //4 bytes aligned
    *ttb_l2++ = entry2;
    entry2 += OFFSET_4K;
  }
}

/** \brief  Create a 64k page entry

  \param [in]               ttb  L1 table base address
  \param [in]      base_address  64k base address
  \param [in]             count  Number of 64k pages to create
  \param [in]     descriptor_l1  L1 descriptor (region attributes)
  \param [in]            ttb_l2  L2 table base address
  \param [in]     descriptor_l2  L2 descriptor (region attributes)

*/
__STATIC_INLINE void MMU_TTPage64k(uint32_t *ttb, uint32_t base_address, uint32_t count, uint32_t descriptor_l1, uint32_t *ttb_l2, uint32_t descriptor_l2 )
{
  uint32_t offset, offset2;
  uint32_t entry, entry2;
  uint32_t i,j;


  offset = base_address >> 20;
  entry  = ((int)ttb_l2 & 0xFFFFFC00) | descriptor_l1;

  //4 bytes aligned
  ttb += offset;
  //create l1_entry
  *ttb = entry;

  offset2 = (base_address & 0xff000) >> 12;
  ttb_l2 += offset2;
  entry2 = (base_address & 0xFFFF0000) | descriptor_l2;
  for (i = 0; i < count; i++ )
  {
    //create 16 entries
    for (j = 0; j < 16; j++)
    {
      //4 bytes aligned
      *ttb_l2++ = entry2;
    }
    entry2 += OFFSET_64K;
  }
}

/** \brief  Enable MMU
*/
__STATIC_INLINE void MMU_Enable(void)
{
  // Set M bit 0 to enable the MMU
  // Clear A bit to disable strict alignment fault checking
  __set_SCTLR( (__get_SCTLR() & ~(1 << 1)) | 1 );
  __ISB();
}

/** \brief  Disable MMU
*/
__STATIC_INLINE void MMU_Disable(void)
{
  // Clear M bit 0 to disable the MMU
  __set_SCTLR( __get_SCTLR() & ~1);
  __ISB();
}

/** \brief  Invalidate entire unified TLB
*/

__STATIC_INLINE void MMU_InvalidateTLB(void)
{
  __set_TLBIALL(0);
  __DSB();     //ensure completion of the invalidation
  __ISB();     //ensure instruction fetch path sees new state
}


#ifdef __cplusplus
}
#endif

#endif /* __ARM_LEGACY_CORE_ARM_H_DEPENDANT */

#endif /* __ARM_LEGACY_ARM_GENERIC */

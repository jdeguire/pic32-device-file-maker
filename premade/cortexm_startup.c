//{DEST: cortex-m/startup.c}
//{LICENSE: CMSIS}

/* This is the startup code for the PIC32 and SAM Cortex-M devices. This is based on the example
   startup code found in CMSIS 6 at "CMSIS/Core/Template/Device_M/Source/startup_Device.c". A
   major difference, however, is that the device interrupt vectors are not defined here like they
   are in the CMSIS template. Instead, they are defined in their own device-specific files located
   in the "proc/" directory found alongside this file. Splitting these up means that only one
   startup module is needed to handle all devices instead of one per device.

   This will also set up the FPU and caches, if present, and initialize program data.
   */

#include <stdint.h>
#include <which_pic32.h>

/* These are defined in the linker script. These names are aliases CMSIS defines for the
   linker script symbols. */
extern uint32_t __INITIAL_SP;
extern uint32_t __STACK_LIMIT;
#if defined (__ARM_FEATURE_CMSE) && (__ARM_FEATURE_CMSE == 3U)
extern uint32_t __STACK_SEAL;
#endif

extern void _init(void);         // Defined in Musl library at "must/crt/arm/crti.s."
extern int main(void);
extern void exit(int status);

/* Define these to run code during startup.  The _on_reset() function is run almost immediately,
   so the cache and FPU will probably not be usable unless they are enabled in _on_reset().
   The _on_bootstrap() function is run just before main is called and so everything should be
   initialized.
   */
extern void __attribute__((weak, long_call)) _on_reset(void);
extern void __attribute__((weak, long_call)) _on_bootstrap(void);


/* Enable the FPU for devices that have one. This is also used for devices that support the M-Profile
   Vector Extensions because that uses the 16 double-precision FPU registers as 8 128-bit vector
   registers.
 */
void __attribute__((weak)) _EnableFpu(void)
{
#if (defined(__ARM_FP) && (0 != __ARM_FP))  ||  (defined(__ARM_FEATURE_MVE) && (__ARM_FEATURE_MVE > 0))
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
#endif
}

/* Enable the Cortex-M Cache Controller with default values. This is used to supplement Cortex-M
   devices that do not have a CPU cache.
   */
void __attribute__((weak)) _EnableCmccCache(void)
{
#if defined(ID_CMCC)
    CMCC_REGS->CTRL |= CMCC_CTRL_CEN_Msk;
#endif
}

/* Enable the Cortex-M CPU instruction and data caches. This applies to CPUs with built-in caches.
   */
void __attribute__((weak)) _EnableCpuCache(void)
{
    // These invalidate the caches before enabling them.
#if __ICACHE_PRESENT == 1
    SCB_EnableICache();
#endif
#if __DCACHE_PRESENT == 1
    SCB_EnableDCache();
#endif
}

/* Enable branch prediction and the Low Overhead Branch extension if either are present.
 */
void __attribute__((weak)) _EnableBranchCaches(void)
{
#if defined(SCB_CCR_LOB_Msk)
  /* Enable Loop and branch info cache */
  SCB->CCR |= SCB_CCR_LOB_Msk;
#endif
#if defined(SCB_CCR_BP_Msk)
  /* Enable Branch Prediction */
  SCB->CCR |= SCB_CCR_BP_Msk;
#endif
#if defined(SCB_CCR_LOB_Msk) || defined(SCB_CCR_BP_Msk)
  __DSB();
  __ISB();
#endif
}

/* Initialize data found in the .data and .bss sections. This is based on the __cmsis_start()
   function found in "CMSIS/Core/Include/m-profile/cmsis_gcc_m.h".
   */
void __attribute__((weak)) _InitData(void)
{
    typedef struct __copy_table {
        uint32_t const* src;
        uint32_t* dest;
        uint32_t  wlen;
    } __copy_table_t;

    typedef struct __zero_table {
        uint32_t* dest;
        uint32_t  wlen;
    } __zero_table_t;

    // These are defined in the linker script
    extern const __copy_table_t __copy_table_start__;
    extern const __copy_table_t __copy_table_end__;
    extern const __zero_table_t __zero_table_start__;
    extern const __zero_table_t __zero_table_end__;

    // Copy .data sections.
    for(__copy_table_t const* pTable = &__copy_table_start__; pTable < &__copy_table_end__; ++pTable)
    {
        for(uint32_t i = 0u; i < pTable->wlen; ++i)
            pTable->dest[i] = pTable->src[i];
    }

    // Zero out .bss sections.
    for(__zero_table_t const* pTable = &__zero_table_start__; pTable < &__zero_table_end__; ++pTable)
    {
        for(uint32_t i = 0u; i < pTable->wlen; ++i)
            pTable->dest[i] = 0u;
    }
}

/* Call compiler-generated initialization routines for C and C++.
   */
void __attribute__((weak)) _LibcInitArray(void)
{
    // These are defined in the linker script.
    extern void (*__preinit_array_start)(void);
    extern void (*__preinit_array_end)(void);
    extern void (*__init_array_start)(void);
    extern void (*__init_array_end)(void);

    void (**preinit_ptr)(void) = &__preinit_array_start;
    while(preinit_ptr < &__preinit_array_end)
    {
        (*preinit_ptr)();
        ++preinit_ptr;
    }

    _init();

    void (**init_ptr)(void) = &__init_array_start;
    while(init_ptr < &__init_array_end)
    {
        (*init_ptr)();
        ++init_ptr;
    }
}


/* The entry point at which the CPU starts execution. The address of this function is in the vector
   table and the CPU fetches it upon power up or reset.
   */
void __attribute((noreturn)) Reset_Handler(void)
{
    /* Initialize the stack pointer. This is normally done by the CPU on reset by reading the first
       entry in the vector table, but do this in case the vector table is not at address 0x0000. */
    __set_PSP((uint32_t)(&__INITIAL_SP));

    /* Initialize stack limit registers for Armv8-M Main devices. These do nothing for
       older devices. */
    __set_MSPLIM((uint32_t)(&__STACK_LIMIT));
    __set_PSPLIM((uint32_t)(&__STACK_LIMIT));

    /* Add stack sealing for Armv8-M based processors. To use this, copy the default linker script
       for the target device. Update the __STACKSEAL_SIZE near the top and uncomment the ".stackseal"
       section near the end. */
#if defined (__ARM_FEATURE_CMSE) && (__ARM_FEATURE_CMSE == 3U)
    __TZ_set_STACKSEAL_S((uint32_t *)(&__STACK_SEAL));
#endif

    if(_on_reset)
        _on_reset();

    _EnableFpu();
    _EnableCpuCache();
    _EnableBranchCaches();
    _EnableCmccCache();

    /* Set the vector table base address, if supported by this device. */
#ifdef SCB_VTOR_TBLOFF_Msk
    extern const void(*__VECTOR_TABLE[])(void);
    uint32_t vtor_addr = (uint32_t)__VECTOR_TABLE;
    SCB->VTOR = (vtor_addr & SCB_VTOR_TBLOFF_Msk);
#endif

    _InitData();
    _LibcInitArray();

    if(_on_bootstrap)
        _on_bootstrap();

    /* The app is ready to go, call main. */
    exit(main());

#ifdef __DEBUG
    __BKPT(0);
#endif

    /* Nothing left to do but spin here forever. */
    while(1) {}
}
# pic32-device-file-maker
Generate device-specifc files for PIC32 and SAM device (ARM-only for now), like linker scripts
and header files.

This is sort of a port of my **generatePic32SpecificStuff** project. That project uses Java and
is a plugin for MPLAB X to access its internal database. This project will not do that, but will
instead ask you to tell it where the database is. If you have MPLAB X installed, look for a "packs"
directory in its install location or in your user directory for a ".mchp_packs" directory.

The other project was also quite concerned with maintaining a fair amount of compatibility with
Microchip's files. This project is not going to be as concerned with that, at least to start. I
have no plans to use these files with Microcip's XC32 compiler or Harmony framework, so there is
not really a reason to worry about it. This comes with the additional benefit of not having to worry
as much about licenses and the legality of mimicking Microchip's code.

Any similarity to Microchip's device files is either coincidental or the result of functional
requirements. This code, presumably like Microchip's/Atmel's code, uses Arm CMSIS 6 as a template
and so there will probably be a lot of similarities because of that. Find CMSIS 6 on GitHub at
https://github.com/ARM-software/CMSIS_6/tree/main.

If you modify this project, be sure to add your name to the copyright string list in 
"file_makers/strings.py". You will see a comment in there showing where and how to add it.
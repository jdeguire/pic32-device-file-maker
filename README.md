# atdf-device-file-maker
_This project used to be called "pic32-device-file-maker", but I changed it to avoid any trademark
concerns with using "PIC" in the name._

Generate device-specifc files for PIC32 and SAM device (ARM-only for now), like linker scripts
and header files.

## Intro
This app works by parsing special XML files in something called a "device pack". The XML files have
the extension ".atdf"--hence the name of this project--and contain lots of information about a device.

Device packs are files that contain information about a vendor's microcontroller and microprocessor
devices. They also contain things like header files and linker scripts that can be used with that
vendor's development tools. From what I can tell, the idea of device packs came from ARM and their
CMSIS framework. Packs are particularly useful for vendors that use Arm's compiler suite instead of
distributing their own. A vendor needs only to update packs to fix bugs or add new devices instead of
needing to bundle up a whole new distribution of a toolchain.

Microchip uses device packs even though they distribute their own custom builds of GCC under the "XC"
branding. This is probably because Atmel was already doing this when Microchip acquired them in 2016.
The header files and such in Microchip's pack rely on extensions specific to Microchip's toolchains,
which is why this project exists. This is intended to make files that work on regular GCC or Clang.

Any similarity to Microchip's device files is either coincidental or the result of functional
requirements. This code, presumably like Microchip's/Atmel's code, uses Arm CMSIS 6 as a template
and so there will probably be a lot of similarities because of that. Find CMSIS 6 on GitHub at
https://github.com/ARM-software/CMSIS_6/tree/main.

If you modify this project, be sure to add your name to the copyright string list in 
"file_makers/strings.py". You will see a comment in there showing where and how to add it.

## Getting the Packs
You need to find where Microchip's packs are located so you can pass that as a command-line argument
to this app.

The easiest way to handle this is to use the Microchip Pack Downloader script found at
https://github.com/jdeguire/mchp-pack-downloader to download the latest versions of Microchip's packs.
See the README in that project repository for more info, but in short you can simply run it and wait
for it to finish. The pack data will be located in a `packs/` directory created in the same location
as the script file.

If you are not able to use that script for some reason, there are a few other ways to find the packs
you need.

- If you have MPLAB X installed, look for a "packs" directory at the install location. For example,
on Windows this would be `C:/Program Files/MPLAB X/<version>/packs`. On Linux, this would be
`/opt/microchip/mplabx/<version>/packs`.
- MPLAB X can download pack updates for you. Those go into your user or home directory in a 
`.mchp_packs` subdirectory. On Windows, this would be `C:/Users/<you>/.mchp_packs`. On Linux, this
is in your home directory.
- You can also manually download packs from https://packs.download.microchip.com/. This is what the
script mentioned above does. Do this if you need only a few packs or you need specific versions.

If you use MPLAB X to handle the packs, then you probably want to merge those two directories above
into a third location that will contain everything. You can also manually download whatever packs you
need into this location using the URL above. You will probably want to keep this merged directory
somewhere safe as an archive for later use. Your packs directory may contain multiple versions of a
pack. The version of a pack is indicated in its directory structure. This app will try to find and
use the latest version for each device family.

I'm not yet sure how the MPLAB Extensions for VS Code will handle packs, but I presume it'll still
use the `.mchp_packs` location or something similar.

## A Quick Word of Caution
This project uses the default XML parsers in Python, which are vulnerable to certain attacks
relying on XML entities referecing other entities multiple times. Specifically, the attacks are
called "Billion Laughs" and "Quadratic Blowup". Therefore, you should ensure that the packs files
you give to this module are really from Microchip and not some malicious user. See the info here:
https://docs.python.org/3/library/xml.html#module-xml. That page has a link to a package called
"defusedxml" you can use if you want to be safer. You should just need to get it from PIP and
update the import statement for ElementTree in the modules that use it.

## Running the App
This app was written using Python 3.10, so you should try to get at least that version. Slightly
older versions might work, like Python 3.8 or so, but there's no guarantee. You can run the app
from the command-line like so:

`python3 ./atdf-device-file-maker.py <packs_dir>`

This will look for the ".atdf" files in the given "packs_dir" and output the generated files to
your working directory (that is, the directory from which you ran the app). You can optionally change
the ouput directory with the `--output_dir` option. The generated files are always put into a
subdirectory called `atdf-device-files` in your chosen output directory.

This app will create a device-specific configuration file for each device it finds. You would pass
this to Clang with the `--config` option to use your desired device. Use the `--define-macro <macro>`
option to add a macro definition to each device config file. The `<macro>` argument needs to follow
the same convention as Clang's (and GCC's) `-D` option. You can specify this option multiple times
to add multiple macros. If you are running this app through the [buildMchpClang](https://github.com/jdeguire/buildMchpClang)
script, then that will pass macros to this app specifying version numbers of the mchpClang toolset.

This app uses the Python `multiprocess` module to parse the device info files. You can control how
many processes are created to do this using the `--parse-jobs` argument. The default and maximum
allowed is one per CPU.

You can also use `--help` or `-h` to get some help text on the command line or use `--version` to
print a bit of version info.

## Previous Work
This is sort of a port of my old **generatePic32SpecificStuff** project, which you can find here if
you really want it: https://github.com/jdeguire/generatePic32SpecificStuff. That project is no longer
maintained and was a plugin for MPLAB X to access its internal database. This internal database used
other XML files that had the ".edc" extension, also found in the device packs. The EDC files did not
have all of the info I needed and so that project also parsed ATDF files for some info.

The other project was also quite concerned with maintaining a fair amount of compatibility with
Microchip's files. This project is not going to be as concerned with that, at least to start. I
have no plans to use these files with Microcip's XC32 compiler or Harmony framework, so there is
not really a reason to worry about it. This comes with the additional benefit of not having to worry
as much about licenses and the legality of mimicking Microchip's code.

Feel free to look at that project or even take it over if you want. That project does have the
advantage of supporting the PIC32 MIPS devices, which this project will likely never support. That
project also could automatically find all of the files it needed by querying MPLAB X for them. As of
this writing in 2025, MPLAB X is in the process of being replaced by the MPLAB VS Code Extensions set.

## License
This app is covered by the standard 3-clause BSD license. See the LICENSE file in this directory
for the full license text.

The files created by this app are covered under the Apache 2.0 license. A copy of the license is
output along with the generated files in a LICENSE file at the top level of the output directory.
The Apache license is used because that is what Arm's CMSIS framework uses and many of the files
created by this app are based on examples provided in CMSIS.

## Trademarks
This project and the similarly-named ones make references to "PIC32", "SAM", "XC32", and "MPLAB"
products from Microchip Technology. Those names are trademarks or registered trademarks of Microchip
Technology.

These projects also refer to "Arm", "ARM", "Cortex", and "CMSIS", which are all trademarks of Arm
Limited.

These projects are all independent efforts not affiliated with, endorsed, sponsored, or otherwise
approved by Microchip Technology nor Arm Limited.

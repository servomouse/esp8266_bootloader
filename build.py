import os
import sys
import subprocess
import time
import glob
from termcolor import colored
from pathlib import Path    # to check if a directory exists

common_path = "/media/master/0E5513DF0E5513DF/Work/esp8266/Toolchain/xtensa-lx106-elf-gcc8_4_0-esp-2020r3-linux-amd64/xtensa-lx106-elf/bin/"

esptool2 = "/media/master/0E5513DF0E5513DF/Work/esp8266/Projects/esptool2/esptool2"

output_file_name = "boot"

asm_path = f"{common_path}xtensa-lx106-elf-as"
compiler_path = f"{common_path}xtensa-lx106-elf-gcc"
linker_path = f"{common_path}xtensa-lx106-elf-ld"
objdump_path = f"{common_path}xtensa-lx106-elf-objdump"
objcopy_path = f"{common_path}xtensa-lx106-elf-objcopy"

linker_script = "eagle.app.v6.ld"

compiler_flags = ["-Os", 
                  "-Wall", 
                  "-fno-inline-functions",
                  "-nostdlib",
                  "-mlongcalls",
                  "-mtext-section-literals",
                  "-D__ets",
                  "-DICACHE_FLASH",
                  "-c",
                  ]

linker_flags = [f"-T {linker_script}", 
                "-EL", 
                "-nostdlib", 
                "-no-check-sections", 
                "-u call_user_start", 
                "-static", 
                "--print-memory-usage"]


def compile(input_file:str) -> int:
    ''' returns 0 if error, 1 if ok '''
    print(f"file: {input_file}", flush=True)
    time.sleep(0.1)
    output_file = f"temp_files/{input_file.split('/')[-1].split('.')[0]}.o"
    return subprocess.call(f'{compiler_path} {" ".join(compiler_flags)} {input_file} -o {output_file}',shell=True)


def compile_all(files:list):
    print(f"files to compile: {' '.join(files)}")
    for item in files:
        if compile(item) == 1:
            print(colored(f"{item} compilation error", 'red'))
            sys.exit(0)
    print(colored("compilation completed successfully", 'green'))
    return 0


def link_all(files:list):
    retval = subprocess.call(f'{linker_path} {" ".join(linker_flags)} {" ".join(files)} -o temp_files/main.elf', shell=True)
    if retval == 1:
        print(colored("linking error", 'red'))
        sys.exit(0)
    return retval


def get_files(path:str, filetype:str)->list:
    result = []

    for x in os.walk(path):
        for y in glob.glob(os.path.join(x[0], f'*{filetype}')):
            temp = y[len(path)+1:].replace("\\", "/")
            result.append(temp)
    return result


def convert_elf():
    # subprocess.call(f'{objcopy_path} -O ihex main.elf main.hex', shell=True)
    # subprocess.call(f'{objcopy_path} -O binary main.elf main.bin', shell=True)
    subprocess.call(f'{esptool2} -quiet -bin -boot0 -4096 -qio -40 temp_files/main.elf {output_file_name}.bin .text .rodata', shell=True)
    print(colored(f"file {output_file_name}.bin ready to be uploaded at address 0x00000000", 'green'))


def build():
    Path("temp_files").mkdir(parents=True, exist_ok=True) # create temp directory if there is no one
    workdir = os.path.abspath(os.getcwd())
    if 0 == compile_all(get_files(workdir, ".c")) and 0 == link_all(get_files(workdir, ".o")):
        convert_elf()
        subprocess.call('rm -r temp_files/*', shell=True)
        return 1
    return 0


def flash_chip():
    os.system("sudo esptool --port /dev/ttyUSB0 write_flash --flash_size=detect --flash_mode dio 0x00000 boot.bin")


if __name__ == '__main__':
    if len(sys.argv) > 1:
        for i in range(1, len(sys.argv)):
            if sys.argv[i] == 'build' and build():
                sys.exit(0)
            elif sys.argv[i] == 'flash':
                flash_chip()
    else:
        build()

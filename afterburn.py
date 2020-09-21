import subprocess
import os
import sys
from datetime import datetime
import time
from logger import make_logger
import xmltodict
import platform
import regex as re
import json

LOGGER = make_logger(sys.stderr, "afterburn")
NVCMD = 'nvidia-smi'


def main():

    if '18.04' in platform.version():
        NV_prefix = "sudo -s DISPLAY=:0 XAUTHORITY=/run/user/1000/gdm/Xauthority"
    if '20.04' in platform.version():
        NV_prefix = "sudo -s DISPLAY=:0 XAUTHORITY=/run/user/125/gdm/Xauthority"

    miner_name = sys.argv[1]

    if miner_name == 'default':
        DEFAULT = True
    else:
        DEFAULT = False


    if DEFAULT==False:
        with open (f"{miner_name}.json", 'r') as file:
            clock_offset_dict = json.load(file)



    process = subprocess.Popen(f"{NVCMD} -x -q", stdout = subprocess.PIPE, stderr = subprocess.PIPE, shell=True)
    output, error = process.communicate()

    info_dict_gpu_count = xmltodict.parse(output)
    num_GPU = int(info_dict_gpu_count['nvidia_smi_log']['attached_gpus'])


    for i in range(num_GPU):

        process = subprocess.Popen(f"nvidia-smi -x -q -i {i}", stdout = subprocess.PIPE, stderr = subprocess.PIPE, shell=True)
        output, error = process.communicate()

        info_dict = xmltodict.parse(output)
        # print(info_dict)

        print(f"Found GPU: #{i}")
        LOGGER.info(f"Found GPU: #{i}")

        current_memory_clock = int(re.search("(\d+) MHz", info_dict['nvidia_smi_log']['gpu']['clocks']['mem_clock'])[1])
        print(f"GPU #{i} Current Memory Clock: {current_memory_clock}")
        LOGGER.info(f"GPU #{i} Current Memory Clock: {current_memory_clock}")

        max_memory_clock = int(re.search("(\d+) MHz", info_dict['nvidia_smi_log']['gpu']['max_clocks']['mem_clock'])[1])
        print(f"GPU #{i} Maximum Memory Clock: {max_memory_clock}")
        LOGGER.info(f"GPU #{i} Maximum Memory Clock: {max_memory_clock}")



        if DEFAULT == False:
            clock_offset = clock_offset_dict[f'gpu{i}']['cpu_clock_offset']
            mem_clock_offset = clock_offset_dict[f'gpu{i}']['mem_clock_offset']
            print(f"Clock Offset: {clock_offset}")
            print(f"Memory Offset: {mem_clock_offset}")
            clock_offset = int(clock_offset)
            mem_clock_offset = int(mem_clock_offset)
        else:
            clock_offset = 0
            mem_clock_offset = 0
            print(f"Reset Clock Offset: {clock_offset}")
            print(f"Reset Memory Offset: {mem_clock_offset}")


        process = subprocess.Popen(f"{NV_prefix} nvidia-settings -a \"[gpu:{i}]/GPUGraphicsClockOffset[3]={clock_offset}\" -a \"[gpu:{i}]/GPUMemoryTransferRateOffset[2]={mem_clock_offset}\" -a \"[gpu:{i}]/GPUMemoryTransferRateOffset[3]={mem_clock_offset}\"", stdout = subprocess.PIPE, stderr = subprocess.PIPE, shell=True)
        output, error = process.communicate()
        if output:
            LOGGER.info(f"[ACTION]: GPU #{i} {output.decode().strip()}")
            print(f"[ACTION]: GPU #{i} {output.decode().strip()}")
        if error:
            LOGGER.critical(f"[ERROR]: GPU #{i} {error.decode().strip()}")
            print(f"[ERROR]: GPU #{i} {error.decode().strip()}")

main()

import os
import subprocess
import threading
import sys
from time import sleep
import numpy
import pandas as pd
import numpy as np

"""
Used in the remote machine for link updating, initializing links, damaging and recovering links and other functionalities。
author: Yangtao Deng (dengyt21@mails.tsinghua.edu.cn) and Zeqi Lai (zeqilai@tsinghua.edu.cn) 
"""


def sn_get_right_satellite(current_sat_id, current_orbit_id, orbit_num):
    if current_orbit_id == orbit_num - 1:
        return [current_sat_id, 0]
    else:
        return [current_sat_id, current_orbit_id + 1]


def sn_get_down_satellite(current_sat_id, current_orbit_id, sat_num):
    if current_sat_id == sat_num - 1:
        return [0, current_orbit_id]
    else:
        return [current_sat_id + 1, current_orbit_id]


def sn_ISL_establish(current_sat, next_sat_in_orbit, sat_in_next_orbit, plane_id, 
                     current_orbit_id, next_orbit_id, container_id_list,
                     orbit_num, sat_num, constellation_size, matrix, bw, loss):
    isl_idx = current_sat * 2 + 1
    # Establish intra-orbit ISLs
    if current_sat != next_sat_in_orbit:
        print("[" + str(isl_idx) + "/" + str(constellation_size * 2) +
              "] Establish intra-orbit ISL from: plane " + str(plane_id) + " - (" + 
              str(current_sat) + "," + str(current_orbit_id) + ") to (" + 
              str(next_sat_in_orbit) + "," + str(current_orbit_id) + ")")
        ISL_name = "Le_" + str(current_sat) + "-" + str(current_orbit_id) + \
            "_" + str(next_sat_in_orbit) + "-" + str(current_orbit_id)
        address_16_23 = isl_idx >> 8
        address_8_15 = isl_idx & 0xff
        # Create internal network in docker.
        os.system('docker network create ' + ISL_name + " --subnet 10." +
                  str(address_16_23) + "." + str(address_8_15) + ".0/24")
        print('[Create ISL:]' + 'docker network create ' + ISL_name +
              " --subnet 10." + str(address_16_23) + "." + str(address_8_15) +
              ".0/24")
        os.system('docker network connect ' + ISL_name + " " +
                  str(container_id_list[current_sat]) + " --ip 10." +
                  str(address_16_23) + "." + str(address_8_15) + ".40")
        delay = matrix[current_sat][next_sat_in_orbit]
        with os.popen(
                "docker exec -it " +
                str(container_id_list[current_sat]) +
                " ip addr | grep -B 2 10." + str(address_16_23) + "." +
                str(address_8_15) +
                ".40 | head -n 1 | awk -F: '{ print $2 }' | tr -d '[:blank:]'") as f:
            ifconfig_output = f.readline()
            target_interface = str(ifconfig_output).split("@")[0]
            os.system("docker exec -d " +
                      str(container_id_list[current_sat]) +
                      " ip link set dev " + target_interface + " down")
            os.system("docker exec -d " +
                      str(container_id_list[current_sat]) +
                      " ip link set dev " + target_interface + " name " + "B" +
                      str(current_sat + 1) +
                      "-eth" + str(next_sat_in_orbit + 1))
            os.system("docker exec -d " +
                      str(container_id_list[current_sat]) +
                      " ip link set dev B" +
                      str(current_sat + 1) +
                      "-eth" + str(next_sat_in_orbit + 1) +
                      " up")
            os.system("docker exec -d " +
                      str(container_id_list[current_sat]) +
                      " tc qdisc add dev B" +
                      str(current_sat + 1) +
                      "-eth" + str(next_sat_in_orbit + 1) +
                      " root netem delay " + str(delay) + "ms loss " + str(loss) + "% rate " + str(bw) + "Gbps")
        print('[Add current node:]' + 'docker network connect ' + ISL_name + " " +
              str(container_id_list[current_sat]) +
              " --ip 10." + str(address_16_23) + "." + str(address_8_15) + ".40")
        os.system('docker network connect ' + ISL_name + " " +
                  str(container_id_list[next_sat_in_orbit]) +
                  " --ip 10." + str(address_16_23) + "." + str(address_8_15) +
                  ".10")
        with os.popen(
                "docker exec -it " +
                str(container_id_list[next_sat_in_orbit]) +
                " ip addr | grep -B 2 10." + str(address_16_23) + "." +
                str(address_8_15) +
                ".10 | head -n 1 | awk -F: '{ print $2 }' | tr -d '[:blank:]'") as f:
            ifconfig_output = f.readline()
            target_interface = str(ifconfig_output).split("@")[0]
            os.system("docker exec -d " +
                      str(container_id_list[next_sat_in_orbit]) + " ip link set dev " +
                      target_interface + " down")
            os.system("docker exec -d " +
                      str(container_id_list[next_sat_in_orbit]) + " ip link set dev " +
                      target_interface + " name " + "B" +
                      str(next_sat_in_orbit + 1) + "-eth" +
                      str(current_sat + 1))
            os.system("docker exec -d " +
                      str(container_id_list[next_sat_in_orbit]) + " ip link set dev B" +
                      str(next_sat_in_orbit + 1) + "-eth" +
                      str(current_sat + 1) + " up")
            os.system("docker exec -d " +
                      str(container_id_list[next_sat_in_orbit]) + " tc qdisc add dev B" +
                      str(next_sat_in_orbit + 1) + "-eth" +
                      str(current_sat + 1) +
                      " root netem delay " + str(delay) + "ms loss " + str(loss) + "% rate " + str(bw) + "Gbps")
        print('[Add down node:]' + 'docker network connect ' + ISL_name + " " +
              str(container_id_list[next_sat_in_orbit]) +
              " --ip 10." + str(address_16_23) + "." + str(address_8_15) + ".10")

        print("Add 10." + str(address_16_23) + "." + str(address_8_15) +
              ".40/24 and 10." + str(address_16_23) + "." + str(address_8_15) +
              ".10/24 to (" + str(current_sat) + "," + str(current_orbit_id) +
              ") to (" + str(next_sat_in_orbit) + "," + str(current_orbit_id) + ")")
        isl_idx = isl_idx + 1

    if current_sat != sat_in_next_orbit:
        # Establish inter-orbit ISLs
        print("[" + str(isl_idx) + "/" + str(constellation_size * 2) +
              "] Establish inttra-orbit ISL from: plane " + str(plane_id) + " (" 
              + str(current_sat) + "," +
              str(current_orbit_id) + ") to (" + str(sat_in_next_orbit) + "," +
              str(next_orbit_id) + ")")
        ISL_name = "La_" + str(current_sat) + "-" + str(current_orbit_id) + \
            "_" + str(sat_in_next_orbit) + "-" + str(next_orbit_id)
        address_16_23 = isl_idx >> 8
        address_8_15 = isl_idx & 0xff
        # Create internal network in docker.
        os.system('docker network create ' + ISL_name + " --subnet 10." +
                  str(address_16_23) + "." + str(address_8_15) + ".0/24")
        print('[Create ISL:]' + 'docker network create ' + ISL_name +
              " --subnet 10." + str(address_16_23) + "." + str(address_8_15) +
              ".0/24")
        os.system('docker network connect ' + ISL_name + " " +
                  str(container_id_list[current_sat]) + " --ip 10." +
                  str(address_16_23) + "." + str(address_8_15) + ".30")
        delay = matrix[current_sat][sat_in_next_orbit]
        with os.popen(
                "docker exec -it " +
                str(container_id_list[current_sat]) +
                " ip addr | grep -B 2 10." + str(address_16_23) + "." +
                str(address_8_15) +
                ".30 | head -n 1 | awk -F: '{ print $2 }' | tr -d '[:blank:]'") as f:
            ifconfig_output = f.readline()
            target_interface = str(ifconfig_output).split("@")[0]
            os.system("docker exec -d " +
                      str(container_id_list[current_sat]) +
                      " ip link set dev " + target_interface + " down")
            os.system("docker exec -d " +
                      str(container_id_list[current_sat]) +
                      " ip link set dev " + target_interface + " name " + "B" +
                      str(current_sat + 1) +
                      "-eth" + str(sat_in_next_orbit + 1))
            os.system("docker exec -d " +
                      str(container_id_list[current_sat]) +
                      " ip link set dev B" +
                      str(current_sat + 1) +
                      "-eth" + str(sat_in_next_orbit + 1) +
                      " up")
            os.system("docker exec -d " +
                      str(container_id_list[current_sat]) +
                      " tc qdisc add dev B" +
                      str(current_sat + 1) +
                      "-eth" + str(sat_in_next_orbit + 1) +
                      " root netem delay " + str(delay) + "ms loss " + str(loss) + "% rate " + str(bw) + "Gbps")
        print('[Add current node:]' + 'docker network connect ' + ISL_name + " " +
              str(container_id_list[current_sat]) +
              " --ip 10." + str(address_16_23) + "." + str(address_8_15) + ".30")
        os.system('docker network connect ' + ISL_name + " " +
                  str(container_id_list[sat_in_next_orbit]) +
                  " --ip 10." + str(address_16_23) + "." + str(address_8_15) +
                  ".20")

        with os.popen(
                "docker exec -it " +
                str(container_id_list[sat_in_next_orbit]) +
                " ip addr | grep -B 2 10." + str(address_16_23) + "." +
                str(address_8_15) +
                ".20 | head -n 1 | awk -F: '{ print $2 }' | tr -d '[:blank:]'") as f:
            ifconfig_output = f.readline()
            target_interface = str(ifconfig_output).split("@")[0]
            os.system("docker exec -d " +
                      str(container_id_list[sat_in_next_orbit]) + " ip link set dev " +
                      target_interface + " down")
            os.system("docker exec -d " +
                      str(container_id_list[sat_in_next_orbit]) + " ip link set dev " +
                      target_interface + " name " + "B" +
                      str(sat_in_next_orbit + 1) + "-eth" +
                      str(current_sat + 1))
            os.system("docker exec -d " +
                      str(container_id_list[sat_in_next_orbit]) + " ip link set dev B" +
                      str(sat_in_next_orbit + 1) + "-eth" +
                      str(current_sat + 1) + " up")
            os.system("docker exec -d " +
                      str(container_id_list[sat_in_next_orbit]) +
                      " tc qdisc add dev B" +
                      str(sat_in_next_orbit + 1) + "-eth" +
                      str(current_sat + 1) +
                      " root netem delay " + str(delay) + "ms loss " + str(loss) + "% rate " + str(bw) + "Gbps")
        print('[Add right node:]' + 'docker network connect ' + ISL_name + " " +
              str(container_id_list[sat_in_next_orbit]) +
              " --ip 10." + str(address_16_23) + "." + str(address_8_15) + ".20")

        print("Add 10." + str(address_16_23) + "." + str(address_8_15) +
              ".30/24 and 10." + str(address_16_23) + "." + str(address_8_15) +
              ".20/24 to (" + str(current_sat) + "," + str(current_orbit_id) +
              ") to (" + str(sat_in_next_orbit) + "," + str(next_orbit_id) + ")")


def sn_establish_ISLs(container_id_list, matrix, orbit_num, sat_num,
                      constellation_size, bw, loss, plane_cnt, 
                      constellation_conf_dir):

    sat_map_df = pd.read_csv(constellation_conf_dir + '/pos/sat_map.csv')

    plane_conf_dfs = [
        pd.read_csv(constellation_conf_dir + '/pos/' + f'constellation_{i}.csv') \
                for i in range(plane_cnt)]

    plane_groups = []
    for p_idx in range(plane_cnt):
        for i in range(plane_conf_dfs[p_idx].shape[0]):
            plane_conf_dfs[p_idx]['constellation'][i] = list(map(int, 
                    plane_conf_dfs[p_idx]['constellation'][i].strip('][').split(',')))
        
        plane_groups.append(plane_conf_dfs[p_idx]['orbit_id'].tolist())

    fast_assignments_df = pd.read_csv(constellation_conf_dir + '/fast_assignment.csv')
    for i in range(fast_assignments_df.shape[0]):
        fast_assignments_df['sat_list'][i] = list(map(int, 
                        fast_assignments_df['sat_list'][i].strip('][').split()))

    ISL_threads = []
    # for current_orbit_id in range(0, orbit_num):
    #     for current_sat_id in range(0, sat_num):
    #         ISL_thread = threading.Thread(
    #             target=sn_ISL_establish,
    #             args=(current_sat_id, current_orbit_id, container_id_list,
    #                   orbit_num, sat_num, constellation_size, matrix, bw,
    #                   loss))
    #         ISL_threads.append(ISL_thread)

    # Hack to initialize ISLs links from given consetellation config
    for p_idx in range(plane_cnt):
        plane = plane_conf_dfs[p_idx]
        for i in range(plane.shape[0]):
            current_orbit = plane['constellation'][i]
            num_sat_per_orbit = len(current_orbit)
            for idx, j in enumerate(current_orbit):
                current_sat = int(sat_map_df.loc[
                        (sat_map_df['orbit_id'] == plane['orbit_id'][i]) &
                        (sat_map_df['orbit_num'] == j)]['k'].values)
                next_sat_in_orbit = int(sat_map_df.loc[
                        (sat_map_df['orbit_id'] == plane['orbit_id'][i]) &
                        (sat_map_df['orbit_num'] == current_orbit[(idx + 1) % num_sat_per_orbit])
                ]['k'].values)
               
                if j in plane['constellation'][(i+1) % plane.shape[0]]:
                    sat_in_next_orbit = int(sat_map_df.loc[
                        (sat_map_df['orbit_id'] == plane['orbit_id'][(i + 1) % plane.shape[0]]) &
                        (sat_map_df['orbit_num'] == j)
                    ]['k'].values)
                else:
                    sat_in_next_orbit = current_sat

                if current_sat == sat_in_next_orbit:
                    next_orbit_id = plane['orbit_id'][i]
                else:
                    next_orbit_id = plane['orbit_id'][(i + 1) % plane.shape[0]]

                ISL_thread = threading.Thread(
                    target=sn_ISL_establish,
                    args=(current_sat, next_sat_in_orbit, sat_in_next_orbit, 
                          p_idx, plane['orbit_id'][i], next_orbit_id,
                          container_id_list, orbit_num, 
                          sat_num, constellation_size, matrix, bw, loss))
                ISL_threads.append(ISL_thread)
    
    for ISL_thread in ISL_threads:
        ISL_thread.start()
    for ISL_thread in ISL_threads:
        ISL_thread.join()


def sn_get_param(file_):
    f = open(file_)
    ADJ = f.readlines()
    for i in range(len(ADJ)):
        ADJ[i] = ADJ[i].strip('\n')
    ADJ = [x.split(',') for x in ADJ]
    f.close()
    return ADJ


def sn_get_container_info():
    #  Read all container information in all_container_info
    with os.popen("docker ps") as f:
        all_container_info = f.readlines()
        n_container = len(all_container_info) - 1

    container_id_list = []
    for container_idx in range(1, n_container + 1):
        container_id_list.append(all_container_info[container_idx].split()[0])

    return container_id_list


def sn_establish_GSL(container_id_list, matrix, fac_num, constellation_size, bw,
                     loss):
    # starting links among satellites and ground stations
    for i in range(1, constellation_size + 1):
        for j in range(constellation_size + 1,
                       constellation_size + fac_num + 1):
            # matrix[i-1][j-1])==1 means a link between node i and node j
            if ((float(matrix[i - 1][j - 1])) <= 0.01):
                continue
            # IP address  (there is a link between i and j)
            delay = str(matrix[i - 1][j - 1])
            address_16_23 = (j - constellation_size) & 0xff
            address_8_15 = i & 0xff
            GSL_name = "GSL_" + str(i) + "-" + str(j)
            # Create internal network in docker.
            os.system('docker network create ' + GSL_name + " --subnet 9." +
                      str(address_16_23) + "." + str(address_8_15) + ".0/24")
            print('[Create GSL:]' + 'docker network create ' + GSL_name +
                  " --subnet 9." + str(address_16_23) + "." +
                  str(address_8_15) + ".0/24")
            os.system('docker network connect ' + GSL_name + " " +
                      str(container_id_list[i - 1]) + " --ip 9." +
                      str(address_16_23) + "." + str(address_8_15) + ".50")
            with os.popen(
                    "docker exec -it " + str(container_id_list[i - 1]) +
                    " ip addr | grep -B 2 9." + str(address_16_23) + "." +
                    str(address_8_15) +
                    ".50 | head -n 1 | awk -F: '{ print $2 }' | tr -d '[:blank:]'"
            ) as f:
                ifconfig_output = f.readline()
                target_interface = str(ifconfig_output).split("@")[0]
                os.system("docker exec -d " + str(container_id_list[i - 1]) +
                          " ip link set dev " + target_interface + " down")
                os.system("docker exec -d " + str(container_id_list[i - 1]) +
                          " ip link set dev " + target_interface + " name " +
                          "B" + str(i - 1 + 1) + "-eth" + str(j))
                os.system("docker exec -d " + str(container_id_list[i - 1]) +
                          " ip link set dev B" + str(i - 1 + 1) + "-eth" +
                          str(j) + " up")
                os.system("docker exec -d " + str(container_id_list[i - 1]) +
                          " tc qdisc add dev B" + str(i - 1 + 1) + "-eth" +
                          str(j) + " root netem delay " + str(delay) + "ms loss " + str(loss) + "% rate " + str(bw) + "Gbps")
            print('[Add current node:]' + 'docker network connect ' +
                  GSL_name + " " + str(container_id_list[i - 1]) + " --ip 9." +
                  str(address_16_23) + "." + str(address_8_15) + ".50")

            os.system('docker network connect ' + GSL_name + " " +
                      str(container_id_list[j - 1]) + " --ip 9." +
                      str(address_16_23) + "." + str(address_8_15) + ".60")
            with os.popen(
                    "docker exec -it " + str(container_id_list[j - 1]) +
                    " ip addr | grep -B 2 9." + str(address_16_23) + "." +
                    str(address_8_15) +
                    ".60 | head -n 1 | awk -F: '{ print $2 }' | tr -d '[:blank:]'"
            ) as f:
                ifconfig_output = f.readline()
                target_interface = str(ifconfig_output).split("@")[0]
                os.system("docker exec -d " + str(container_id_list[j - 1]) +
                          " ip link set dev " + target_interface + " down")
                os.system("docker exec -d " + str(container_id_list[j - 1]) +
                          " ip link set dev " + target_interface + " name " +
                          "B" + str(j) + "-eth" + str(i - 1 + 1))
                os.system("docker exec -d " + str(container_id_list[j - 1]) +
                          " ip link set dev B" + str(j) + "-eth" +
                          str(i - 1 + 1) + " up")
                os.system("docker exec -d " + str(container_id_list[j - 1]) +
                          " tc qdisc add dev B" + str(j) + "-eth" +
                          str(i - 1 + 1) + " root netem delay " + str(delay) +
                          "ms loss " + str(loss) + "% rate " + str(bw) +
                          "Gbps")
            print('[Add right node:]' + 'docker network connect ' + GSL_name +
                  " " + str(container_id_list[j - 1]) + " --ip 9." +
                  str(address_16_23) + "." + str(address_8_15) + ".60")
    for j in range(constellation_size + 1, constellation_size + fac_num + 1):
        GS_name = "GS_" + str(j)
        # Create default network and interface for GS.
        os.system('docker network create ' + GS_name + " --subnet 9." +
                  str(j) + "." + str(j) + ".0/24")
        print('[Create GS network:]' + 'docker network create ' + GS_name +
              " --subnet 9." + str(j) + "." + str(j) + ".10/24")
        os.system('docker network connect ' + GS_name + " " +
                  str(container_id_list[j - 1]) + " --ip 9." + str(j) + "." +
                  str(j) + ".10")
        with os.popen(
                "docker exec -it " + str(container_id_list[j - 1]) +
                " ip addr | grep -B 2 9." + str(j) + "." + str(j) +
                ".10 | head -n 1 | awk -F: '{ print $2 }' | tr -d '[:blank:]'"
        ) as f:
            ifconfig_output = f.readline()
            target_interface = str(ifconfig_output).split("@")[0]
            os.system("docker exec -d " + str(container_id_list[j - 1]) +
                      " ip link set dev " + target_interface + " down")
            os.system("docker exec -d " + str(container_id_list[j - 1]) +
                      " ip link set dev " + target_interface + " name " + "B" +
                      str(j - 1 + 1) + "-default")
            os.system("docker exec -d " + str(container_id_list[j - 1]) +
                      " ip link set dev B" + str(j - 1 + 1) + "-default" +
                      " up")
        print('[Add current node:]' + 'docker network connect ' + GS_name +
              " " + str(container_id_list[j - 1]) + " --ip 9." + str(j) + "." +
              str(j) + ".10")


def sn_copy_run_conf(container_idx, Path, current, total):
    os.system("docker cp " + Path + "/B" + str(current + 1) + ".conf " +
              str(container_idx) + ":/B" + str(current + 1) + ".conf")
    print("[" + str(current + 1) + "/" + str(total) + "]" +
          " docker cp bird.conf " + str(container_idx) + ":/bird.conf")
    command = ['docker', 'exec', '-i', str(container_idx), 'bird', '-c',
               'B{}.conf'.format(current + 1)]
    
    result = subprocess.run(command, capture_output=False, text=True)
    # os.system("docker exec -it " + str(container_idx) + " bird -c B" +
    #           str(current + 1) + ".conf")
    print("[" + str(current + 1) + "/" + str(total) +
          "] Bird routing process for container: " + str(container_idx) +
          " has started. ")


def sn_copy_run_conf_to_each_container(container_id_list, sat_node_number,
                                       fac_node_number, path):
    print(
        "Copy bird configuration file to each container and run routing process."
    )
    # total = len(container_id_list)
    total = sat_node_number + fac_node_number
    copy_threads = []
    for current in range(0, total):
        copy_thread = threading.Thread(
            target=sn_copy_run_conf,
            args=(container_id_list[current], path + "/conf/bird-" +
                  str(sat_node_number) + "-" + str(fac_node_number), current,
                  total))
        copy_threads.append(copy_thread)
    for copy_thread in copy_threads:
        copy_thread.start()
    for copy_thread in copy_threads:
        copy_thread.join()
    print("Initializing routing...")
    sleep(120)
    print("Routing initialized!")


def sn_damage_link(sat_index, container_id_list):
    with os.popen(
            "docker exec -it " + str(container_id_list[sat_index]) +
            " ifconfig | sed 's/[ \t].*//;/^\(eth0\|\)\(lo\|\)$/d'") as f:
        ifconfig_output = f.readlines()
        for intreface in range(0, len(ifconfig_output), 2):
            os.system("docker exec -d " + str(container_id_list[sat_index]) +
                      " tc qdisc change dev " +
                      ifconfig_output[intreface][:-1] +
                      " root netem loss 100%")
            print("docker exec -d " + str(container_id_list[sat_index]) +
                  " tc qdisc change dev " + ifconfig_output[intreface][:-1] +
                  " root netem loss 100%")


def sn_damage(random_list, container_id_list):
    damage_threads = []
    for random_satellite in random_list:
        damage_thread = threading.Thread(target=sn_damage_link,
                                         args=(int(random_satellite),
                                               container_id_list))
        damage_threads.append(damage_thread)
    for damage_thread in damage_threads:
        damage_thread.start()
    for damage_thread in damage_threads:
        damage_thread.join()


def sn_recover_link(
    damaged_satellite,
    container_id_list,
    sat_loss,
):
    with os.popen(
            "docker exec -it " + str(container_id_list[damaged_satellite]) +
            " ifconfig | sed 's/[ \t].*//;/^\(eth0\|\)\(lo\|\)$/d'") as f:
        ifconfig_output = f.readlines()
        for i in range(0, len(ifconfig_output), 2):
            os.system("docker exec -d " +
                      str(container_id_list[damaged_satellite]) +
                      " tc qdisc change dev " + ifconfig_output[i][:-1] +
                      " root netem loss " + str(sat_loss) + "%")
            print("docker exec -d " +
                  str(container_id_list[damaged_satellite]) +
                  " tc qdisc change dev " + ifconfig_output[i][:-1] +
                  " root netem loss " + str(sat_loss) + "%")


def sn_del_network(network_name):
    os.system('docker network rm ' + network_name)


def sn_stop_emulation():
    os.system("docker service rm constellation-test")
    with os.popen("docker rm -f $(docker ps -a -q)") as f:
        f.readlines()
    with os.popen("docker network ls") as f:
        all_br_info = f.readlines()
        del_threads = []
        for line in all_br_info:
            if "La" in line or "Le" or "GS" in line:
                network_name = line.split()[1]
                del_thread = threading.Thread(target=sn_del_network,
                                              args=(network_name, ))
                del_threads.append(del_thread)
        for del_thread in del_threads:
            del_thread.start()
        for del_thread in del_threads:
            del_thread.join()


def sn_recover(damage_list, container_id_list, sat_loss):
    recover_threads = []
    for damaged_satellite in damage_list:
        recover_thread = threading.Thread(target=sn_recover_link,
                                          args=(int(damaged_satellite),
                                                container_id_list, sat_loss))
        recover_threads.append(recover_thread)
    for recover_thread in recover_threads:
        recover_thread.start()
    for recover_thread in recover_threads:
        recover_thread.join()


def sn_update_delay(matrix, container_id_list,
                    constellation_size):  # updating delays
    delay_threads = []
    for row in range(len(matrix)):
        for col in range(row, len(matrix[row])):
            if float(matrix[row][col]) > 0:
                if row < col:
                    delay_thread = threading.Thread(
                        target=sn_delay_change,
                        args=(row, col, matrix[row][col], container_id_list,
                              constellation_size))
                    delay_threads.append(delay_thread)
                else:
                    delay_thread = threading.Thread(
                        target=sn_delay_change,
                        args=(col, row, matrix[col][row], container_id_list,
                              constellation_size))
                    delay_threads.append(delay_thread)
    for delay_thread in delay_threads:
        delay_thread.start()
    for delay_thread in delay_threads:
        delay_thread.join()
    print("Delay updating done.\n")


def sn_delay_change(link_x, link_y, delay, container_id_list,
                    constellation_size):  # multi-thread updating delays
    if link_y <= constellation_size:
        os.system("docker exec -d " + str(container_id_list[link_x]) +
                  " tc qdisc change dev B" + str(link_x + 1) + "-eth" +
                  str(link_y + 1) + " root netem delay " + str(delay) + "ms")
        os.system("docker exec -d " + str(container_id_list[link_y]) +
                  " tc qdisc change dev B" + str(link_y + 1) + "-eth" +
                  str(link_x + 1) + " root netem delay " + str(delay) + "ms")
    else:
        os.system("docker exec -d " + str(container_id_list[link_x]) +
                  " tc qdisc change dev B" + str(link_x + 1) + "-eth" +
                  str(link_y + 1) + " root netem delay " + str(delay) + "ms")
        os.system("docker exec -d " + str(container_id_list[link_y]) +
                  " tc qdisc change dev B" + str(link_y + 1) + "-eth" +
                  str(link_x + 1) + " root netem delay " + str(delay) + "ms")


if __name__ == '__main__':
    if len(sys.argv) == 12:
        plane_cnt = int(sys.argv[1])
        constellation_conf_dir = sys.argv[2]
        orbit_num = int(sys.argv[3])
        sat_num = int(sys.argv[4])
        constellation_size = int(sys.argv[5])
        fac_num = int(sys.argv[6])
        sat_bandwidth = float(sys.argv[7])
        sat_loss = float(sys.argv[8])
        sat_ground_bandwidth = float(sys.argv[9])
        sat_ground_loss = float(sys.argv[10])
        current_topo_path = sys.argv[11]
        matrix = sn_get_param(current_topo_path)
        container_id_list = sn_get_container_info()
        
        sn_establish_ISLs(container_id_list, matrix, orbit_num, sat_num,
                          constellation_size, sat_bandwidth, sat_loss,
                          plane_cnt, constellation_conf_dir)
        sn_establish_GSL(container_id_list, matrix, fac_num, constellation_size,
                         sat_ground_bandwidth, sat_ground_loss)
    elif len(sys.argv) == 4:
        if sys.argv[3] == "update":
            current_delay_path = sys.argv[1]
            constellation_size = int(sys.argv[2])
            matrix = sn_get_param(current_delay_path)
            container_id_list = sn_get_container_info()
            sn_update_delay(matrix, container_id_list, constellation_size)
        else:
            constellation_size = int(sys.argv[1])
            fac_num = int(sys.argv[2])
            path = sys.argv[3]
            container_id_list = sn_get_container_info()
            sn_copy_run_conf_to_each_container(container_id_list,
                                               constellation_size, fac_num,
                                               path)
    elif len(sys.argv) == 2:
        path = sys.argv[1]
        random_list = numpy.loadtxt(path + "/damage_list.txt")
        container_id_list = sn_get_container_info()
        sn_damage(random_list, container_id_list)
    elif len(sys.argv) == 3:
        path = sys.argv[1]
        sat_loss = float(sys.argv[2])
        damage_list = numpy.loadtxt(path + "/damage_list.txt")
        container_id_list = sn_get_container_info()
        sn_recover(damage_list, container_id_list, sat_loss)
    elif len(sys.argv) == 1:
        sn_stop_emulation()

import numpy as np
import matplotlib.pyplot as plt
import re
import os

def load_delay_matrix(file_):
    f = open(file_)
    ADJ = f.readlines()
    for i in range(len(ADJ)):
        ADJ[i] = ADJ[i].strip('\n')
    ADJ = [x.split(',') for x in ADJ]
    f.close()
    return ADJ

def get_handover_delay(cell, target_sat, pre_sat, gw, current_time, 
                         handover_type, file_dir):
    # load delay matrix
    current_topo_path = file_dir + str(current_time) + '.txt'
    pre_topo_path = file_dir + str(current_time - 1) + '.txt'
    
    curr_matrix = load_delay_matrix(current_topo_path)
    pre_matrix = load_delay_matrix(pre_topo_path)
    
    # get message delay
    pre_backhaul_delay = float(pre_matrix[pre_sat-1][gw-1])
    target_backhaul_delay = float(curr_matrix[target_sat-1][gw-1])
    pre_comm_delay = float(pre_matrix[pre_sat-1][cell-1])
    target_comm_delay = float(curr_matrix[target_sat-1][cell-1])
    
    if target_comm_delay == 0:
        print("[Handover] target unreachable.")
        return -1
    if handover_type == 'CU-2':
        if curr_matrix[target_sat-1][pre_sat-1] == 0:
            isl_delay = pre_backhaul_delay + target_backhaul_delay
        else:
            isl_delay = curr_matrix[target_sat-1][pre_sat-1]
    else:
        isl_delay = None
        
    handover_delay = calculate_handover_delay(pre_backhaul_delay, target_backhaul_delay,
                                              pre_comm_delay, target_comm_delay,
                                              handover_type, isl_delay=isl_delay)
    
    return handover_delay
    
def calculate_handover_delay(pre_backhaul_delay, target_backhaul_delay,
                             pre_comm_delay, target_comm_delay,
                             handover_type, isl_delay=None):
    if handover_type == 'CU-1':
        delay = 2*pre_comm_delay + 1*target_comm_delay + 6*pre_backhaul_delay + 8*target_backhaul_delay
    elif handover_type == 'CU-2':
        assert isl_delay is not None
        delay = 2*pre_comm_delay + 1*target_comm_delay + 6*isl_delay + 2*target_backhaul_delay
    elif handover_type == 'DU-1':
        delay = 2*pre_comm_delay + 1*target_comm_delay + 5*pre_backhaul_delay + 3*target_backhaul_delay
    elif handover_type == 'DU-2':
        delay = 2*pre_comm_delay + 1*target_comm_delay
    else:
        raise ValueError("Invalid handover type.")
    
    return delay

def extract_perf_sections(perf_file): 
    roi = False
    lines = []
    
    with open(perf_file, 'r') as f:
        iperf_output = f.read()
    
    iperf_lines = iperf_output.split('\n')

    iperf_start_times = []
    iperf_sim_times = []
    iperf_start = False

    current_time = sim_time = -1
    for line_idx, line in enumerate(iperf_lines):
        if line_idx == len(iperf_lines)-1:
            break
        if 'current_time' in line:
            current_time = int(line.split(', ')[0].split(': ')[1])
            sim_time = int(line.split(', ')[1].split(': ')[1])
            if 'Connecting to' in iperf_lines[line_idx+1]:
                iperf_start_times.append(current_time)
                iperf_sim_times.append(sim_time)
                iperf_start = True
        if 'connected to' in line and iperf_start:
            roi = True
            continue
        if '- - - - - - - - - - - - -' in iperf_lines[line_idx+1]:
            roi = False
            iperf_start = False
            current_time = sim_time = -1
        if roi:
            lines.append(line)

    if lines == []:
        print("file empty: " + perf_file)
        return None
    
    result_lines = [lines[0]]
    
    for line_idx, line in enumerate(lines):
        if line_idx == 0:
            continue
        if 'ID' not in line and line != '' and '0.00-1.00' not in line:
            result_lines.append(line)

    results = '\n'.join(result_lines)
    
    return results, iperf_start_times, iperf_sim_times

def parse_perf_results(input_lines):
    # Extract bandwidth values using regular expressions
    transfer_values_tuple = re.findall(r'sec\s*(\d+\.\d+|\d+)\s*(K|M|G)Bytes', input_lines)
    transfer_rates_tuple = re.findall(r'(\d+\.\d+|\d+)\s(K|M|G)bits/sec', input_lines)

    transfer_rates_out = []
    for tup in transfer_rates_tuple:
        if tup[1] == 'K':
            rate = float(tup[0]) / 1000
        elif tup[1] == 'M':
            rate = float(tup[0])
        elif tup[1] == 'G':
            rate = float(tup[0]) * 1000
        else:
            raise ValueError("Invalid rate unit.")
        transfer_rates_out.append(rate)
    
    transfer_values_out = []
    for tup in transfer_values_tuple:
        if tup[1] == 'K':
            value = float(tup[0]) / 1000
        elif tup[1] == 'M':
            value = float(tup[0])
        elif tup[1] == 'G':
            value = float(tup[0]) * 1000
        else:
            raise ValueError("Invalid value unit.")
        transfer_values_out.append(value)
   
    return transfer_values_out, transfer_rates_out
    
def aggregate_results(transfer_values):
    # Convert extracted values to integers and sum them up
    total_transfer_bytes = sum(Bt for Bt in transfer_values)
    
    return total_transfer_bytes

def apply_handover_delay(cell, target_sat, pre_sat, gw, in_transferred, transfer_rate,
                         current_time, handover_type, delay_dir):
    handover_delay = get_handover_delay(cell, target_sat, pre_sat, gw, current_time,
                                        handover_type, delay_dir)
    transferred = in_transferred - handover_delay * transfer_rate / 8
    
    if transferred < 0:
        transferred = 0
        
    return transferred

def construct_change_matrix(cell_num, topo_change_file, cell_indices, sim_duration):
    with open(topo_change_file) as f:
        change_file = f.read()
        
    change_lines = change_file.split('\n')
    num_changes = sum(1 for line in change_lines if 'time' in line) - 1
    
    # initialize change matrix
    change_matrix = [[[-1, -1] for _ in range(num_changes)] for _ in range(cell_num)]
    change_time = [-1 for _ in range(num_changes)]
    change_idx = -1
    
    fi = open(topo_change_file, 'r')
    line = fi.readline()
    
    while line:
        words = line.split()
        if words[0] == 'time':
            print ("Time: " + words[1].strip())
            if (int(words[1].strip(':')) == sim_duration+1):
                break
            
            change_idx += 1
            change_time[change_idx] = int(words[1].strip(':'))
            line = fi.readline()
            words = line.split()
            line = fi.readline()
            line = fi.readline()
            words = line.split()
            while words[0] != 'del:': # addlink
                word = words[0].split('-')
                s = int (word[0])
                f = int (word[1])
                if s > f:
                    s, f = f, s
                if f in cell_indices:
                    print ("Add link: " + str(s) + " " + str(f))
                    change_matrix[cell_indices.index(f)][change_idx][1] = s
                line = fi.readline()
                words = line.split()
            line = fi.readline()
            words = line.split()
            while words[0] != 'time': # dellink
                word = words[0].split('-')
                s = int (word[0])
                f = int (word[1])

                if s > f:
                    s, f = f, s
                if f in cell_indices:
                    print ("Del link: " + str(s) + " " + str(f))
                    change_matrix[cell_indices.index(f)][change_idx][0] = s
                line = fi.readline()
                words = line.split() 
    
    fi.close()
    
    return change_matrix, change_time

def handover_through_time(cell, gw_list, iperf_start_times, iperf_sim_times, change_matrix, change_time, cell_indices,
                          transferred_list, trans_rates_list, handover_type, delay_dir):
    for idx, change in enumerate(change_matrix[cell_indices.index(cell)]):
        pre_sat = change[0] 
        target_sat = change[1]
        curr_time = change_time[idx]
        iperf_start = curr_time - 1
        if iperf_start not in iperf_start_times or (pre_sat == -1 or target_sat == -1):
            continue
        gw = gw_list[iperf_start_times.index(iperf_start)]
        trans_idx = sum(iperf_sim_times[:iperf_start_times.index(iperf_start)])
        transferred_list[trans_idx] = apply_handover_delay(cell, 
                                                       target_sat,
                                                       pre_sat,
                                                       gw,
                                                       transferred_list[trans_idx],
                                                       trans_rates_list[trans_idx],
                                                       curr_time,
                                                       handover_type,
                                                       delay_dir)
        
    return transferred_list

def get_throughput_results(file_dir, cell_indices, gw_indices, assignments, duration,
                           demands, change_time, change_matrix, handover_type, delay_dir):
    total_transfer = 0
    total_transfer_per_cell = []

    total_demands_per_cell = []
    total_demands = 0

    for cell in cell_indices:
        perf_file = file_dir + '/iperf/iperf_' + str(cell) + '_results.txt'
        sections, iperf_start_times, iperf_sim_times = extract_perf_sections(perf_file)

        if sections is None:
            continue
        transferred_list, trans_rates_list = parse_perf_results(sections)
        # print ("cell: {}".format(cell))
        # print (len(transferred_list))
        # print (len(trans_rates_list))
        # print (sum(iperf_sim_times))

        assert (len(transferred_list) == len(trans_rates_list) == sum(iperf_sim_times))

        if len(assignments.shape) == 1:
            gw_list = [gw_indices[assignments[cell_indices.index(cell)]] for _ in range(len(iperf_start_times))]
        else:
            gw_list = [gw_indices[assignments[iperf_start_times[t],cell_indices.index(cell)]] for t in iperf_start_times]

        transferred_list = handover_through_time(cell, gw_list, iperf_start_times, 
                                                 iperf_sim_times, change_matrix,
                                                 change_time, cell_indices, transferred_list,
                                                 trans_rates_list, handover_type, delay_dir)


        transferred = aggregate_results(transferred_list)
        total_transfer_per_cell.append(transferred)

    total_transfer = sum(total_transfer_per_cell)

    total_demands_per_cell = np.sum(demands, axis=0)/8
    total_demands = sum(total_demands_per_cell)

    return total_transfer, total_demands, total_transfer_per_cell, total_demands_per_cell
                                                           


if __name__ == "__main__":
	# Perform some actions or call functions here
	print ("No main function to run.")
	pass
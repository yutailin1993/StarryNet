#!/bin/bash

end_sim_time=29

while true; do
echo "waiting for starrynet running ..."
while [ ! -f star_info.txt ]; do
	sleep 3
done

echo "begin to run exp_ops.py"

if IFS=',' read -r current_time sim_time next_udpate_time < "./star_info.txt"; then
    rm star_info.txt

	echo "current_time: $current_time, sim_time: $sim_time, next_udpate_time: $next_udpate_time"

    sleep 10

    if [ "$next_udpate_time" -eq "$end_sim_time" ]; then
        python3 exp_ops.py $current_time $sim_time --collect-results 1
        touch exp_done.txt
        break
    else
        python3 exp_ops.py $current_time $sim_time
    fi

    touch exp_done.txt
fi

done
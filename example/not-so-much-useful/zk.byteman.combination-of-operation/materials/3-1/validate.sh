#! /bin/bash
set -x

sleep 10

#result=1
#count=0
#while [ ${result} -eq 1 -a ${count} -lt 30 ]
#do
#    python ${EQ_MATERIALS_DIR}/check-fle-states.py 2181 2182 2183 2184 2185 && result=0
#    (( count++ ))
#    sleep 1
#done
bash $EQ_MATERIALS_DIR/check-fle-states.sh 2181 2182 2183 2184 2185

result=1
count=0
while [ ${result} -eq 1 -a ${count} -lt 30 ]
do
    $EQ_MATERIALS_DIR/zookeeper/bin/zkCli.sh -server localhost:2181,localhost:2182,localhost:2183,localhost:2184,localhost:2185 create /hoo bar && result=0
    (( count++ ))
    sleep 1
done

if [ ${result} -eq 1 ]
then
    exit 1
else
    exit 0
fi


# Earthquake Demo (zookeeper)

## Getting Started
Prepare

    $ cp config_example.json config.json
    $ ./000-prepare-zk.sh
    $ ./010-start-orchestrator.sh


Run experiments

    $ ./020-start-zk-ensemble.sh
    $ ./030-concurrent-write.sh
    $ killall -9 java; rm -rf /tmp/eq/zk

    $ ./020-start-zk-ensemble.sh
    $ ./030-concurrent-write.sh
    $ killall -9 java; rm -rf /tmp/eq/zk

    # loop...


Get experimental result CSV

    $ ..
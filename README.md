# Earthquake: Dynamic Model Checker for Distributed Systems

## Python Binding
   $ ./build 
   # make sure ./bin/libearthquake.so is built
   $ LD_LIBRARY_PATH=./bin PYTHONPATH=. python -m pyearthquake.orchestrator.orchestrator example/zk/config.json


## Earthquake Classic (no binding)
   $ ./build
   $ ./bin/earthquake-classic -help

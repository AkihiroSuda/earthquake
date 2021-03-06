#!/bin/bash
set -e # exit on an error
. ${EQ_MATERIALS_DIR}/lib.sh

########## Boot ##########
CHECK_PREREQUISITES # already checked in init, but check again
if [ -z ${EQ_DISABLE} ]; then
    INSTALL_IPTABLES_RULE
    START_NFQHOOK
    START_INSPECTOR
    # TODO: check boot failure
fi
START_ZK_TEST
#PAUSE
COLLECT_COVERAGE

########## Shutdown ##########
if [ -z ${EQ_DISABLE} ]; then
    UNINSTALL_IPTABLES_RULE
    KILL_NFQHOOK
    KILL_INSPECTOR
fi

exit 0

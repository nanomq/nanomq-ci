#ifndef NNC_TEST_H
#define NNC_TEST_H

#include "utils.h"
#include "dbg.h"
#include <nng/mqtt/mqtt_client.h>
#include <nng/supplemental/util/platform.h>
#include <nng/nng.h>
#include <stdio.h>
#include <string.h>
#include <assert.h>
#include <errno.h>
#include <getopt.h>
#include <stdint.h>
#include <stdlib.h>
#include <time.h>
#include <unistd.h>
#include <stdatomic.h>

#define TOPIC_CNT 100
#define TOPIC_LEN 10


int init_test(void);
int run_test(const char *url);
// int client(const char *url);

#endif
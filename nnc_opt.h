#ifndef NNC_OPT_H
#define NNC_OPT_H

#include <getopt.h>
#include <stdint.h>


static char *short_options = "h:p:";
static struct option long_options[] = {
	{ "host", required_argument, NULL, 0 },
	{ "port", required_argument, NULL, 0 },
	{ "help", no_argument, NULL, 0 },
	{ NULL, 0, NULL, 0 },
};

typedef struct nnc_opt_s nnc_opt_t;
struct nnc_opt_s {
	char *host;
	int  port;
};

nnc_opt_t *nnc_get_opt(int argc, char **argv);

#endif

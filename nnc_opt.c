#include "nnc_opt.h"
#include "dbg.h"
#include "nnc_help.h"
#include "nng/nng.h"
#include "stdlib.h"


nnc_opt_t *nnc_get_opt(int argc, char **argv)
{
	int   opt = 0;
	int   digit_optind  = 0;
	int   option_index  = 0;

	nnc_opt_t *ret = nng_alloc(sizeof(nnc_opt_t));
	if (ret == NULL) {
		log_err("memory alloc error!");
		exit(EXIT_FAILURE);
	}
	ret->host = NULL;


	while ((opt = getopt_long(argc, argv, short_options, long_options,
	            &option_index)) != -1) {
		int this_option_optind = optind ? optind : 1;

		switch (opt) {
		case 0:
			if (!strcmp(long_options[option_index].name, "help")) {
				fprintf(stderr, "Usage: %s\n", ci_info);
				exit(EXIT_FAILURE);
			} else if (!strcmp(long_options[option_index].name,
			               "host")) {
				ret->host = nng_strdup(optarg);
			} else if (!strcmp(long_options[option_index].name,
			               "port")) {
				ret->port = atoi(optarg);
			}
			break;
		case 'h':
			ret->host = nng_strdup(optarg);
			break;
		case 'p':
			ret->port = atoi(optarg);
			break;
		case '?':
			fprintf(stderr, "Usage: %s\n", ci_info);
			exit(EXIT_FAILURE);
			break;
		default:
			fprintf(stderr, "Usage: %s\n", ci_info);
			exit(EXIT_FAILURE);
			printf(
			    "?? getopt returned character code 0%o ??\n", opt);
		}
	}
	if (optind < argc) {
		fprintf(stderr, "Usage: %s\n", ci_info);
		exit(EXIT_FAILURE);
		while (optind < argc)
			printf("%s ", argv[optind++]);
		printf("\n");
	}


	if (ret->host == NULL) {
		ret->host = nng_strdup("localhost");
	}

	if (ret->port == 0) {
		ret->port = 1883;
	}

	return ret;
}



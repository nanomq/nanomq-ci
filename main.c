#include "nnc_help.h"
#include "nnc_opt.h"
#include "nnc_test.h"


int
main(int argc, char **argv)
{
	int    rc;
	char url[64]        = { 0 };

	test_wildcard_topic_check();

	nnc_opt_t * opt = nnc_get_opt(argc, argv);
	sprintf(url, "mqtt-tcp://%s:%d", opt->host, opt->port);

	if ((rc = init_test()) != 0) {
		log_err("init test failed!");
	}

	run_test(url);
	sleep(1);
	return 0;
}

#include <assert.h>
#include <errno.h>
#include <getopt.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>
#include <stdatomic.h>
#include "dbg.h"
#include "utils.h"
#include "nnc_help.h"
#include "nnc_opt.h"

#include <nng/mqtt/mqtt_client.h>
#include <nng/nng.h>
#include <nng/supplemental/util/platform.h>


#define TOPIC_CNT 1000
#define TOPIC_LEN 100

static size_t nwork = 32;
static atomic_int acnt = 0;
static bool is_sub_finished = false;
static char **topic_que = NULL;

struct work {
	enum { INIT, RECV, WAIT, SEND } state;
	nng_aio *aio;
	nng_msg *msg;
	nng_ctx  ctx;
};


void
fatal(const char *msg, int rv)
{
	fprintf(stderr, "%s: %s\n", msg, nng_strerror(rv));
}


int check_recv(nng_msg *msg)
{

	// Get PUBLISH payload and topic from msg;
	uint32_t payload_len;
	uint32_t topic_len;

	uint8_t *payload = nng_mqtt_msg_get_publish_payload(msg, &payload_len);
	const char *topic = nng_mqtt_msg_get_publish_topic(msg, &topic_len);

	// TODO update assert_str
	if (!assert_str((char*) payload, topic, topic_len)) {
		acnt++;
		log_info("PASS RANDOM TEST [%d / %d]", acnt, TOPIC_CNT);
	} else {
		log_err("assert_str failed");
		return -1;
	}

	// printf("RECV: '%.*s' FROM: '%.*s'\n", payload_len,
	//     (char *) payload, topic_len, recv_topic);

	return 0;
}

void
sub_cb(void *arg)
{
	struct work *work = arg;
	nng_msg *    msg;
	int          rv;

	switch (work->state) {
	case INIT:
		work->state = RECV;
		nng_ctx_recv(work->ctx, work->aio);
		break;
	case RECV: 
		if ((rv = nng_aio_result(work->aio)) != 0) {
			nng_msg_free(work->msg);
			fatal("nng_send_aio", rv);
		}
		msg   = nng_aio_get_msg(work->aio);

		if (-1 == check_recv(msg)) {
			abort();
		}

		work->state = RECV;
		nng_ctx_recv(work->ctx, work->aio);
		break;
	default:
		fatal("bad state!", NNG_ESTATE);
		break;
	}
}

struct work *
alloc_work(nng_socket sock)
{
	struct work *w;
	int          rv;

	if ((w = nng_alloc(sizeof(*w))) == NULL) {
		fatal("nng_alloc", NNG_ENOMEM);
	}
	if ((rv = nng_aio_alloc(&w->aio, sub_cb, w)) != 0) {
		fatal("nng_aio_alloc", rv);
	}
	if ((rv = nng_ctx_open(&w->ctx, sock)) != 0) {
		fatal("nng_ctx_open", rv);
	}
	w->state = INIT;
	return (w);
}

void
connect_cb(nng_pipe p, nng_pipe_ev ev, void *arg)
{
	printf("%s: connected!\n", __FUNCTION__);
	nng_socket sock = *(nng_socket *) arg;

	nng_mqtt_topic_qos topic_qos[TOPIC_CNT];
  	for (int i = 0; i < TOPIC_CNT; i++) {
  		topic_qos[i].qos = 0;
  		topic_qos[i].topic.buf = (uint8_t*) topic_que[i];
  		topic_qos[i].topic.length = strlen(topic_que[i]);
		// log_info("%s", topic_qos[i].topic.buf);
  	}
	size_t topic_qos_count =
	    sizeof(topic_qos) / sizeof(nng_mqtt_topic_qos);
	// Connected succeed
	nng_msg *msg;
	nng_mqtt_msg_alloc(&msg, 0);
	nng_mqtt_msg_set_packet_type(msg, NNG_MQTT_SUBSCRIBE);
	nng_mqtt_msg_set_subscribe_topics(msg, topic_qos, topic_qos_count);

	// Send subscribe message
	int rv  = 0;
	if ((rv = nng_sendmsg(sock, msg, NNG_FLAG_NONBLOCK)) != 0) {
		fatal("nng_sendmsg", rv);
	}

	is_sub_finished = true;
}

void
disconnect_cb(nng_pipe p, nng_pipe_ev ev, void *arg)
{
	printf("%s: disconnected!\n", __FUNCTION__);
}


int
client_publish(nng_socket sock, const char *topic, uint8_t *payload,
    uint32_t payload_len, uint8_t qos, bool verbose)
{
	int rv;

	// create a PUBLISH message
	nng_msg *pubmsg;
	nng_mqtt_msg_alloc(&pubmsg, 0);
	nng_mqtt_msg_set_packet_type(pubmsg, NNG_MQTT_PUBLISH);
	nng_mqtt_msg_set_publish_dup(pubmsg, 0);
	nng_mqtt_msg_set_publish_qos(pubmsg, qos);
	nng_mqtt_msg_set_publish_retain(pubmsg, 0);
	nng_mqtt_msg_set_publish_payload(
	    pubmsg, (uint8_t *) payload, payload_len);
	nng_mqtt_msg_set_publish_topic(pubmsg, topic);

	if (verbose) {
		uint8_t print[1024] = { 0 };
		nng_mqtt_msg_dump(pubmsg, print, 1024, true);
		printf("%s\n", print);
	}

	// printf("Publishing '%s' to '%s' ...\n", payload, topic);
	if ((rv = nng_sendmsg(sock, pubmsg, NNG_FLAG_NONBLOCK)) != 0) {
		fatal("nng_sendmsg", rv);
	}

	return rv;
}

int
client(const char *url)
{
	nng_socket   sock;
	nng_dialer   dialer;
	struct work *works[nwork];
	int          i;
	int          rv;

	if ((rv = nng_mqtt_client_open(&sock)) != 0) {
		fatal("nng_socket", rv);
	}

	for (i = 0; i < nwork; i++) {
		works[i] = alloc_work(sock);
	}

	// Mqtt connect message
	nng_msg *msg;
	nng_mqtt_msg_alloc(&msg, 0);
	nng_mqtt_msg_set_packet_type(msg, NNG_MQTT_CONNECT);
	nng_mqtt_msg_set_connect_keep_alive(msg, 60);
	nng_mqtt_msg_set_connect_clean_session(msg, true);

	nng_mqtt_set_connect_cb(sock, connect_cb, &sock);
	nng_mqtt_set_disconnect_cb(sock, disconnect_cb, NULL);

	if ((rv = nng_dialer_create(&dialer, sock, url)) != 0) {
		fatal("nng_dialer_create", rv);
	}

	nng_dialer_set_ptr(dialer, NNG_OPT_MQTT_CONNMSG, msg);
	nng_dialer_start(dialer, NNG_FLAG_NONBLOCK);

	for (i = 0; i < nwork; i++) {
		sub_cb(works[i]);
	}

	while (!is_sub_finished) {}
	nng_msleep(TOPIC_CNT); 
	int cnt = 0;
	for (size_t j = 0 ; j < TOPIC_CNT; j++) {
		cnt++;
		client_publish(sock, topic_que[j], (uint8_t*) topic_que[j], TOPIC_LEN, 0, false);
	}

	log_info("cnt: %d", cnt);


	// TODO Here we will wait this group test finished.
	for (;;) {
		nng_msleep(3600000);
	}

	// disconnect
}


int
main(int argc, char **argv)
{
	int    rc;
	char url[64]        = { 0 };


	srand(time(NULL));
	topic_que = (char**) malloc(sizeof(char*) * TOPIC_CNT);
	if (topic_que == NULL) {
		log_err("memory alloc error");
		return -1;
	}

	for (size_t i = 0; i < TOPIC_CNT; i++) {
		topic_que[i] = (char*) malloc(sizeof(char) * TOPIC_LEN);
		if (topic_que[i] == NULL) {
			log_err("memory alloc error");
			return -1;

		}
	}

  	if (-1 == mk_rnd_str_que(TOPIC_CNT, TOPIC_LEN, topic_que)) {
	 	log_err("make string queue failed!");
		return -1;
  	}

#ifdef VERBOSE
	for (size_t i = 0; i < TOPIC_CNT; i++) {
		log_info("topic: %s", topic_que[i]);
	}
#endif

	nnc_opt_t * opt = nnc_get_opt(argc, argv);
	sprintf(url, "mqtt-tcp://%s:%d", opt->host, opt->port);
	client(url);

	return 0;
}

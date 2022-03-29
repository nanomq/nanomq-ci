#include "nnc_test.h"

char **topic_que = NULL;
char **wildcard_topic_que = NULL;
char **normal_topic_que = NULL;
bool is_sub_finished = false;

// #define VERBOSE
typedef enum {
	TEST_RANDOM,
	TEST_WILDCARD,
} test_state_t;

test_state_t test_state;

static size_t nwork = 32;
static atomic_int acnt = 0;
static int wildcard_acnt = 0;

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

void
disconnect_cb(nng_pipe p, nng_pipe_ev ev, void *arg)
{
	printf("%s: disconnected!\n", __FUNCTION__);
}

void set_sub_topic(nng_mqtt_topic_qos topic_qos[], int qos, char **topic_que)
{
  	for (int i = 0; i < TOPIC_CNT; i++) {
  		topic_qos[i].qos = qos;
  		topic_qos[i].topic.buf = (uint8_t*) topic_que[i];
  		topic_qos[i].topic.length = strlen(topic_que[i]);
  	}
    return;
}
        

void
connect_cb(nng_pipe p, nng_pipe_ev ev, void *arg)
{
	// printf("%s: connected!\n", __FUNCTION__);
	nng_socket sock = *(nng_socket *) arg;

	nng_mqtt_topic_qos topic_qos[TOPIC_CNT];
	if (topic_que == NULL) {
		log_err("topic que is NULL!");
		return;
	}

    switch (test_state) {
        case TEST_RANDOM:
             set_sub_topic(topic_qos, 0, topic_que);
            break;
        case TEST_WILDCARD:
            set_sub_topic(topic_qos, 0, wildcard_topic_que);
            break;
        default:
            log_err("Should not be here: %d", test_state);
            break;
    }

	size_t topic_qos_count =
	    sizeof(topic_qos) / sizeof(nng_mqtt_topic_qos);

	nng_msg *msg;
	nng_mqtt_msg_alloc(&msg, 0);
	nng_mqtt_msg_set_packet_type(msg, NNG_MQTT_SUBSCRIBE);
	nng_mqtt_msg_set_subscribe_topics(msg, topic_qos, topic_qos_count);

	// Send subscribe message
	int rv  = 0;
	while ((rv = nng_sendmsg(sock, msg, NNG_FLAG_NONBLOCK)) != 0) {
		fatal("nng_sendmsg", rv);
		sleep(1);
	}

	is_sub_finished = true;
}

int check_recv(nng_msg *msg)
{

	// Get PUBLISH payload and topic from msg;
	uint32_t payload_len;
	uint32_t topic_len;

	uint8_t *payload = nng_mqtt_msg_get_publish_payload(msg, &payload_len);
	const char *topic = nng_mqtt_msg_get_publish_topic(msg, &topic_len);

	switch (test_state)
	{
	case TEST_RANDOM:
		if (!assert_str((char*) payload, topic, topic_len)) {
			acnt++;
		} else {
			log_err("assert_str failed");
			return -1;
		}
		break;
	case TEST_WILDCARD:;
		char topic_buf[TOPIC_LEN];
		char payload_buf[TOPIC_LEN];
		
		memcpy(topic_buf, topic, topic_len);
		memcpy(payload_buf, payload, payload_len);
		payload_buf[TOPIC_LEN-1] = '\0';
		topic_buf[TOPIC_LEN-1] = '\0';
		
		if (check_wildcard(payload_buf, topic_buf)) {
			acnt++;
		} else {
			log_err("wildcard check failed");
			return -1;
		}
		break;
	
	default:
		log_err("Should not be here");
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


	// printf("Publishing '%s' to '%s' ...\n", payload, topic);
	if ((rv = nng_sendmsg(sock, pubmsg, NNG_FLAG_NONBLOCK)) != 0) {
		fatal("nng_sendmsg", rv);
	}

	return rv;
}

int nnc_unsub_all(nng_socket sock, char **tq)
{
	nng_mqtt_topic topics[TOPIC_CNT];
	for (size_t i = 0; i < TOPIC_CNT; i++) {
		topics[i].buf = (uint8_t*) tq[i];
		topics[i].length = TOPIC_LEN;
	}

	int rv;

	// create a unsub message
	nng_msg *unsubmsg;
	nng_mqtt_msg_alloc(&unsubmsg, 0);
	nng_mqtt_msg_set_packet_type(unsubmsg, NNG_MQTT_UNSUBSCRIBE);
	nng_mqtt_msg_set_unsubscribe_topics(unsubmsg, topics, TOPIC_CNT);

	if ((rv = nng_sendmsg(sock, unsubmsg, NNG_FLAG_NONBLOCK)) != 0) {
		fatal("nng_sendmsg", rv);
		return rv;
	}

	return 0;
}

int
client(const char *url, nng_socket *sock_ret)
{
	nng_socket   sock;
	nng_dialer   dialer;
	int          rv;
	struct work *works[nwork];

	if ((rv = nng_mqtt_client_open(&sock)) != 0) {
		fatal("nng_socket", rv);
		return rv;
	}

	for (int i = 0; i < nwork; i++) {
		works[i] = alloc_work(sock);
	}

	// Mqtt connect message
	nng_msg *msg;
	nng_mqtt_msg_alloc(&msg, 0);
	nng_mqtt_msg_set_packet_type(msg, NNG_MQTT_CONNECT);
	nng_mqtt_msg_set_connect_keep_alive(msg, 60);
	nng_mqtt_msg_set_connect_clean_session(msg, false);
	nng_mqtt_msg_set_connect_user_name(msg, "nng_mqtt_client");
	nng_mqtt_msg_set_connect_password(msg, "secrets");

	nng_mqtt_set_connect_cb(sock, connect_cb, &sock);
	nng_mqtt_set_disconnect_cb(sock, disconnect_cb, NULL);

	if ((rv = nng_dialer_create(&dialer, sock, url)) != 0) {
		fatal("nng_dialer_create", rv);
	}

	nng_dialer_set_ptr(dialer, NNG_OPT_MQTT_CONNMSG, msg);
	nng_dialer_start(dialer, NNG_FLAG_NONBLOCK);

	for (int i = 0; i < nwork; i++) {
		sub_cb(works[i]);
	}

    *sock_ret = sock;
	return 0;

}

void test_random(const char *url)
{
    nng_socket sock;
    client(url, &sock);
	while (!is_sub_finished) {}
	int i = 0;

	while (acnt < TOPIC_CNT && i++ < 5) {
		acnt = 0;
		// In case receive last test publish message.
		nng_msleep(TOPIC_CNT);
		for (size_t j = 0 ; j < TOPIC_CNT; j++) {
			client_publish(sock, topic_que[j], (uint8_t*) topic_que[j], TOPIC_LEN, 0, false);
		}

		for (size_t k = 0; k < TOPIC_CNT; k++) {
			nng_msleep(10);
		}

		if (acnt == TOPIC_CNT) {
			break;
		} else {
			log_info("RANDOM TOPIC TEST FINISHED %d/%d! TRY IT AGAIN!", acnt, TOPIC_CNT);
		}
	}

	if (acnt == wildcard_acnt) {
		log_info("RANDOM TOPIC TEST FAILED, FINISHED %d/%d!", acnt, TOPIC_CNT);
	}

	nnc_unsub_all(sock, topic_que);	
	
}

void test_wildcard(const char *url)
{
    nng_socket sock;
    client(url, &sock);
	while (!is_sub_finished) {}

	int i = 0;
	while (acnt < wildcard_acnt && i++ < 5) {
		acnt = 0;
		// In case receive last test publish message.
		nng_msleep(TOPIC_CNT);
		for (size_t j = 0 ; j < TOPIC_CNT; j++) {
			client_publish(sock, normal_topic_que[j], (uint8_t*) wildcard_topic_que[j], TOPIC_LEN, 0, false);
		}

		for (size_t k = 0; k < TOPIC_CNT; k++) {
			nng_msleep(10);
		}

		if (acnt == wildcard_acnt) {
			break;
		} else {
			log_info("WILDCARD TOPIC TEST FINISHED %d/%d! TRY IT AGAIN!", acnt, wildcard_acnt);
		}
	}

	if (acnt == wildcard_acnt) {
		log_info("WILDCARD TOPIC TEST ALL %d/%d PASSED!", acnt, wildcard_acnt);
	}

	nnc_unsub_all(sock, wildcard_topic_que);
	
}


void test_clean_session(const char *url) 
{
	// TODO two connections, one for pub, one for sub.
	return;
}


void test_retain(const char *url) 
{

	return;
}


void test_last_will(const char *url)
{
	return;
}


int init_test()
{
	srand(time(NULL));
	if ((topic_que = str_arr_alloc(TOPIC_CNT, TOPIC_LEN)) == NULL) {
		return -1;
	}

  	if (-1 == mk_rnd_str_que(TOPIC_CNT, TOPIC_LEN, topic_que)) {
	 	log_err("make string queue failed!");
		goto exit;
  	}
	

#ifdef VERBOSE
	for (size_t i = 0; i < TOPIC_CNT; i++) {
		log_info("topic: %s", topic_que[i]);
	}
#endif

	if ((wildcard_topic_que = str_arr_alloc(TOPIC_CNT, TOPIC_LEN)) == NULL) {
		return -1;
	}

	if ((normal_topic_que = str_arr_alloc(TOPIC_CNT, TOPIC_LEN)) == NULL) {
		return -1;
	}

  	if (-1 == mk_rnd_wildcard_2str_que(TOPIC_CNT, TOPIC_LEN, wildcard_topic_que, normal_topic_que)) {
	 	log_err("make string queue failed!");
		goto exit;
  	}

	int last = 0;

	for (size_t i = 0; i < TOPIC_CNT; i++) {

		last = wildcard_acnt;
		if (check_wildcard(wildcard_topic_que[i], normal_topic_que[i])) {
			wildcard_acnt++;
		} 

#ifdef VERBOSE
		log_info("cnt: %d, topic: %s %s", wildcard_acnt, wildcard_topic_que[i], normal_topic_que[i]);
#endif
		
	}

	return 0;

exit:
	if (topic_que) {
		for (size_t i = 0; i < TOPIC_CNT; i++) {
			if (topic_que[i]) {
				free(topic_que[i]);
			}
		}
		free(topic_que);
	}

	if (wildcard_topic_que) {
		for (size_t i = 0; i < TOPIC_CNT; i++) {
			if (wildcard_topic_que[i]) {
				free(wildcard_topic_que[i]);
			}
		}
		free(wildcard_topic_que);
	}

	if (normal_topic_que) {
		for (size_t i = 0; i < TOPIC_CNT; i++) {
			if (normal_topic_que[i]) {
				free(normal_topic_que[i]);
			}
		}
		free(normal_topic_que);
	}
	return -1;
}

int run_test(const char *url)
{
	test_state = TEST_RANDOM;
    test_random(url);
	acnt = 0;
	is_sub_finished = false;
	test_state = TEST_WILDCARD;
    test_wildcard(url);
    test_clean_session(url);
    test_last_will(url);
    return 0;
}
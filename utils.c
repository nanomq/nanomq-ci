#include "utils.h"
#include "dbg.h"
#include <time.h>
#include <stdbool.h>

static char charset[] = "/abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";
static char charset_wildcard[] = "#+/abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";
// static char charset[] = "/abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789,.-?!";


int mk_rnd_str(size_t len, char *rnd_str) 
{ 
    if (len <= 0 || !rnd_str) {
        log_err("input param illegal");
        return -1;
    }

    int l = (int) (sizeof(charset) -1);
    for (int n = 0;n < len;n++) {
        int key = rand() % l;
        rnd_str[n] = charset[key];

    }
    rnd_str[len] = '\0';
    return 0;
}

int mk_rnd_2str_wildcard(size_t len, char *rnd_str, char *n_rnd_str)
{
    char wildcard[] = "#+";
    if (len <= 0 || !rnd_str || !n_rnd_str ) {
        log_err("input param illegal");
        return -1;
    }

    int rv = 0;
    int cl = sizeof(charset) - 1;

    switch (len) {
        case 1:
            // only + or # 
            rnd_str[0] = wildcard[rand() % 2];
            n_rnd_str[0] = charset[rand() % cl];
            break;
        case 2:
            // /# /+ +/
            if ((rv = rand() % 3) == 0) {
                memcpy(rnd_str, "/#", len);
                n_rnd_str[0] = '/';
                n_rnd_str[1] = charset[rand() % cl];
            } else if (rv == 1) {
                memcpy(rnd_str, "/+", len);
                n_rnd_str[0] = '/';
                n_rnd_str[1] = charset[rand() % cl];
            } else if (rv ==2) {
                memcpy(rnd_str, "+/", len);
                n_rnd_str[0] = charset[rand() % cl];
                n_rnd_str[1] = '/';
            }
            break;
        default:;
            int l = (int) (sizeof(charset_wildcard) -1);
            bool is_hashtag = false;
            for (int n = 0; n < len; n++) {
                int key = rand() % l;
                if (key == 0) {
                    is_hashtag = true;
                    rnd_str[n] = charset[rand() % (l-2)];
                    n_rnd_str[n] = rnd_str[n];
                } else if (key == 1) {
                    // TODO
                    if (n == 0) {

                        n_rnd_str[0] = charset[rand() % cl];
                        n_rnd_str[1] = '/';
                        rnd_str[n] = charset[rand() % (l-2)];
                        memcpy(rnd_str, "+/", 2);
                        n++;
                    } else if (n == len-1) {
                        n_rnd_str[n-1] = '/';
                        n_rnd_str[n] = charset[rand() % cl];
                        memcpy(rnd_str+n-1, "/+", 2);
                    } else {
                        n_rnd_str[n-1] = '/';
                        n_rnd_str[n] = charset[rand() % cl];
                        n_rnd_str[n+1] = '/';
                        memcpy(rnd_str+n-1, "/+/", 3);
                        n++;
                    }

                } else {
                    rnd_str[n] = charset_wildcard[key];
                    n_rnd_str[n] = rnd_str[n];
                }
            }

            if (is_hashtag) {
                memcpy(rnd_str+len-2, "/#", 2);
                n_rnd_str[len-2] = '/';
                n_rnd_str[len-1] = charset[rand() % cl];
            }
    }
    rnd_str[len] = '\0';
    n_rnd_str[len] = '\0';

    return 0;

}

int mk_rnd_str_wildcard(size_t len, char *rnd_str)
{
    char wildcard[] = "#+";
    if (len <= 0 || !rnd_str) {
        log_err("input param illegal");
        return -1;
    }

    int rv = 0;

    switch (len) {
        case 1:
            // only + or # 
            rnd_str[0] = wildcard[rand() % 2];
            break;
        case 2:
            // /# /+ +/
            if ((rv = rand() % 3) == 0) {
                memcpy(rnd_str, "/#", len);
            } else if (rv == 1) {
                memcpy(rnd_str, "/+", len);
            } else if (rv ==2) {
                memcpy(rnd_str, "+/", len);
            }
            break;
        default:;
            int l = (int) (sizeof(charset_wildcard) -1);
            bool is_hashtag = false;
            for (int n = 0; n < len; n++) {
                int key = rand() % l;
                if (key == 0) {
                    is_hashtag = true;
                    rnd_str[n] = charset[rand() % (l-2)];
                } else if (key == 1) {
                    // TODO
                    if (n == 0) {
                        memcpy(rnd_str, "+/", 2);
                        n++;
                    } else if (n == len-1) {
                        memcpy(rnd_str+n-1, "/+", 2);
                    } else {
                        memcpy(rnd_str+n-1, "/+/", 3);
                        n++;
                    }

                } else {
                    rnd_str[n] = charset_wildcard[key];
                }
            }

            if (is_hashtag) {
                memcpy(rnd_str+len-2, "/#", 2);
            }
    }
    rnd_str[len] = '\0';

    return 0;

}

int mk_rnd_wildcard_2str_que(size_t size, size_t len, char **wildcard_que, char **normal_que)
{
    if (!size || !len || !wildcard_que || !normal_que) {
        log_err("input param illegal");
        return -1;
    }

    for (size_t i = 0; i < size; i++) {
        if (-1 == mk_rnd_2str_wildcard(len, wildcard_que[i], normal_que[i])) {
            log_err("make wildcard random string error.");
            return -1;
        }
    }

    return 0;
}

int mk_rnd_wildcard_str_que(size_t size, size_t len, char **rnd_str_que)
{
    if (!size || !len || !rnd_str_que) {
        log_err("input param illegal");
        return -1;
    }

    for (size_t i = 0; i < size; i++) {
        if (-1 == mk_rnd_str_wildcard(len, rnd_str_que[i])) {
            log_err("make wildcard random string error.");
            return -1;
        }
    }

    return 0;
}

int mk_rnd_str_que(size_t size, size_t len, char **rnd_str_que) 
{
    if (!size || !len || !rnd_str_que) {
        log_err("input param illegal");
        return -1;
    }

    for (size_t i = 0; i < size; i++) {
        if (-1 == mk_rnd_str(len, rnd_str_que[i])) {
            log_err("make random string error.");
            return -1;
        }
    }

    return 0;
}


int assert_str(const char *s1, const char *s2, size_t len)
{
    if (!strncmp(s1, s2, len)) {
        return 0;
    } else {
        log_err("[LEFT]: %s, [RIGHT]: %s", s1, s2);
        return -1;
    }
}

#include "utils.h"
#include "dbg.h"
#include <time.h>

static char charset[] = "/abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";
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

        // if (charset[key] == '/') {
        //     if (n == 0 || n == len - 1 || rnd_str[n-1] == '/') {
        //             rnd_str[n] = charset[n % (l-1) + 1];
        //     } else {
        //             rnd_str[n] = charset[key];
        //     }
        // } else {
            rnd_str[n] = charset[key];

        // }

    }
    rnd_str[len] = '\0';
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
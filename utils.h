#ifndef UTILS_H
#define UTILS_H

#include <assert.h>
#include <stdio.h>
#include <stdlib.h>

int mk_rnd_str(size_t len, char *rnd_str);
int mk_rnd_str_que(size_t size, size_t len, char **rnd_str_que);
int assert_str(const char *s1, const char *s2, size_t len);

#endif

#ifndef UTILS_H
#define UTILS_H

#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>

int mk_rnd_str(size_t len, char *rnd_str);
int mk_rnd_str_que(size_t size, size_t len, char **rnd_str_que);

int mk_rnd_wildcard_str(size_t len, char *rnd_str);
int mk_rnd_wildcard_str_que(size_t size, size_t len, char **rnd_str_que);

int mk_rnd_2str_wildcard(size_t len, char *rnd_str, char *n_rnd_str);
int mk_rnd_wildcard_2str_que(size_t size, size_t len, char **wildcard_que, char **normal_que);

int assert_str(const char *s1, const char *s2, size_t len);


#endif

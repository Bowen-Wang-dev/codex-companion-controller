#pragma once
#include <stdbool.h>
#include "cJSON.h"
void network_start(void);
void network_arm(void);
bool network_pairing_armed(void);
bool network_provision(cJSON *message);
const char *network_status(void);
bool network_receive(char *out, unsigned size);
bool network_send(const char *frame,bool urgent);

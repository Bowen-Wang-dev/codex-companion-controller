#pragma once
#include <stdbool.h>
#ifndef COMPANION_DEFAULT_ENGLISH
#define COMPANION_DEFAULT_ENGLISH 0
#endif
#if COMPANION_DEFAULT_ENGLISH
#define COMPANION_UI_LANGUAGE "en"
#else
#define COMPANION_UI_LANGUAGE "zh-CN"
#endif
const char *device_text(bool english,const char *source);
const char *device_language(void);

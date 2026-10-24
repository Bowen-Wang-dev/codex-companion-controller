#pragma once
void battery_start(void);
// The device fuel-gauge SOC, or -1 when absent/not ready/read failed.
int battery_percent(void);

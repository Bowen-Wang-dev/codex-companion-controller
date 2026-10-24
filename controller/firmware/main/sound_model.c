#include "sound_model.h"
static const sound_note_t permission[]={{1200,180},{0,120},{1200,180},{0,120},{1200,180}};
static const sound_note_t completed[]={{900,110},{0,40},{1200,110},{0,40},{1600,160}};
static const sound_note_t failed[]={{700,150},{0,80},{380,230}};
static const sound_note_t disconnected[]={{260,120}};
static const sound_note_t exhausted[]={{330,130},{0,100},{330,130},{0,100},{270,200}};
static const sound_note_t allowed[]={{1800,110}};
static const sound_note_t denied[]={{420,150},{0,80},{320,180}};
static const sound_note_t touch[]={{1500,65}};
static const sound_note_t preview[]={{1200,180}};
typedef struct { const sound_note_t *notes; size_t count; } plan_t;
#define PLAN(name) {name,sizeof(name)/sizeof(name[0])}
static const plan_t plans[]={PLAN(permission),PLAN(completed),PLAN(failed),PLAN(disconnected),
 PLAN(exhausted),PLAN(allowed),PLAN(denied),PLAN(touch),PLAN(preview)};
size_t sound_notes(sound_kind_t kind,const sound_note_t **notes) {
 if(kind<0 || kind>=SOUND_COUNT) { *notes=0; return 0; }
 *notes=plans[kind].notes; return plans[kind].count;
}
int sound_priority(sound_kind_t kind) { return kind==SOUND_PERMISSION?100:10; }
static int clamp(int value) { return value<0?0:value>100?100:value; }
int sound_volume_step(int value,int direction) {
 value=((clamp(value)+5)/10)*10;
 return clamp(value+(direction>0?10:direction<0?-10:0));
}
// Demo's softened electronic waveform, using integer DDS on ESP32-C3.
static const int16_t wave[64]={
 0,5620,10344,13686,15892,17279,18136,18665,
 18995,19204,19338,19427,19486,19525,19550,19564,
 19568,19564,19550,19525,19486,19427,19338,19204,
 18995,18665,18136,17279,15892,13686,10344,5620,
 0,-5620,-10344,-13686,-15892,-17279,-18136,-18665,
 -18995,-19204,-19338,-19427,-19486,-19525,-19550,-19564,
 -19568,-19564,-19550,-19525,-19486,-19427,-19338,-19204,
 -18995,-18665,-18136,-17279,-15892,-13686,-10344,-5620
};
void sound_pcm(sound_pcm_t *state,int hz,int total,int offset,int16_t *pcm,int count,int volume) {
 volume=clamp(volume);
 uint32_t step=hz>0?(uint32_t)(((uint64_t)hz<<32)/16000):0;
 for(int i=0;i<count;i++) {
  int n=offset+i, ramp=n;
  if(total-1-n<ramp)ramp=total-1-n;
  if(ramp<0)ramp=0;
  if(ramp>80)ramp=80;
  pcm[i]=hz>0?(int16_t)((int32_t)wave[state->phase>>26]*volume*ramp/8000):0;
  state->phase+=step;
 }
}

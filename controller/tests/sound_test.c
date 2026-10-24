#include "../firmware/main/sound_model.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
int main(void) {
 const sound_note_t *notes; size_t count=sound_notes(SOUND_PERMISSION,&notes);
 assert(count==5); int ms=0,beeps=0;
 for(size_t i=0;i<count;i++) {
  ms+=notes[i].ms;
  if(notes[i].hz) { assert(notes[i].hz==1200 && notes[i].ms==180); beeps++; }
  else assert(notes[i].ms==120);
 }
 assert(ms==780 && beeps==3);
 for(int k=1;k<SOUND_COUNT;k++) {
  assert(sound_notes((sound_kind_t)k,&notes)>0);
  assert(sound_priority(SOUND_PERMISSION)>sound_priority((sound_kind_t)k));
 }
 assert(sound_volume_step(0,-1)==0 && sound_volume_step(100,1)==100);
 assert(sound_volume_step(20,1)==30 && sound_volume_step(20,-1)==10);
 int16_t pcm[2880]; sound_pcm_t state={0};
 sound_pcm(&state,1200,2880,0,pcm,2880,20);
 int peak=0,crossings=0;
 for(int i=0;i<2880;i++) {
  if(abs(pcm[i])>peak)peak=abs(pcm[i]);
  if(i>80 && i<2800 && pcm[i-1]<=0 && pcm[i]>0)crossings++;
 }
 // 20% is linear PCM amplitude, not a second -40 dB codec attenuation.
 assert(peak>3800 && peak<4000);
 assert(crossings>=202 && crossings<=205);
 assert(pcm[0]==0 && pcm[2879]==0);
 state.phase=0;sound_pcm(&state,1200,2880,0,pcm,2880,0);
 for(int i=0;i<2880;i++)assert(pcm[i]==0);
 state.phase=0;sound_pcm(&state,0,2880,0,pcm,2880,100);
 for(int i=0;i<2880;i++)assert(pcm[i]==0);
 state.phase=0;sound_pcm(&state,1200,2880,0,pcm,2880,100);
 for(int i=0;i<2880;i++)assert(abs(pcm[i])<=19661);
 puts("sound: pager timing, waveform, linear gain, mute and volume bounds passed");
}

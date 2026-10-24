#include "../firmware/main/controller.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
static void tap(controller_t *s,int key,int64_t at) { controller_press(s,key,at); controller_release(s,key,at+100); }
int main(void) {
 controller_t s; controller_init(&s);
 uint32_t view=controller_view_hash(&s);
 s.sequence=99;s.last_rx=123;s.expires=555;s.utc=1700000000;s.clock_at=88;
 assert(controller_view_hash(&s)==view); // Transport ticks don't rebuild LVGL.
 s.page=1;assert(controller_view_hash(&s)!=view);s.page=0;
 controller_press(&s,1,100); assert(s.page==0); controller_release(&s,1,200); assert(s.page==1);
 controller_press(&s,1,300); controller_tick(&s,950); assert(s.page==2);
 controller_tick(&s,2000); assert(s.page==2); controller_release(&s,1,2100); assert(s.page==2);
 tap(&s,1,2200); assert(s.page==3);
 tap(&s,1,2400); assert(s.page==3 && s.option==1);
 controller_press(&s,1,2600); controller_tick(&s,3250); assert(s.page==4 && s.option==0);
 controller_release(&s,1,3400); assert(s.page==4 && s.option==0);
 s.history_count=3; tap(&s,1,3500); assert(s.page==4 && s.option==1);
 controller_press(&s,1,3700); controller_release(&s,1,4350); assert(s.page==5);
 tap(&s,1,4400); assert(s.page==0);
 s.online=true; s.last_rx=5000; controller_request(&s,"r1"); s.expires=99999;
 tap(&s,0,5100); assert(s.selected==-1 && s.stage==0);
 tap(&s,2,5300); assert(s.stage==0); // incomplete scope: never allow
 tap(&s,1,5500); tap(&s,2,5700); assert(s.stage==1);
 controller_press(&s,2,6000); assert(controller_tick(&s,6999)==ACTION_NONE);
 assert(controller_tick(&s,7000)==ACTION_DENY); assert(controller_tick(&s,7100)==ACTION_NONE);
 controller_release(&s,2,7200); assert(s.stage==2);
 controller_request(&s,"r2"); s.expires=99999; s.last_rx=7500;
 tap(&s,1,7500); tap(&s,2,7700); assert(s.stage==1);
 controller_press(&s,0,7900); assert(controller_tick(&s,8550)==ACTION_NONE);
 assert(s.stage==0 && s.selected==-1 && !s.request_visible && s.request);
 controller_release(&s,0,8600);
 controller_press(&s,2,8700); controller_tick(&s,9350); assert(s.request_visible);
 controller_release(&s,2,9400);
 s.last_rx=0; controller_tick(&s,10000); assert(!s.online && s.stage==0 && s.selected==-1);
 s.expires=10001; controller_tick(&s,10002); assert(!s.request);
 controller_init(&s); s.primary=0; tap(&s,0,100); assert(s.page==2);
 controller_init(&s); s.secondary=0; tap(&s,0,100); assert(s.page==2);
 // Reset requires two short confirmations, then a fresh one-second hold.
 controller_init(&s); s.page=2; s.online=true; s.last_rx=1000; s.resets=2; strcpy(s.reset_id,"offer");
 tap(&s,2,1000); assert(s.reset_stage==1);
 tap(&s,2,1200); assert(s.reset_stage==2);
 controller_press(&s,2,1400); assert(controller_tick(&s,2399)==ACTION_NONE);
 assert(controller_tick(&s,2400)==ACTION_RESET); assert(controller_tick(&s,2500)==ACTION_NONE);
 assert(controller_release(&s,2,2550)==ACTION_NONE);
 // Leaving or disconnecting cancels the confirmation, never spending a reset.
 s.reset_stage=2; s.last_rx=2600; controller_press(&s,0,2600);
 assert(controller_tick(&s,3250)==ACTION_NONE); assert(s.page==1 && s.reset_stage==0);
 controller_release(&s,0,3300);
 s.page=2; s.reset_stage=2; s.online=false; controller_press(&s,2,3500);
 assert(controller_tick(&s,4500)==ACTION_NONE); controller_release(&s,2,4600);
 // A zero balance cannot even enter confirmation.
 controller_init(&s); s.online=true; s.last_rx=1000; s.page=2; s.resets=0; strcpy(s.reset_id,"offer");
 tap(&s,2,1000); assert(s.reset_stage==0);
 // Complete low-risk approval has the same fresh-hold rule; no choice is preselected.
 controller_init(&s); s.online=true; s.last_rx=1000; controller_request(&s,"allow-test"); s.expires=10000; s.can_allow=true;
 tap(&s,2,1000); assert(s.stage==0 && s.selected==-1);
 tap(&s,0,1200); tap(&s,2,1400); assert(s.stage==1);
 controller_press(&s,2,1600); assert(controller_tick(&s,2599)==ACTION_NONE);
 assert(controller_tick(&s,2600)==ACTION_ALLOW); assert(controller_release(&s,2,2700)==ACTION_NONE);
 // A directory-grant notification is informational: buttons never synthesize
 // a native permission grant/denial. OK only silences its pager reminder.
 controller_init(&s); s.online=true; s.last_rx=1000; controller_request(&s,"directory-notice");
 s.expires=10000; s.can_allow=false; s.can_deny=false;
 tap(&s,0,1000); tap(&s,1,1200); assert(s.selected==-1 && s.stage==0);
 controller_press(&s,2,1400); assert(controller_release(&s,2,1500)==ACTION_MUTE);
 assert(s.muted && s.stage==0);
 controller_press(&s,2,1600); assert(controller_tick(&s,2600)==ACTION_MUTE);
 assert(controller_release(&s,2,2700)==ACTION_NONE && s.stage==0);
 // Volume is an explicit editor: 10% steps, inclusive bounds, no wrapping.
 controller_init(&s); assert(s.volume==20); s.page=3; s.option=3;
 tap(&s,2,1000); assert(s.volume_edit && s.volume==20);
 tap(&s,0,1200); assert(s.volume==30 && s.option==3 && s.page==3);
 tap(&s,1,1400); assert(s.volume==20);
 for(int i=0;i<20;i++)tap(&s,1,1600+i*200);
 assert(s.volume==0 && s.volume_edit);
 for(int i=0;i<20;i++)tap(&s,0,6000+i*200);
 assert(s.volume==100 && s.volume_edit);
 tap(&s,2,10500); assert(!s.volume_edit && s.volume==100);
 tap(&s,1,10700); assert(s.option==4 && s.volume==100);
 s.option=3; tap(&s,2,10900); assert(s.volume_edit);
 controller_press(&s,1,11100); controller_tick(&s,11750);
 assert(s.page==4 && !s.volume_edit && s.volume==100);
 controller_release(&s,1,11900);
 controller_init(&s); s.page=3; s.option=1;
 controller_press(&s,2,12000);
 assert(controller_release(&s,2,12100)==ACTION_TEST_AUDIO);
 // A reply reminder can be acknowledged, but can never approve a scope.
 controller_init(&s); s.online=true; s.last_rx=1000; controller_request(&s,"human-input");
 s.expires=10000; s.user_input=true; s.can_allow=false; s.can_deny=false;
 controller_press(&s,2,1100); assert(controller_release(&s,2,1200)==ACTION_DISMISS);
 assert(!s.request_visible && s.page==0 && s.stage==0);
 s.request_visible=true; s.can_allow=true; s.selected=0; s.stage=1;
 controller_press(&s,2,1400); assert(controller_tick(&s,2400)==ACTION_NONE);
 assert(controller_release(&s,2,2500)==ACTION_NONE);
 // Detail navigation cannot select/confirm approval. Loading a page is async;
 // stale packets cannot unlock or overwrite the selected page.
 controller_init(&s);s.online=true;s.last_rx=1000;
 controller_request(&s,"paged");s.expires=99999;s.can_allow=true;
 controller_review_snapshot(&s,0,3,"first");
 assert(s.review_protocol==1 && !controller_review_final(&s));
 tap(&s,0,1100);assert(s.review_page==0 && s.selected==-1);
 tap(&s,2,1300);assert(s.stage==0 && s.selected==-1);
 tap(&s,1,1500);assert(s.review_page==1 && s.selected==-1);
 tap(&s,1,1700);assert(s.review_page==1); // Wait for page content before another turn.
 controller_review_snapshot(&s,0,3,"stale");assert(s.review_loaded==-1);
 assert(!controller_review_final(&s));
 controller_review_snapshot(&s,1,3,"second");tap(&s,1,1900);
 controller_review_snapshot(&s,2,3,"last detail");tap(&s,1,2100);
 assert(s.review_page==3 && !controller_review_final(&s));
 tap(&s,0,2300);tap(&s,2,2500);assert(s.selected==-1 && s.stage==0);
 controller_review_snapshot(&s,3,3,"");assert(controller_review_final(&s));
 controller_review_snapshot(&s,2,3,"late");assert(s.review_loaded==-1 && !controller_review_final(&s));
 controller_review_snapshot(&s,3,3,"");assert(controller_review_final(&s));
 tap(&s,0,2700);tap(&s,2,2900);assert(s.stage==1 && s.selected==0);
 controller_press(&s,0,3100);assert(controller_tick(&s,3750)==ACTION_REVIEW);
 assert(s.review_page==0 && s.stage==0 && s.selected==-1 && s.request_visible);
 controller_release(&s,0,3800);
 // After re-reading, the final allow still needs a fresh short OK then hold.
 for(int i=0;i<3;i++) { controller_review_snapshot(&s,i,3,"review");tap(&s,1,3900+i*200); }
 controller_review_snapshot(&s,3,3,"");s.last_rx=4500;
 tap(&s,0,4500);tap(&s,2,4700);controller_press(&s,2,4900);
 assert(controller_tick(&s,5899)==ACTION_NONE);assert(controller_tick(&s,5900)==ACTION_ALLOW);
 assert(controller_release(&s,2,6000)==ACTION_NONE);
 controller_request(&s,"replacement");assert(s.review_page==0 && s.review_protocol==0 && s.selected==-1);
 puts("controller: navigation/hold/permission/expiry/disconnect/input-notice/paged-review assertions passed");
}

"""Render the actual firmware render() with local LVGL and mocked hardware.

Run on a host with CMake, a C compiler and the locked LVGL component available.
Output stays private; --private-artwork includes local Apple assets only.
No device access or network requests. This is layout QA, not hardware acceptance.
"""
import argparse
import json
from pathlib import Path
import struct
import subprocess
import zlib

ROOT=Path(__file__).resolve().parents[1]


def png(path,width,height,rgb):
    def chunk(kind,data):
        return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
    rows=b''.join(b'\0'+rgb[y*width*3:(y+1)*width*3] for y in range(height))
    path.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>2I5B',width,height,8,2,0,0,0))+
                     chunk(b'IDAT',zlib.compress(rows))+chunk(b'IEND',b''))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--private-artwork',action='store_true')
    args=parser.parse_args()
    work=ROOT/'private/ui-preview';work.mkdir(parents=True,exist_ok=True)
    source=(ROOT/'firmware/main/main.c').read_text(encoding='utf-8')
    render=source[source.index('static lv_obj_t *label('):source.index('void app_main(void)')]
    header=r'''
#include "lvgl.h"
#include "controller.h"
#include "ui_language.h"
#include "sound.h"
#include <stdio.h>
#include <inttypes.h>
#include <string.h>
#include <time.h>
LV_FONT_DECLARE(ui_font)
static controller_t s;
static bool armed;
static int64_t now_ms(void){return 10000;}
static bool bsp_lvgl_lock(int timeout){(void)timeout;return true;}
static void bsp_lvgl_unlock(void){}
static int battery_percent(void){return 76;}
sound_health_t sound_health(void){return (sound_health_t){.state=SOUND_READY};}
static bool network_pairing_armed(void){return armed;}
static const char *network_status(void){return armed?"请在 PC 端运行无线配对":"正在连接 Wi-Fi";}
'''
    if args.private_artwork:
        if not (ROOT/'firmware/main/pet_assets.h').is_file():raise FileNotFoundError('Private artwork missing')
        header+='#define HAVE_PETS 1\n#include "pet_assets.h"\n'
    else:header+='#define HAVE_PETS 0\n'
    harness=r'''
static uint16_t pixels[240*320],draw_buffer[240*320];
static void flush(lv_display_t *display,const lv_area_t *area,uint8_t *map){
 uint16_t *source=(uint16_t *)map;
 for(int y=area->y1;y<=area->y2;y++)for(int x=area->x1;x<=area->x2;x++)pixels[y*240+x]=*source++;
 lv_display_flush_ready(display);
}
static void json_text(FILE *f,const char *text){
 fputc('"',f);for(const unsigned char *p=(const unsigned char *)text;*p;p++){
  if(*p=='"'||*p=='\\')fputc('\\',f);
  if(*p=='\n'){fputs("\\n",f);continue;}fputc(*p,f);
 }fputc('"',f);
}
static void labels(FILE *f,lv_obj_t *parent){
 uint32_t count=lv_obj_get_child_count(parent);
 for(uint32_t i=0;i<count;i++){
  lv_obj_t *child=lv_obj_get_child(parent,i);
  if(lv_obj_check_type(child,&lv_label_class)){
   lv_point_t size;const char *text=lv_label_get_text(child);
   lv_text_get_size(&size,text,lv_obj_get_style_text_font(child,0),lv_obj_get_style_text_letter_space(child,0),
       lv_obj_get_style_text_line_space(child,0),lv_obj_get_width(child),LV_TEXT_FLAG_NONE);
   int x=lv_obj_get_x(child),width=lv_obj_get_width(child);
   lv_text_align_t align=lv_obj_get_style_text_align(child,0);
   if(align==LV_TEXT_ALIGN_RIGHT)x+=width-size.x;
   else if(align==LV_TEXT_ALIGN_CENTER)x+=(width-size.x)/2;
   fprintf(f,"{\"x\":%d,\"y\":%d,\"width\":%d,\"text_width\":%d,\"text_height\":%d,\"text\":",x,(int)lv_obj_get_y(child),width,(int)size.x,(int)size.y);
   json_text(f,text);fputs("}\n",f);
  }else if(lv_obj_check_type(child,&lv_image_class)){
   fprintf(f,"{\"x\":%d,\"y\":%d,\"width\":%d,\"text_width\":0,\"text_height\":0,\"image\":true,\"text\":\"\"}\n",(int)lv_obj_get_x(child),(int)lv_obj_get_y(child),(int)lv_obj_get_width(child));
  }labels(f,child);
 }
}
int main(void){
 lv_init();lv_display_t *display=lv_display_create(240,320);
 lv_display_set_color_format(display,LV_COLOR_FORMAT_RGB565);
 lv_display_set_buffers(display,draw_buffer,NULL,sizeof(draw_buffer),LV_DISPLAY_RENDER_MODE_FULL);
 lv_display_set_flush_cb(display,flush);
 for(int english=0;english<2;english++)for(int scenario=0;scenario<20;scenario++){
  controller_init(&s);s.english=english;s.online=true;s.last_rx=10000;s.utc=1793700000;s.clock_at=10000;
  s.primary=82;s.secondary=64;s.resets=2;s.minutes[0]=300;s.minutes[1]=10080;
  s.resets_at[0]=s.utc+7200;s.resets_at[1]=s.utc+86400;strcpy(s.transport,"wifi");
  strcpy(s.billing,"token");strcpy(s.token_model,"gpt-6.1-sol");strcpy(s.token_cost_currency,"USD");
  s.token_updated=s.token_total_updated=s.token_priced=true;s.token_cost_last=1.2345;s.token_cost_total=12.3456;
  s.token_cost_last_parts_valid=s.token_cost_total_parts_valid=true;
  for(int i=0;i<6;i++){s.token_last[i]=1000*(i+1);s.token_total[i]=10000*(i+1);s.token_cost_last_parts[i%5]=0.1234;s.token_cost_total_parts[i%5]=1.2345;}
  armed=false;
  if(scenario<6)s.page=scenario;
  if(scenario==4){s.history_count=1;strcpy(s.history[0],english?"Approval delivered to Codex":"批准已送达 Codex");}
  if(scenario==5)strcpy(s.hook_status,english?"App approvals connected":"App 实体审批已接入");
  if(scenario==6){s.page=5;s.online=false;armed=true;}
  if(scenario>=7&&scenario<=11){
   controller_request(&s,"preview-request");s.review_protocol=1;s.review_total=2;s.review_page=0;s.review_loaded=0;
   s.can_allow=s.can_deny=true;s.expires=100000;
   strcpy(s.command,english?"Command approval":"命令执行审批");
   strcpy(s.scope,english?"This turn only; no persistent permission":"仅本轮，不保存长期权限");
   strcpy(s.review_text,english?"Request this\noperation\npwd\nWorking dir:\n/test/project":"请求执行操作\npwd\n工作目录：\n/test/project");
   if(scenario>=8){s.review_page=s.review_total;s.review_loaded=s.review_page;}
   if(scenario==9){s.stage=1;s.selected=0;}
   if(scenario==10){s.stage=1;s.selected=1;}
   if(scenario==11)s.user_input=true;
  }
  if(scenario==12){s.page=1;s.meter_stage=1;}
  if(scenario>=13&&scenario<=15){strcpy(s.billing,"subscription");s.page=scenario==13?0:2;s.reset_stage=scenario==14?1:scenario==15?2:0;}
  if(scenario==16||scenario==17){strcpy(s.face,"delight");strcpy(s.receipt,scenario==16?(english?"Approval delivered to Codex":"批准已送达 Codex"):(english?"Receipt unconfirmed; check host":"回执未确认 · 请在 PC 端查看"));}
  if(scenario==18){strcpy(s.state,"approval_sent");}
  if(scenario==19){s.online=false;strcpy(s.state,"failed");strcpy(s.face,"crying");}
  render();lv_obj_update_layout(lv_screen_active());lv_refr_now(display);
  char name[80];snprintf(name,sizeof(name),"%s-%02d.ppm",english?"en":"zh",scenario);
  FILE *f=fopen(name,"wb");fprintf(f,"P6\n240 320\n255\n");
  for(int i=0;i<240*320;i++){
   unsigned v=pixels[i];unsigned char rgb[]={((v>>11)&31)*255/31,((v>>5)&63)*255/63,(v&31)*255/31};fwrite(rgb,1,3,f);
  }fclose(f);
  snprintf(name,sizeof(name),"%s-%02d.jsonl",english?"en":"zh",scenario);
  f=fopen(name,"w");labels(f,lv_screen_active());fclose(f);
 }
 return 0;
}
'''
    (work/'preview.c').write_text(header+render+harness,encoding='utf-8')
    cmake='''cmake_minimum_required(VERSION 3.16)
project(firmware_preview C)
set(CONFIG_LV_BUILD_DEMOS OFF CACHE BOOL "" FORCE)
set(CONFIG_LV_BUILD_EXAMPLES OFF CACHE BOOL "" FORCE)
set(CONFIG_LV_USE_THORVG_INTERNAL OFF CACHE BOOL "" FORCE)
add_compile_definitions(LV_CONF_SKIP LV_FONT_MONTSERRAT_12=1 LV_FONT_MONTSERRAT_20=1 LV_COLOR_DEPTH=16 LV_USE_STDLIB_MALLOC=LV_STDLIB_CLIB)
add_subdirectory("'''+str(ROOT/'firmware/managed_components/lvgl__lvgl')+'''" lvgl)
add_executable(preview preview.c "'''+str(ROOT/'firmware/main/ui_font.c')+'''" "'''+str(ROOT/'firmware/main/controller.c')+'''" "'''+str(ROOT/'firmware/main/ui_language.c')+'''" "'''+str(ROOT/'firmware/main/sound_model.c')+'''")
target_include_directories(preview PRIVATE "'''+str(ROOT/'firmware/main')+'''")
target_link_libraries(preview PRIVATE lvgl m)
'''
    (work/'CMakeLists.txt').write_text(cmake,encoding='utf-8')
    (work/'lv_conf.h').write_text('#pragma once\n',encoding='utf-8')
    subprocess.run(['cmake','-S',str(work),'-B',str(work/'build')],check=True)
    subprocess.run(['cmake','--build',str(work/'build'),'-j','4'],check=True)
    subprocess.run([str(work/'build/preview')],cwd=work,check=True)
    for language in ('en','zh'):
        sheet=bytearray(240*4*320*5*3)
        for index in range(20):
            name=f'{language}-{index:02d}'
            rgb=(work/(name+'.ppm')).read_bytes().split(b'\n',3)[3]
            png(work/(name+'.png'),240,320,rgb)
            x,y=(index%4)*240,(index//4)*320
            for row in range(320):sheet[((y+row)*960+x)*3:((y+row)*960+x+240)*3]=rgb[row*720:(row+1)*720]
        png(work/(language+'-contact-sheet.png'),960,1600,sheet)
    findings=[]
    for path in sorted(work.glob('??-??.jsonl')):
        labels=[json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]
        for index,label in enumerate(labels):
            if label['y']+label['text_height']>320:findings.append((path.name,'outside screen',label['text']))
            if not label['text'].strip():continue
            for other in labels[:index]:
                if not other['text'].strip():continue
                if (max(label['x'],other['x'])<min(label['x']+label['text_width'],other['x']+other['text_width'])
                        and max(label['y'],other['y'])<min(label['y']+label['text_height'],other['y']+other['text_height'])):
                    findings.append((path.name,'text overlap',label['text'],other['text']))
    (work/'layout-findings.json').write_text(json.dumps(findings,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Rendered 40 firmware screens with actual LVGL / fonts to',work,'; layout findings:',len(findings))
    if findings:raise SystemExit('Firmware layout findings require review; see layout-findings.json')


if __name__=='__main__':main()

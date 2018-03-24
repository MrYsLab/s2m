"""
 Copyright (c) 2017 Alan Yorinks All rights reserved.
 This program is free software; you can redistribute it and/or
 modify it under the terms of the GNU AFFERO GENERAL PUBLIC LICENSE
 Version 3 as published by the Free Software Foundation; either
 or (at your option) any later version.
 This library is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 General Public License for more details.
 You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
 along with this library; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 Last modified 24 March 2018
"""
from microbit import*
def loop(digital_outputs):
 while True:
  data=uart.readline()
  sleep(8)
  if data:
   cmd=str(data,'utf-8').rstrip()
   if not len(cmd):
    continue
   cmd_list=cmd.split(",")
   try:
    cmd_id=cmd_list[0]
   except IndexError:
    cmd_id='z'
    continue
   if cmd_id=='d':
    image_dict={"HAPPY":Image.HAPPY,"SAD":Image.SAD,"ANGRY":Image.ANGRY,"SMILE":Image.SMILE,"CONFUSED":Image.CONFUSED,"ASLEEP":Image.ASLEEP,"SURPRISED":Image.SURPRISED,"SILLY":Image.SILLY,"FABULOUS":Image.FABULOUS,"MEH":Image.MEH,"YES":Image.YES,"NO":Image.NO,"RABBIT":Image.RABBIT,"COW":Image.COW,"ROLLERSKATE":Image.ROLLERSKATE,"HOUSE":Image.HOUSE,"SNAKE":Image.SNAKE,"HEART":Image.HEART,"DIAMOND":Image.DIAMOND,"DIAMOND_SMALL":Image.DIAMOND_SMALL,"SQUARE":Image.SQUARE,"SQUARE_SMALL":Image.SQUARE_SMALL,"TRIANGLE":Image.TRIANGLE,"TARGET":Image.TARGET,"STICKFIGURE":Image.STICKFIGURE,"ARROW_N":Image.ARROW_N,"ARROW_NE":Image.ARROW_NE,"ARROW_E":Image.ARROW_E,"ARROW_SE":Image.ARROW_SE,"ARROW_S":Image.ARROW_S,"ARROW_SW":Image.ARROW_SW,"ARROW_W":Image.ARROW_W,"ARROW_NW":Image.ARROW_NW}
    try:
     image_key=cmd_list[1]
    except IndexError:
     continue
    if image_key in image_dict:
     display.show(image_dict.get(image_key),wait=False)
   elif cmd_id=='s':
    display.scroll(str(cmd_list[1]),wait=False)
   elif cmd_id=='p':
    try:
     x=int(cmd_list[1])
    except ValueError:
     continue
    except IndexError:
     continue
    if x<0:
     x=0
    if x>4:
     x=4
    try:
     y=int(cmd_list[2])
    except ValueError:
     continue
    except IndexError:
     continue
    if y<0:
     y=0
    if y>4:
     y=4
    try:
     value=int(cmd_list[3])
    except ValueError:
     continue
    except IndexError:
     continue
    if value<0:
     value=0
    if value>9:
     value=9
    display.set_pixel(x,y,value)
   elif cmd_id=='c':
    display.clear()
   elif cmd_id=='a':
    try:
     pin=int(cmd_list[1])
     value=int(cmd_list[2])
    except IndexError:
     continue
    except ValueError:
     continue
    if 0<=pin<=2:
     if not 0<=value<=1023:
      value=256
     if pin==0:
      pin0.write_analog(value)
     elif pin==1:
      pin1.write_analog(value)
     elif pin==2:
      pin2.write_analog(value)
   elif cmd_id=='t':
    try:
     pin=int(cmd_list[1])
     value=int(cmd_list[2])
     digital_outputs[pin]=True
     print(str(digital_outputs))
    except IndexError:
     continue
    except ValueError:
     continue
    if 0<=pin<=2:
     if 0<=value<=1:
      if pin==0:
       pin0.write_digital(value)
      elif pin==1:
       pin1.write_digital(value)
      elif pin==2:
       pin2.write_digital(value)
     else:
      pass
   elif cmd=='g':
    sensor_string=""
    sensor_string+=str(accelerometer.get_x())+','
    sensor_string+=str(accelerometer.get_y())+','
    sensor_string+=str(accelerometer.get_z())+','
    sensor_string+=str(button_a.is_pressed())+','
    sensor_string+=str(button_b.is_pressed())+','
    if not digital_outputs[0]:
     sensor_string+=str(pin0.read_digital())+','
    else:
     sensor_string+='0'+','
    if not digital_outputs[1]:
     sensor_string+=str(pin1.read_digital())+','
    else:
     sensor_string+='0'+','
    if not digital_outputs[2]:
     sensor_string+=str(pin2.read_digital())+','
    else:
     sensor_string+='0'+','
    sensor_string+=str(pin0.read_analog())+','
    sensor_string+=str(pin1.read_analog())+','
    sensor_string+=str(pin2.read_analog())
    print(sensor_string)
   elif cmd=='v':
    print('s2mb.py Version 1.07 24 March 2018')
   else:
    continue
loop([False,False,False])
# Created by pyminifier (https://github.com/liftoff/pyminifier)

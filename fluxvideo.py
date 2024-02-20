
#To use this script the video must be an AVI file
#In order to convert a video from mp4 to AVI format you have use:
# ""  ./ffmpeg -i input.mp4 -vcodec mjpeg -vf "scale=1280:-1"  -q:v 2 -an video.avi ""
#The ffmpeg file is under <openmvide_installdir>/share/qtcreator/ffmpeg
## Source: https://forums.openmv.io/t/fun-with-avi-files/9105

import sensor, image, time
from AVIParse import *

filename = 'video.avi'
avi = AVIParse(filename)
ret = avi.parser_init()

print(avi)

clock = time.clock()                   # Create a clock object to track the FPS.

#stream = image.ImageIO("/to_analyse.avi", "w") #Temporal line to create a new video to analyze in RT1062

t = time.ticks_us()

#print("buffer: ", avi.buf)

while avi.avi_info['cur_img'] < avi.avi_info['total_frame']:
    clock.tick()

    frame_type = avi.get_frame()
    if frame_type == avi.AVI_VIDEO_FRAME:
        avi.avi_info['cur_img'] += 1
        #print("Numero frame actual: ", avi.avi_info['cur_img'])
        img = image.Image(avi.avi_info['width'], avi.avi_info['height'],
                          image.JPEG, buffer=avi.buf, copy_to_fb=True)
        #img.to_jpeg()


        #stream.write(img)
        while time.ticks_diff(time.ticks_us(), t) < avi.avi_info['sec_per_frame']:
            pass
        t = time.ticks_add(t, avi.avi_info['sec_per_frame'])
    print(clock.fps())

avi.avi_info['cur_img'] = 0

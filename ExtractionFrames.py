#To use this script the video must be an AVI file
#In order to convert a video from mp4 to AVI format you have use:
# ""  ./ffmpeg -i input.mp4 -vcodec mjpeg -vf "scale=1280:-1"  -q:v 2 -an video.avi ""
#The ffmpeg file is under <openmvide_installdir>/share/qtcreator/ffmpeg
## Source: https://forums.openmv.io/t/fun-with-avi-files/9105


import image, time, os
from AVIParse import *

filename = 'video2.avi'
avi = AVIParse(filename)
ret = avi.parser_init()

if not "frames_analyse" in os.listdir(): os.mkdir("frames_analyse")

clock = time.clock()                   # Create a clock object to track the FPS.

while avi.avi_info['cur_img'] < avi.avi_info['total_frame']:
    clock.tick()

    frame_type = avi.get_frame()
    if frame_type == avi.AVI_VIDEO_FRAME:
        avi.avi_info['cur_img'] += 1
        print("Numero frame actual: ", avi.avi_info['cur_img'])
        img = image.Image(avi.avi_info['width'], avi.avi_info['height'],
                          image.JPEG, buffer=avi.buf, copy_to_fb=True)

    stream = image.ImageIO("/frames_analyse/frame_{}.jpeg".format(avi.avi_info['cur_img']), "w")
        # Guardar el frame como una imagen JPEG
    stream.write(img)
    stream.close()
        #img.save(frame_filename)
    print(clock.fps())

avi.avi_info['cur_img'] = 0

files=os.listdir("/frames_analyse")
jpegs=[files for files in files if "jpeg" in files]
print(jpegs)
for jpeg in jpegs:
    print(jpeg)
    stream = image.ImageIO("/frames_analyse/"+jpeg, "r")
    img = stream.read(copy_to_fb=True, loop=True, pause=True)
    img.save("/frames_analyse/"+jpeg)



# Untitled - By: keyia - mer. févr. 14 2024

import sensor, image, time, os

if not "frames_bmp" in os.listdir(): os.mkdir("frames_bmp")

files=os.listdir("/frames_analyse")
bmps=[files for files in files if "bmp" in files]
print(bmps)
for bmp in bmps:
    img=image.Image("/frames_analyse/"+bmp,copy_to_fb=True)
    gray=img.to_grayscale()
    gray.save("/frames_bmp/"+bmp)
    print(bmp)

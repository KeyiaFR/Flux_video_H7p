# Untitled - By: keyia - mer. févr. 14 2024

import sensor, image, time, os

if not "frames_bmp" in os.listdir(): os.mkdir("frames_bmp")


dir_path = "/frames_analyse"

for file in os.ilistdir(dir_path):
    file_name = file[0]
    if file_name.endswith(".bmp"):
        img=image.Image("/frames_analyse/"+file_name,copy_to_fb=True)
        gray=img.to_grayscale()
        gray.save("/frames_bmp/"+file_name)
        print(file_name)

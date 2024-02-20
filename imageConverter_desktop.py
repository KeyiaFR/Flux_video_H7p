from PIL import Image
import glob, os



for file in glob.glob("frames_analyse/*.jpeg"):
    image = Image.open(file)
    image.save(file.replace("jpeg", "bmp"))
    print("image: ", file)

for file in glob.glob("frames_analyse/*.jpeg"):
    os.remove(file)
    
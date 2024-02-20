import os
rute = "/frames_bmp"  
files = os.listdir(rute)
files.sort()

counter = 1

for f in files:
    
    name, extension = os.path.splitext(f)
    
    if extension == ".bmp":
       
        new_name = "frame_" + str(counter) + ".bmp"
        
        og_directory = os.path.join(rute, f)
        new_directory = os.path.join(rute, new_name)
        
        os.rename(og_directory, new_directory)
        
        counter += 1

print("End")

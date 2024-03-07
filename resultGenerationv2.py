import sensor, image, time, mjpeg, os, gc, machine, math, re
from config import *

#****************************************************
#*********Configuration******************************
#****************************************************
conf = configurationClass('config.json')
if(conf.getConfig() == True):
    conf.getConfigFromConfigFile()
else:
    conf.getConfigByDefault()

#*********Debug****************************************
verbose = False 																	   # Verbose parameter used for debug

#********Log*******************************************
logDetectionFlag = True                                               # Flag used to log detections on csv file (Only available with SD card, if it is present)

#*******Global Variables**************
start = 0
startValidDetection = 0
cptValidDetection =0
detectionFlag = True

#*********Environment**********************************
cameraHeightInM = 7
if cameraHeightInM == 5:
    widthXImageInM = 20                                                                # Function of height of product, width of image (in m) = 1500
elif cameraHeightInM == 6:
    widthXImageInM = 25
elif cameraHeightInM == 7:
    widthXImageInM = 30
else:
    widthXImageInM = 25

def findBlobFunctionOfArea(blobCenterX, blobCenterY):                                   # Return Minimum detecion area corresponding to blob zone detection

    #declarations
    imageZone = 0
    area = (0,0)

    # Compute distance of center blob compared to center of image
    blobCenterX = blobCenterX-resolutionX/2
    blobCenterY = blobCenterY-resolutionY/2
    hypotenuse = math.sqrt(blobCenterX**2 + blobCenterY**2)
    imageZone =  hypotenuse // radiusAreaDivision

    #Set minimal area of detection
    if imageZone == 0:
        area = (area0ThresholdMin,area0ThresholdMax)
    elif imageZone == 1:
        area = (area1ThresholdMin,area1ThresholdMax)
    elif imageZone == 2:
        area = (area2ThresholdMin,area2ThresholdMax)
    elif imageZone == 3:
        area = (area3ThresholdMin,area3ThresholdMax)
    elif imageZone == 4:
        area = (area4ThresholdMin,area4ThresholdMax)
    else:
        area = (areaDefaultThresholdMin, areaDefaultThresholdMax)

    if(verbose == True):
        print("******* Image Zone " + str (imageZone))
        print("******* Area = " + str(area))

    return area

def setDacAccordingToObject(objectDetected):
    if (objectDetected == "Pieton"):
        dac.write(77) # 1V sur 3.3Ref et 8 bits de res (255)
    elif (objectDetected == "Velo"):
        dac.write(144) #2V
    elif (objectDetected == "Vehicle"):
        dac.write(144) #3V


def validationArea(blobCx, blobCy, excludedZones):                                      # Return if blob was in a valid area
    validation = False
    zone = (blobCx//40 + 1)*100 + ((blobCy+heightCropStep*conf.cropPosition)//40 + 1)
    if(zone not in excludedZones):
        validation = True

    return validation


def blobs_speed_track(imgBlobList):                                                                       # Define the list of blobs from current frame diffenrencing analysis
    speed_vects = []                                                                                      # Table containing vector and norm
    if len(imgBlobList) > 2:                                                                              # If at least 3 image have been detected
        imgBlobList_0 = imgBlobList[0]
        imgBlobList_1 = imgBlobList[1]
        imgBlobList_2 = imgBlobList[2]
        if  imgBlobList_0 and imgBlobList_1 and imgBlobList_2:                                            # If a blob exist in imgBlobList 0, 1 and 2
            for blob_2 in imgBlobList_2:
                for blob_1 in imgBlobList_1:
                    hypothenuse = math.sqrt((blob_2.cx()-blob_1.cx())**2 + (blob_2.cy()-blob_1.cy())**2); # Compute hypothenuse (distance) between two blobs
                    cFps = clock.fps()
                    if(hypothenuse < int(((maxSpeedKmh/3.6)/cFps)*(ratioImageInPxPerM))):                 # If hypothenuse (distance) is inferior to a given speed
                                                                                                          # For a vehicle at 50km/h, it travel at ~=14m/s speed, so 50kmh in px  = (speed/fps)* pxwdth / m width                                                                                                          # = (14/6)*640 / 25 ~= 59 px
                        if abs(blob_1.area()-blob_2.area()) < blob_1.area() * (percentBlobAreaDifference/100):  # Test if blobs have approximatively the same size.
                            NormVecteur =  (hypothenuse * (cFps))                                         # Vector norm (in px / seconds), clock.fps() = Frame Per Seconds -> A frame = 1 image comparison
                            x_end = blob_2.cx() + int((blob_2.cx() - blob_1.cx())*NormVecteur/60)         # 60 arbitrary value to be able to see arrow
                            if x_end < 0:
                                x_end = 0

                            y_end = blob_2.cy() + int((blob_2.cy() - blob_1.cy())*NormVecteur/60)
                            if y_end < 0:
                                y_end = 0

                            speedKmH = (NormVecteur*(1/ratioImageInPxPerM))*3.6;                          # (px/s * m/px) * 3.6

                            speed_vects.append([blob_2.cx(), blob_2.cy(), x_end , y_end, NormVecteur, speedKmH/2.5 , blob_2.area(), blob_2.density()])

                            if (verbose == True):
                                print("-----")
                                print("Speed Vect : xStart : "  + str(blob_2.cx())  + " yStart : "  + str(blob_2.cy()) + "|| xEnd : "  + str(x_end) + " yEnd: "  + str(y_end) + " Norm: " + str(NormVecteur))
                                print("Cfps = " + str(cFps) + " blob_1_cx = " + str(blob_1.cx()) + " blob_1_cx = " + str(blob_1.cy()))
                                print("Blob1 area " + str(blob_1.area()) + " Blob2 area " + str(blob_2.area()))
                                print("Speed km/h = " + str(speedKmH))
                                print("-----")
    return speed_vects

#****************************************************
#***************End Functions************************
#****************************************************



#*********Image transforming***************************
thresholds = (10,240) #5,251                                                                   # Pixels took into account for image diff from grayscale to binary
heightCropStep = 20

#*********Blob detection threshold*********************
blobDensity = 0.13                                                                     # From Doc : "Returns the density ratio of the blob. This is the number of pixels in the blob over its bounding box area."
blobElongationMax = 0.85                                                               # Elongation Max, permet d'éliminer toiles d'araignées ou pluie
blobElongationMin = 0.15                                                               # Elongation Min, permet d'éliminer toiles d'araignées ou pluie
blobAreaThreshold = 350                                                                # Minimum area in pixels considered for blob detections
blobAreaDetection = 350                                                                # Minimum area in pixels used for detection Note : Same size as blobAreaThreshold for speed computing
maxBlobSizeThreshold = 40000 														   # Maximum threshold size in px: 3072000 Max

#*********Exclusion zone*******************************
excludedZones = conf.excludedZones                                                     # Exclusion zone 40*40 pixels 16 zones on x, 12 on y (192 areas)

#*********Speed detection threshold********************
pedestrianMinSpeed = 1.2
pedestrianHighSpeed = 10
bicycleHighSpeed = 25
vehicleMinArea = 8000
percentBlobAreaDifference = 50
maxSpeedKmh = 30
minNbOfSpeedDetectionAtHighPower = 4                                                   #Minimum Nb of Speed Detection to allow detection (When light is at High Power)


#*********Zone and Blob detection threshold************
radiusAreaDivision = 80;                                                               # Radius Area division of image to determine which area is take into account for blob detection (see function findBlobFunctionOfArea)
area0ThresholdMin = 650																   # Minimum threashold in pixels used for detection in area0
area1ThresholdMin = 550																   # Minimum threshold in pixels used for detection in area1
area2ThresholdMin = 400																   # Minimum threshold in pixels used for detection in area2
area3ThresholdMin = 350																   # Minimum threshold in pixels used for detection in area3
area4ThresholdMin = 300																   # Minimum threshold in pixels used for detection in area4
areaDefaultThresholdMin = 300														   # Minimum threshold in pixels used for detection in areaDefault
area0ThresholdMax = 8000    														   # Maximum threashold in pixels used for detection in area0
area1ThresholdMax = 8000    														   # Maximum threshold in pixels used for detection in area1
area2ThresholdMax = 8000     														   # Maximum threshold in pixels used for detection in area2
area3ThresholdMax = 8000     														   # Maximum threshold in pixels used for detection in area3
area4ThresholdMax = 8000    														   # Maximum threshold in pixels used for detection in area4
areaDefaultThresholdMax = 8000   													   # Maximum threshold in pixels used for detection in areaDefault
resolutionX= 640 		                                                               # Same to frameSize (x)
resolutionY= 360                                                  	                   # Same to frameSize (y)
ratioImageInPxPerM = resolutionX/widthXImageInM






sensor.reset()
sensor.set_pixformat(sensor.GRAYSCALE)
sensor.set_framesize(sensor.VGA)
sensor.skip_frames(time=2000)

#****************************************************
#*************Global Declarations********************
#****************************************************
compteur = 0                                                                           		# Counter used to define active time of detection
validAreaBlobFound = False
imgBlobList = [[]]                                                                     		# List of image containing Blobs list used to calculate speed vector
blobValidList = []                                                                     		# List of image containing Blobs list used to calculate speed vector
blobValidListTmp =[]
clock = time.clock()                                                                   		# Set variable to clock
rtc = machine.RTC()
rtc.datetime((2000, 1, 1, 1, 0, 0, 0, 0))
cptFileName = 0;                                                                       		# Counter computed by getfileName method and used for videos filenames
sdCardPresentFlag = False
recordVideo = False
cptDetections = 0;                                                                     		# Counter used for videos filenames
cptRecord =0;
isAutoMode = True;
exposureComputed = 0
gainComputed = 0                                                                 		# Exposition memorized used in auto adjust Exposure function
objectDetected = "Null"																   		# Nature of object / No item Detected at start


m = mjpeg.Mjpeg("ResultToulouse1_1.mjpeg")  #Result file
print("Nombre del archivo: ResultToulouse1_1.mjpeg")



dir_path = "/frames_analyse/"
# Extra buffer
img_ref = sensor.alloc_extra_fb(640, 360, sensor.GRAYSCALE)

#files = os.listdir("/frames_bmp")

files_iter = os.ilistdir("/frames_analyse")

for file_info in files_iter:
    filename = file_info[0]
    print("----------/////// Iteration start ///////------------")
    if filename.endswith(".bmp"):
        print(f"Processing: {filename}")
        clock.tick()

        file_path = dir_path+filename
        patron = re.compile(r'\d+')
        numero = re.search(patron, filename).group(0)
        index=int(numero)
        print("first index : ",index)

        img_ref.replace(image.Image(file_path, copy_to_fb=True))

        if index > 1:
            try:
                second_path=dir_path+"frame_"+str(index - 1)+".bmp"
                img = image.Image(second_path, copy_to_fb=True)
                img_diff = img_ref.difference(img)
                img_diff_bin = img_diff.binary([(10, 240)])
                print("second index : ",str(index - 1))
                print("Getting blobs")

                blobs = img_diff_bin.find_blobs([(254,255)], merge=True, margin=20, area_threshold=blobAreaThreshold, pixels_threshold=50) # Apply Blob detection algorithm

                print("blobs gotten ")


                #*****Extract and fill list of Valid Blobs for caracterization***
                for blob in blobs:
                      if blob.area() > blobAreaDetection and blob.area() < maxBlobSizeThreshold and blob.density() > blobDensity  and blob.elongation() < blobElongationMax and blob.elongation() > blobElongationMin:
                        colorDrawBlob = 128                                             				# Colored in Grey if it does not validate detection criterias
                        areaDetection = findBlobFunctionOfArea(blob.cx(), blob.cy())    				# Get Area of detection depending of center blob position
                        if blob.area() > areaDetection[0] and blob.area() < areaDetection[1] : 			# If Blob is bigger than given Min area and smaller than givent Max area
                            isValidArea =  validationArea(blob.cx(), blob.cy(), excludedZones)  		# Check If blob is not in an excluded area
                            if isValidArea :                                            				# If blob is not in an excluded area Detection is Valid
                              img.draw_string(150, 0, "Area > " + str(areaDetection[0]) + " < " + str(areaDetection[1]))   # TODO : To be removed, for debug
                              colorDrawBlob = 255                                       				# Colored in White if it validate detection criterias
                              blobValidList.append(blob)                                				# Add blob to blobValidList
                              validAreaBlobFound = True                                					# Flag Used for filling imgBlobList in order to calculate speed
                        img.draw_rectangle(blob.rect(), color=colorDrawBlob)            				# Draw Blob founds
                        img.draw_cross(blob.cx(), blob.cy(), color=colorDrawBlob)
                        img.draw_string(blob.cx(),blob.cy() + 5, str(blob.area()))


                        if colorDrawBlob == 255:
                            colorDrawBlob = 200
                        img_diff_bin.draw_rectangle(blob.rect(), color=colorDrawBlob)            				# Draw Blob founds
                        img_diff_bin.draw_cross(blob.cx(), blob.cy(), color=colorDrawBlob)
                        img_diff_bin.draw_string(blob.cx(),blob.cy() + 5, str(blob.area()))

                if (validAreaBlobFound == True):                                        				# Fill blob validated list
                    startBlobSeen = time.ticks_ms();                                   				    # Time reset to clear imgBlobList after a given time
                    imgBlobList.append(blobValidList.copy())                            				# Add Valid Blobs to imgBlobList  Note : copy used to not clear imgBlobList when blobValidList is cleared
                    blobValidList.clear()
                    validAreaBlobFound = False

                #********Blob Caracterization and detection algorithm ***********
                if len(imgBlobList)>0:																    # If blobs are in valid blob list

                    speed_vects = blobs_speed_track(imgBlobList)										# Calculating and displaying blob speed vectors
                    for speed_vect in speed_vects:														# Go all over speed vectors
                        img.draw_arrow(speed_vect[0:4], color=0, thickness=6)							# Draw indicating speed arrow
                        img.draw_string(speed_vect[2]+20,speed_vect[3]+ 20, str(speed_vect[5]),color=0, scale =2)
                        if(speed_vect[5] > pedestrianMinSpeed and speed_vect[5] <= bicycleHighSpeed) :  # Characterize object detected depending of blobs speed
                            if(speed_vect[5] > pedestrianMinSpeed and speed_vect[5] <= pedestrianHighSpeed):
                                objectDetected = "Pieton"												# Pedestrian object
                            elif(speed_vect[5] > pedestrianHighSpeed and speed_vect[5] <= bicycleHighSpeed):
                                objectDetected = "Velo"                                                 # Bike object
                            img.draw_string(speed_vect[2]+20,speed_vect[3]- 20, objectDetected, color=0, scale =2) # Print type of detection on image
                            img_diff_bin.draw_string(speed_vect[2]+20,speed_vect[3]- 20, objectDetected, color=128, scale =2) # Prin

                            startValidDetection = time.ticks_ms()										# Start time of active detection
                            cptValidDetection +=1														# Increment counter of valid detections

                            img.draw_string(200,20, "Density = " + str(speed_vect[7]), color=0, scale =2) # Print type of detection on image
                            img_diff_bin.draw_string(200,20, "Density = " + str(speed_vect[7]), color=128, scale =2) # Print type of detection on image.draw_string(200,20, "Density = " + str(speed_vect[7]), color=0, scale =2) # Print type of detection on image
                            #*************Detection******************************************
                            if((detectionFlag == True and cptValidDetection > minNbOfSpeedDetectionAtHighPower) or detectionFlag == False): #Security used to ensure a continuous motion is present when light is power up.
                                if(detectionFlag == False):
                                    if (logDetectionFlag == True):
                                        writeTypeDetectionFull(objectDetected, speed_vect)                           	# Log First cause of detection
                                #powerUp()        # Give order to increase light

                        elif(speed_vect[5] > bicycleHighSpeed or speed_vect[6] > vehicleMinArea):
                            img.draw_string(speed_vect[2]+20,speed_vect[3]- 20, "Vehicle", color=0, scale =2) # Vehicle object
                        else:
                            img.draw_string(speed_vect[2]+20,speed_vect[3]- 20, "Null", color=0, scale =2)    # Null object

                    if len(imgBlobList) > 3:
                        print("len(imgBlobList) > 3")
                        imgBlobList.pop(0)                                                              # Remove first element in imgBlobList                                                                                                                         #

                    if len(imgBlobList)>0:
                        print("len(imgBlobList)>0")
                        imgBlobList_0 = imgBlobList[0]													# Replace imgBlobList_0 by old imgBlobList_1
                else :
                   imgBlobList.clear()


                #*************End of Detection***********************************
                if (detectionFlag == True):
                    img.draw_string(0, 0, "Detection")
                    img_diff_bin.draw_string(0, 0, "No detection")
                else :
                    img.draw_string(0, 0, "No detection")
                    img_diff_bin.draw_string(0, 0, "No detection")


                print("memoire free: ",gc.mem_free())

                #Add circles to image video
                img_diff_bin.draw_circle((295,310,104),color=255,thickness=2, fill=False) ## Change radius, in this case radius for 5m is 104
                img_diff_bin.draw_circle((295,310,417//2),color=255,thickness=2) #10 m
                img_diff_bin.draw_circle((295,310,652//2),color=255,thickness=2) #15 m

                # Add frame to video
                m.add_frame(img_diff_bin)
                print("frames in video: ", m.count())
                print("Size video: ", m.size())
                time.sleep_ms(200)
            except:
                print("FileNotFoundError")
                time.sleep_ms(200)
                continue
# Close video
m.close()
print("Closed file: ",m.is_closed())

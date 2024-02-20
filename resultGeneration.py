import sensor, image, time, mjpeg, os, gc

sensor.reset()
sensor.set_pixformat(sensor.GRAYSCALE)
sensor.set_framesize(sensor.VGA)
sensor.skip_frames(time=2000)

clock = time.clock()

m = mjpeg.Mjpeg("Result.mjpeg")  # Establecer el archivo de video
print("Nombre del archivo: Result.mjpeg")  # Imprimir información del archivo de video

files = os.listdir("/frames_bmp")
bmps = [file for file in files if "bmp" in file]
print(bmps)

# Crear un framebuffer extra para almacenar la referencia del frame
img_ref = sensor.alloc_extra_fb(640, 360, sensor.GRAYSCALE)

for i in range(1, len(bmps)):
    print(f"Calculando diferencia entre los frames {i-1} y {i}")
    clock.tick()  # Actualizar el FPS

    # Cargar los frames
    img_ref.replace(image.Image("/frames_bmp/" + bmps[i-1], copy_to_fb=True))

    img_buff = image.Image("/frames_bmp/" + bmps[i], copy_to_fb=True)

    # Calcular la diferencia entre los frames
    img_diff = img_ref.difference(img_buff)

    img_diff_bin = img_diff.binary([(10,240)])

    blobs = img_diff_bin.find_blobs([(254,255)], merge=True, margin=10, area_threshold=300, pixels_threshold=50) # Apply Blob detection algorithm

    print("blobs: ",blobs)
    # Agregar la diferencia al objeto m
    m.add_frame(img_diff_bin)

# Cerrar el video
m.close()
print("Archivo cerrado")

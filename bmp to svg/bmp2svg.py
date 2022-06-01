import os

input_file = "photo.bmp"
output_file = "photo.svg"

os.system("potrace {} --svg -o {}".format(input_file, output_file))
#!/usr/bin/env python3

from PIL import Image
from math import ceil
from fpdf import FPDF
from os import unlink, environ
import argparse

parser = argparse.ArgumentParser(description="Split map to print on multiple pages with overlap", epilog="The PAGE_SIZE parameter will override the PAGE_WIDTH and PAGE_HEIGHT parameters")

parser.add_argument('--file', dest="image_name", required=True, help="Input filename")
parser.add_argument('--file-width', dest="map_width", type=float, required=True, help="Width of input file (inches)")
parser.add_argument('--file-height', dest="map_height", type=float, required=True, help="Height of input file (inches)")
parser.add_argument('--page-size', dest='page_size', help="Page size (letter, legal, ledger)")
parser.add_argument('--page-width', dest='page_width', type=float, default=8.5, help="Width of output pages (inches)")
parser.add_argument('--page-height', dest='page_height', type=float, default=11, help="Height of outout pages (inches)")
parser.add_argument('--output', dest='output_name', default='output', help="Name of output file")
parser.add_argument('--temp-dir', dest='temp_dir', default=environ['TMP'], help='Location of temp files')

args=parser.parse_args()

image_name = args.image_name
output_name = args.output_name
map_width = args.map_width
map_height = args.map_height
page_width = args.page_width
page_height = args.page_height
if args.page_size:
  if args.page_size.lower() == 'letter':
    page_width = 8.5
    page_height = 11
  if args.page_size.lower() == 'legal':
    page_width = 8.5
    page_height = 14
  if args.page_size.lower() == 'ledger':
    page_width = 11
    page_height = 17
temp_dir = args.temp_dir

pixel_per_inch = 72

margin = 0.25
overlap = 0.5

hole_size = 0.25
hole_offset = overlap/2-hole_size/2

# 'split image' dimension is dimension = 2 x ( margin + overlap )
si_width = page_width - 2 * (margin + overlap)
si_height = page_height - 2 * (margin + overlap)

image_width = map_width * pixel_per_inch
image_height = map_height * pixel_per_inch

x_pages = int(ceil(map_width/(page_width - overlap)))
y_pages = int(ceil(map_height/(page_height - overlap)))

image = Image.open(image_name)

image = image.resize((int(image_width), int(image_height)), Image.ANTIALIAS)

# image.save("output.png")

pdf = FPDF('P','in', (page_width, page_height))

temp_files = []

for y in range(y_pages):
  for x in range(x_pages):
    outfile = "%s/_%s_%dx%d.png" % (temp_dir,output_name,x,y)
    temp_files.append(outfile)

    cut_width = page_width - 2*margin
    cut_height = page_height - 2*margin
    cut_right = min(image.size[0], (x*(si_width + overlap) + cut_width) * pixel_per_inch)
    cut_bottom = min(image.size[1], (y*(si_height + overlap) + cut_height) * pixel_per_inch)

    # save new image cut from image
    cut_image = image.crop((x*(cut_width-overlap)*pixel_per_inch,y*(cut_height-overlap)*pixel_per_inch,cut_right,cut_bottom))
    cut_image.save(outfile)
    # place image in PDF
    pdf.add_page()
    pdf.image(outfile,x=margin, y=margin, w=min(page_width-2*margin, cut_image.size[0]/pixel_per_inch), h=min(page_height-2*margin, cut_image.size[1]/pixel_per_inch))
    # place holes on PDF
    pdf.set_draw_color(r=0)
    pdf.set_fill_color(r=255)
    left_dot = margin+hole_offset
    right_dot = cut_image.size[0]/pixel_per_inch-hole_size+margin/2
    top_dot = margin+hole_offset
    bottom_dot = cut_image.size[1]/pixel_per_inch-hole_size+margin/2
    if x != 0 or y !=0:
      pdf.ellipse(x=left_dot, y=top_dot, w=hole_size, h=hole_size, style='DF')
    if x != 0 or y != y_pages-1:
      pdf.ellipse(x=left_dot, y=bottom_dot, w=hole_size, h=hole_size, style='DF')
    if x != x_pages-1 or y !=0:
      pdf.ellipse(x=right_dot, y=top_dot, w=hole_size, h=hole_size, style='DF')
    if x != x_pages-1 or y != y_pages-1:
      pdf.ellipse(x=right_dot, y=bottom_dot, w=hole_size, h=hole_size, style='DF')

# save PDf
pdf.output("%s.pdf"%output_name)

# remove temp files
while temp_files:
  try:
    unlink(temp_files.pop())
  except:
    pass

print("Map will require %d pins." % int((x_pages+1)*(y_pages+1)-4))

from PIL import Image, ImageDraw
import fitz

img = Image.new('RGB', (800, 400), 'white')
draw = ImageDraw.Draw(img)
draw.text((50, 50), 'The quick brown fox jumps over the lazy dog.', fill='black')
draw.text((50, 100), 'This is a test of our OCR pipeline.', fill='black')
draw.text((50, 150), 'Document translation with OCR support.', fill='black')
img.save('/tmp/test_scan.png')

doc = fitz.open()
page = doc.new_page(width=612, height=792)
page.insert_image(fitz.Rect(50, 200, 550, 500), filename='/tmp/test_scan.png')
doc.save('/tmp/test_scan.pdf')
doc.close()
print('Created test_scan.pdf')

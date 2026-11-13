"""Create an isolated labelled synthetic image for browser coordinate tests."""
from pathlib import Path
from PIL import Image, ImageDraw

root=Path('/tmp/corovision-reference-browser-synthetic')
root.mkdir(exist_ok=True)
image=Image.new('RGB',(512,512),'#e4e4e7')
draw=ImageDraw.Draw(image)
draw.text((20,20),'SYNTHETIC SOFTWARE FIXTURE - NOT PATIENT DATA',fill='black')
draw.rectangle((60,100,400,120),fill='#222222')
draw.rectangle((60,200,400,240),fill='#222222')
image.save(root/'synthetic-reference.png')
print(root/'synthetic-reference.png')

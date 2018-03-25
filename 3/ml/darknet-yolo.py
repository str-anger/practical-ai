# you will need make and gcс.
# if you need cuda, chage Makefile: GPU=1

# git clone https://github.com/pjreddie/darknet
# cd darknet
# make
# wget https://pjreddie.com/media/files/yolov3.weights
# ./darknet detect cfg/yolov3.cfg yolov3.weights data/dog.jpg

import sys, os

# put here path to darknet/python/ folder
sys.path.append(os.path.join(os.getcwd(), 'python/'))

from darknet import *

#NB use binary strings for compatibility with binaries
prefix = b"/home/stranger/pai/darknet/"
# to load network you need its structure (config) and neuron weights
net = load_net(prefix + b"cfg/yolo.cfg", prefix + b"yolo.weights", 0)

# meta provides info about dataset tags
# we need it to know how many tags are there in data/coco.names file
meta = load_meta(prefix + b"cfg/coco.data")

# here's the forward ANN run itself
bb = detect(net, meta, b"/mnt/c/dev/practical-ai/3/classic/cars.jpg")

# print bounding boxes
print(bb)
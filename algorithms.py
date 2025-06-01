import cv2 as cv
import numpy as np
from csbdeep.utils import  normalize
from stardist import random_label_cmap


lbl_cmap = random_label_cmap()

def cell_detection(img, thresh):
    #Following tutorial from https://docs.opencv.org/4.x/d3/db4/tutorial_py_watershed.html
    image = cv.imread(img)
    imgRGB = cv.cvtColor(image, cv.COLOR_BGR2RGB)

    #Image needs to be grayscale for cv.threshold()
    img = cv.cvtColor(image, cv.COLOR_BGR2GRAY)

    _, imgThreshold = cv.threshold(img, thresh, 255, cv.THRESH_BINARY_INV)
    
    cv.imwrite('tests/threshold.jpg', imgThreshold)
    kernel = cv.getStructuringElement(cv.MORPH_ELLIPSE, (9,9))

    #Open = Erosion followed by a dilation to remove noise
    imgOpen = cv.morphologyEx(imgThreshold, cv.MORPH_OPEN, kernel)
    cv.imwrite('tests/open.jpg', imgOpen)
    
    #Dilate to take account pixels around thresholded zones
    #Sure background area
    imgDilate = cv.morphologyEx(imgOpen, cv.MORPH_DILATE, kernel, iterations=3)
    cv.imwrite('tests/surebg.jpg', imgDilate)

    #DistanceTransform is a function that calculates the Euclidean distance between each non-zero pixel in an image and the nearest zero pixel
    #Sure foreground area
    distTrans = cv.distanceTransform(imgOpen, cv.DIST_L2, 5)
    _,distThresh = cv.threshold(distTrans, 1, 255, cv.THRESH_BINARY)
    cv.imwrite('tests/surefg.jpg', distThresh)

    #Unknown region
    sure_fg = np.uint8(distThresh)
    unknown = cv.subtract(imgDilate,sure_fg)

    distThresh = np.uint8(distThresh)
    nbLabels, labels = cv.connectedComponents(distThresh)
    labels = labels +1
    labels[unknown==255] = 0
    
    labels = np.int32(labels)
    labels = cv.watershed(imgRGB, labels)
    
    labels[labels == -1] = 0

    background_label = np.min(labels[labels > 0])  
    labels[labels == background_label] = 0

    # Create mask
    # Overlay onto original image
    color_map = np.random.randint(0, 255, size=(np.max(labels), 3), dtype=int)
    color_mask = np.ones_like(image)*255

    for label in range(2, np.max(labels)+1):
        mask = (labels == label)
        color_mask[mask] = color_map[label-1]

    transparency = 0.4
    mask = cv.addWeighted(image, 1 - transparency, color_mask, transparency, 0)
    cv.imwrite('static/mask_output.jpg', mask)
    return labels

    
def stardist(img_path, model):
    X = [img_path] 
    X = list(map(cv.imread,X))
    cv.imwrite('static/mask_output.jpg', X[0])

    n_channel = 1 if X[0].ndim == 2 else X[0].shape[-1]
    axis_norm = (0,1)   # normalize channels independently

    if n_channel > 1:
        print("Normalizing image channels %s." % ('jointly' if axis_norm is None or 2 in axis_norm else 'independently'))
    
    img = normalize(X[0], 1, 99.8, axis=axis_norm)

    labels, details = model.predict_instances_big(img, axes='YXC', block_size = 512, min_overlap = 128, context = 96)

    color_map = np.random.randint(0, 255, size=(np.max(labels), 3), dtype=int)
    color_mask = np.ones_like(X[0])*255

    for label in range(2, np.max(labels)+1):
        mask = (labels == label)
        color_mask[mask] = color_map[label-1]

    transparency = 0.4
    mask = cv.addWeighted(X[0], 1 - transparency, color_mask, transparency, 0)
    cv.imwrite('static/mask_output.jpg', mask)

    return labels


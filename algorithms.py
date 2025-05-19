import cv2 as cv
import numpy as np
#from matplotlib import pyplot as plt
#from scipy import ndimage
#from skimage import measure, color, io
#from stardist.models import StarDist2D
#from stardist.plot import render_label
#from csbdeep.utils import normalize
#import matplotlib.pyplot as plt
#from tifffile import imread
#from csbdeep.utils import Path, normalize

#from stardist import random_label_cmap, _draw_polygons, export_imagej_rois

#lbl_cmap = random_label_cmap()


def cell_detection(img, thresh ):
    #img = cv.imread("TestImage2.jpg")
    #img = cv.imread("TestImage.jpeg")
    image = cv.imread(img)
    imgRGB = cv.cvtColor(image, cv.COLOR_BGR2RGB)
    #image needs to be grayscale for cv.threshold()
    img = cv.cvtColor(image, cv.COLOR_BGR2GRAY)

    #plt.figure()
    #plt.subplot(231)
    #plt.imshow(img, cmap = 'gray')
    
    #TODO determine threshold values from image data
    #plt.subplot(232)
    _, imgThreshold = cv.threshold(img, thresh, 255, cv.THRESH_BINARY_INV)
    #plt.imshow(imgThreshold, cmap='gray')

    #plt.subplot(233)
    #TODO Change structuring element to ellipse, How to determine the radius??
    #kernel = np.ones((3,3), np.uint8)
    kernel = cv.getStructuringElement(cv.MORPH_ELLIPSE, (9,9))
    #Open = Erosion followed by a dilation to remove noise
    imgOpen = cv.morphologyEx(imgThreshold, cv.MORPH_OPEN, kernel)
    #Dilate to take account pixels around thresholded zones
    #Sure background area
    imgDilate = cv.morphologyEx(imgOpen, cv.MORPH_DILATE, kernel)
    #plt.imshow(imgDilate)

    #plt.subplot(234)
    #DistanceTransform is a function that calculates the Euclidean distance between each non-zero pixel in an image and the nearest zero pixel
    #Sure foreground area
    distTrans = cv.distanceTransform(imgOpen, cv.DIST_L2, 5)
    #plt.imshow(distTrans)

    #plt.subplot(235)
    _,distThresh = cv.threshold(distTrans, 1, 255, cv.THRESH_BINARY)
    #plt.imshow(distThresh)

    #Unknown region
    sure_fg = np.uint8(distThresh)
    unknown = cv.subtract(imgDilate,sure_fg)

    #plt.subplot(236)
    distThresh = np.uint8(distThresh)
    nbLabels, labels = cv.connectedComponents(distThresh)
    labels = labels +1
    labels[unknown==255] = 0
    #plt.imshow(labels)

    #plt.figure()
    #plt.subplot(121)
    labels = np.int32(labels)
    labels = cv.watershed(imgRGB, labels)

    # Create mask
    #mask = np.where(labels > 0, 255, 0).astype(np.uint8)

    # Overlay onto original image
    #segmented_image = cv.bitwise_and(image, image, mask=mask)
    #image[labels==-1] = [255,0, 0]
    #cv.imwrite('static/mask_output.jpg', image)
    cv.imwrite('static/labels.jpg', labels)
    #plt.imshow(labels)
    color_map = np.random.randint(0, 255, size=(np.max(labels), 3), dtype=int)
    color_mask = np.ones_like(image)*255

    for label in range(2, np.max(labels)+1):
        mask = (labels == label)
        color_mask[mask] = color_map[label-1]
    #plt.subplot(122)
    #imgRGB[labels==-1] = [255,0, 0]
    #plt.imshow(imgRGB)

    transparency = 0.4
    mask = cv.addWeighted(image, 1 - transparency, color_mask, transparency, 0)
    cv.imwrite('static/mask_output.jpg', mask)
    #success, buffered_img = cv.imencode('.jpg', mask)
    #if not success:
    #    return "Error encoding image", 500
    #cv.imshow('color image',imgRGB)
    

    #plt.show()
    #cv.imwrite('TCGA-2Z-A9J9-01A-01-TS1_Watershed_pred.jpg', imgRGB)
    #return nbLabels"""
    return True


def tissue_detection(img):
    #img = cv.imread("ROI_test.jpeg")
    img = cv.imread("ROI_test2.jpeg")
    imgRGB = cv.cvtColor(img, cv.COLOR_BGR2RGB)
    #image needs to be grayscale for cv.threshold()
    img = cv.cvtColor(img, cv.COLOR_BGR2GRAY)

    #plt.figure()
    #plt.subplot(231)
    #plt.imshow(img, cmap = 'gray')

    #plt.subplot(232)
    kernel = np.ones((3,3), np.uint8)
    #Open = Erosion followed by a dilation to remove noise
    imgOpen = cv.morphologyEx(img, cv.MORPH_OPEN, kernel)
    #plt.imshow(imgOpen)

    #plt.subplot(233)
    _, imgThreshold = cv.threshold(imgOpen, 210, 255, cv.THRESH_BINARY_INV)
    #plt.imshow(imgThreshold, cmap='gray')

    #plt.subplot(234)
    imgThreshold = np.uint8(imgThreshold)
    _, labels = cv.connectedComponents(imgThreshold)
    contours, _ = cv.findContours(imgThreshold, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
    #plt.imshow(labels)
    
    #plt.subplot(235)
    #cv.drawContours(imgRGB, contours, -1, (255,0,0), 1)
    #plt.imshow(imgRGB)

    #cv.imshow('color image',imgRGB)
    #plt.show()

def cell_cnt(img):
    nbLabels = cell_detection(img)
    print(nbLabels-1) #all components minus the background
    return nbLabels-1

    

def starDist(img):
    # prints a list of available models
    

    # creates a pretrained model
    #X = ["TCGA-2Z-A9J9-01A-01-TS1.tif"] 
   
    # Cell count = number of items - background
    #print(len(unique_labels)-1)

    #plt.figure(figsize=(8,8))
    #plt.imshow(img if img.ndim==2 else img[...,0], clim=(0,1), cmap='gray')
    #plt.imshow(labels, cmap=lbl_cmap, alpha=0.5)
    #plt.axis('off')
    #plt.show()
    #cv.imwrite('TCGA-2Z-A9J9-01A-01-TS1_StarDist_pred.jpg', labels)
    return True


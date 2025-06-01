import cv2 as cv
import numpy as np
import algorithms
from stardist.models import StarDist2D
import pandas as pd
from stardist.matching import matching
# creates a pretrained model
stardist_model = StarDist2D.from_pretrained('2D_versatile_he')



def make_ground_truth(path_gt):
    img = cv.imread(path_gt)
    gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)

    _,distThresh = cv.threshold(gray, 1, 255, cv.THRESH_BINARY)
    distThresh = np.uint8(distThresh)
    
    nbLabels, labels = cv.connectedComponents(distThresh)

    labels = np.int32(labels)
    labels = cv.watershed(img, labels)
    
    labels[labels == -1] = 0

    background_label = np.min(labels[labels > 0])  
    labels[labels == background_label] = 0
    
    # Create mask
    # Overlay onto original image
    color_map = np.random.randint(0, 255, size=(np.max(labels), 3), dtype=int)
    color_mask = np.ones_like(img)*255

    for label in range(1, np.max(labels)+1):
        mask = (labels == label)
        color_mask[mask] = color_map[label-1]
    mask = (labels == 0)
    color_mask[mask] = [0,0,0]

    transparency = 0.6
    mask = cv.addWeighted(img, 1 - transparency, color_mask, transparency, 0)
    #cv.imwrite(path, mask)
    return labels

def compute_accuracy():
    slides_nb_images = [(1,7),(2,3),(3,5),(4,8),(5,4),(6,3),(7,3),(8,4),(9,6),(10,4),(11,3)]
    watershed_df = pd.DataFrame(columns=['Slide','Image','Threshold','Accuracy','Precision', 'Recall', 'F1 Score', 'TP', 'FP', 'FN', 'Number of Cells Ground Truth', 'Number of Predicted Cells'])
    stardist_df = pd.DataFrame(columns=['Slide','Image','Accuracy','Precision', 'Recall', 'F1 Score', 'TP', 'FP', 'FN', 'Number of Cells Ground Truth', 'Number of Predicted Cells'])
    
    thresholds = [140, 150, 160, 170, 180, 190]
    for (slide, nb_images) in slides_nb_images:
        if(slide<10):
            path = "../TNBC_dataset/Slide_0"+str(slide)+"/0"+str(slide)+"_"
            path_gt = "../TNBC_dataset/GT_0"+str(slide)+"/0"+str(slide)+"_"
        else:
            path = "../TNBC_dataset/Slide_"+str(slide)+"/"+str(slide)+"_"
            path_gt = "../TNBC_dataset/GT_"+str(slide)+"/"+str(slide)+"_"
        
        for i in range(1, nb_images+1):
            image_path = path+str(i)+".png"
            image_binary = path_gt+str(i)+".png"

            ground_truth = make_ground_truth(image_binary)
            
            stardist_pred = algorithms.stardist(image_path, stardist_model)
            stardist_metrics =  matching(ground_truth, stardist_pred)
            stardist_df.loc[len(stardist_df)] = [slide,i,round(stardist_metrics.accuracy, 2) , round(stardist_metrics.precision, 2), round(stardist_metrics.recall,2), round(stardist_metrics.f1,2), stardist_metrics.tp, stardist_metrics.fp, stardist_metrics.fn, stardist_metrics.n_true, stardist_metrics.n_pred]
            
           
            for j in range(len(thresholds)):
                watershed_pred = algorithms.cell_detection(image_path, thresholds[j])
                watershed_metrics = matching(ground_truth, watershed_pred)
                watershed_df.loc[len(watershed_df)] = [slide, i, thresholds[j],round(watershed_metrics.accuracy,2), round(watershed_metrics.precision,2), round(watershed_metrics.recall,2), round(watershed_metrics.f1,2), watershed_metrics.tp, watershed_metrics.fp, watershed_metrics.fn, watershed_metrics.n_true, watershed_metrics.n_pred]
        
       
        stardist_df.to_csv('tests/accuracy_results_by_image_stardist.csv')
        
        watershed_df_140 = watershed_df[watershed_df['Threshold'] == 140]
        watershed_df_140.to_csv('tests/accuracy_results_by_image_watershed_140.csv')
        
        watershed_df_150 = watershed_df[watershed_df['Threshold'] == 150]
        watershed_df_150.to_csv('tests/accuracy_results_by_image_watershed_150.csv')
        
        watershed_df_160 = watershed_df[watershed_df['Threshold'] == 160]
        watershed_df_160.to_csv('tests/accuracy_results_by_image_watershed_160.csv')
        
        watershed_df_170 = watershed_df[watershed_df['Threshold'] == 170]
        watershed_df_170.to_csv('tests/accuracy_results_by_image_watershed_170.csv')
        
        watershed_df_180 = watershed_df[watershed_df['Threshold'] == 180]
        watershed_df_180.to_csv('tests/accuracy_results_by_image_watershed_180.csv')
        
        watershed_df_190 = watershed_df[watershed_df['Threshold'] == 190]
        watershed_df_190.to_csv('tests/accuracy_results_by_image_watershed_190.csv')
 
    return

if __name__ == '__main__':
    compute_accuracy()
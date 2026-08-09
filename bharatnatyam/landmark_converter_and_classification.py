import numpy as np
import mediapipe as mp
import pickle
from ultralytics import YOLO
hand2model=YOLO(r"1hand.pt")
hand1model=YOLO(r"2hand.pt")
handmodel=YOLO(r"hand.pt")
with open(r"double_hand.pkl","rb") as file:
    double_hand=pickle.load(file)
with open(r"single_hand.pkl","rb") as file:
    single_hand=pickle.load(file)
new_double={}
for k,v in double_hand.items():
    if len(v)!=63:
        new_double[k]=v
double_hand=new_double
def landmark_convert_to_list(landmark):
    return [(lm.x,lm.y,lm.z) for lm in landmark]
def euclidien_distance(c1,c2):
    return ((c1[0]-c2[0])**2 + (c1[1]-c2[1])**2 + (c1[2]-c2[2])**2)**0.5

def landmark_centroids(landmarks):
    landmark=landmarks
    hand_size = euclidien_distance(landmark[5], landmark[17]) # palm width
    # centroid using only base of all five fingers [0, 5, 9, 13, 17]
    finger_base=[0, 5, 9, 13, 17]
    finger_base_centroid=[0,0,0]
    for i in range(3):#for (x,y,z) co-ordinate of points
        centroid=float()
        for base in finger_base:
            centroid+=landmark[base][i]
        finger_base_centroid[i]=centroid/5
    return finger_base_centroid,hand_size

def normalized_distance(left,right):
    c1,s1=landmark_centroids(left)
    c2,s2=landmark_centroids(right)
    eucd=euclidien_distance(c1,c2)
    avg_hand_size=(s1+s2)/2

    return eucd/avg_hand_size if avg_hand_size!=0 else eucd

def is_hand_combined(left, right):
    if left is None or right is None:
        return False

    threshold = 3
    return normalized_distance(left, right) <= threshold , normalized_distance(left,right)


def flatten_mudra(landmark):
    if len(landmark) == 21:
        landmark = [landmark]

    li = []
    for hand in landmark:
        for x, y, z in hand:
            li.extend([x, y, z])
    return li


def cosine_similarity(vec1, vec2):
    n1 = np.linalg.norm(vec1)
    n2 = np.linalg.norm(vec2)
    if n1 == 0 or n2 == 0:
        return 0.0
    return np.dot(vec1, vec2) / (n1 * n2)



def classify_mudra_using_cosine_similarity(landmark):
    label, score = "", 0.0

    landmark = flatten_mudra(landmark)

    if len(landmark) == 63:  # 21 × 3 → single hand
        database = single_hand
    elif len(landmark) == 126:  # 2 × 21 × 3 → double hand
        database = double_hand
    else:
        return "", 0.0

    for mudra, vector in database.items():
        curr_score = cosine_similarity(landmark, vector)
        if curr_score > score:
            score = curr_score
            label = mudra

    return label, score

def classify_mudra_using_image(img):
    res=handmodel.predict(img)
    return (res[0].names[res[0].probs.top1],res[0].probs.top1conf.item())
    # if typ==1:#1hand mudra
    #     res=handmodel.predict(img)
    #     return (res[0].names[res[0].probs.top1],res[0].probs.top1conf.item())
    # else:
    #     res=hand2model.predict(img)
    #     return (res[0].names[res[0].probs.top1],res[0].probs.top1conf.item())



        
        



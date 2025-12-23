
import mediapipe as mp

def landmark_convert_to_list(landmark):
    return [(lm.x,lm.y,lm.z) for lm in landmark]
def euclidien_distance(c1,c2):
    return ((c1[0]-c2[0])**2 + (c1[1]-c2[1])**2 + (c1[2]-c2[2])**2)**0.5

def landmark_centroids(landmarks):
    landmark=landmarks
    hand_size=euclidien_distance(landmark[0],landmark[9]) # wrist+middle miger top
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

def is_hand_combined(left,right):
    if not left:left=[(0,0,0) for i in range(21)]
    if not right:right=[(0,0,0) for i in range(21)]
    threshold=2
    if normalized_distance(left,right)>threshold:return False
    return True


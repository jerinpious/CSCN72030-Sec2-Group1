#Group-1,Jerin,Inshal,Evan,Nour - Winter23 - Face Recognition Security camera 



#importing  the necessary libraries
import cv2
import winsound



webcam=cv2.VideoCapture(0)

#A while so that the program continues to record until said so
while True:
    #saving the captured content to variables
    _,img1=webcam.read()
    _,img2=webcam.read()
    #checking the diffrences in the images
    diff=cv2.absdiff(img1,img2)
    #changing the feed to gray and tracking the threshhold and contour 
    gray= cv2.cvtColor(diff,cv2.COLOR_BGR2GRAY)
    _,thresh=cv2.threshold(gray,20,255,cv2.THRESH_BINARY)
    contours,_=cv2.findContours(thresh,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
    for c in contours:
        #if contourArea less than 5000 program should continue as the motion can be by a bug or wind which should be discarded
        if cv2.contourArea(c)<5000:
            continue
        #else the program will print motion detected and will save the image to the program file
        print("Motion detected")
        i="0"
        cv2.imwrite('motion.png',img1)
        winsound.Beep(500,100)
    #live output
    cv2.imshow("Security Camera",thresh)
    #waitkey set to escape key to exit the program
    if cv2.waitKey(10)==27:
        break
webcam.release()
cv2.destroyAllWindows()
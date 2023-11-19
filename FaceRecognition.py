import cv2
import face_recognition
import winsound
from datetime import datetime
import os
import time

# Load images and their corresponding names from the "known_faces" folder
known_faces_folder = 'C:/Users/salty/Desktop/known_faces'
known_face_names = []
known_face_encodings = []

for file_name in os.listdir(known_faces_folder):
    if file_name.endswith(".jpg") or file_name.endswith(".png"):
        file_path = os.path.join(known_faces_folder, file_name)
        known_image = face_recognition.load_image_file(file_path)
        known_encoding = face_recognition.face_encodings(known_image)[0]
        known_face_names.append(os.path.splitext(file_name)[0])
        known_face_encodings.append(known_encoding)

# Load images and their corresponding names from the "unwanted_people" folder
unwanted_folder = 'C:/Users/salty/Desktop/unwanted_people'
unwanted_face_names = []
unwanted_face_encodings = []

for file_name in os.listdir(unwanted_folder):
    if file_name.endswith(".jpg") or file_name.endswith(".png"):
        file_path = os.path.join(unwanted_folder, file_name)
        unwanted_image = face_recognition.load_image_file(file_path)
        
        # Check if any face is found in the image
        unwanted_face_encoding = face_recognition.face_encodings(unwanted_image)
        if unwanted_face_encoding:
            unwanted_face_encodings.append(unwanted_face_encoding[0])
            unwanted_face_names.append(os.path.splitext(file_name)[0])

# Initialize variables for motion tracking and person names
motion_paths = {}  # Dictionary to store the motion paths of faces

webcam = cv2.VideoCapture(0)

# Set webcam resolution and desired frame rate
webcam.set(3, 640)  # Width
webcam.set(4, 480)  # Height
desired_fps = 15  # Set the desired frame rate

# Set the frame rate for the webcam
webcam.set(cv2.CAP_PROP_FPS, desired_fps)
webcam_fps = webcam.get(cv2.CAP_PROP_FPS)
print(f"Webcam Frame Rate: {webcam_fps}")

# Initialize frame counter
frame_counter = 0

recording = False
start_time = None
record_duration = 3 * 60 * 60  # 3 hours in seconds

faces_output_folder = 'C:/Users/salty/Desktop/faces'
os.makedirs(faces_output_folder, exist_ok=True)

records_output_folder = 'C:/Users/salty/Desktop/records'
os.makedirs(records_output_folder, exist_ok=True)

video_writer = None

def save_screenshot(face_img, name, timestamp, face_index):
    filename = f'{faces_output_folder}/{name}_{timestamp}_face_{face_index}.png'
    cv2.imwrite(filename, face_img)

while True:
    _, img1 = webcam.read()

    # If recording is turned on, skip frames to improve performance
    if recording and frame_counter % 5 != 0:
        frame_counter += 1
        time.sleep(0.02)  # Adjust the delay to reduce lag
        continue

    if recording and time.time() - start_time >= record_duration:
        recording = False
        if video_writer:
            video_writer.release()
            video_writer = None  # Reset video_writer after releasing

    # Find faces in the current frame
    face_locations = face_recognition.face_locations(img1)
    face_encodings = face_recognition.face_encodings(img1, face_locations)

    for i, (top, right, bottom, left) in enumerate(face_locations):
        # Check if the current face matches any unwanted faces
        intruder_name = None
        for j, unwanted_encoding in enumerate(unwanted_face_encodings):
            if face_recognition.compare_faces([unwanted_encoding], face_encodings[i], tolerance=0.5)[0]:
                intruder_name = unwanted_face_names[j]
                break

        # Draw a rectangle around the detected face
        if intruder_name:
            rectangle_color = (0, 0, 255)  # Red for unwanted faces
            winsound.Beep(1000, 100)

            # Mark unwanted person as "INTRUDER"
            cv2.putText(img1, f"INTRUDER: {intruder_name}", (left, top - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
            
            # Save the screenshot of the intruder to the "intruders" folder
            intruder_filename = f'C:/Users/salty/Desktop/intruders/{intruder_name}_{datetime.now().strftime("%Y%m%d%H%M%S")}_intruder_{i + 1}.png'
            cv2.imwrite(intruder_filename, img1[top:bottom, left:right])
        else:
            rectangle_color = (0, 255, 0)  # Green for known faces

            # Use a unique identifier for each face
            face_id = hash((top, right, bottom, left))

            # Update or initialize the motion path for the current face
            if face_id not in motion_paths:
                motion_paths[face_id] = []
            motion_paths[face_id].append(((left + right) // 2, (top + bottom) // 2))  # Record the center of the face

            # Draw a dot to track the motion of the face
            if len(motion_paths[face_id]) > 0:
                last_point = motion_paths[face_id][-1]
                cv2.circle(img1, last_point, 5, (0, 255, 0), -1)

            # Check if the current face matches any known faces
            matches = face_recognition.compare_faces(known_face_encodings, face_encodings[i], tolerance=0.5)

            name = "Unknown"
            if True in matches:
                first_match_index = matches.index(True)
                name = known_face_names[first_match_index]

                # Save the cropped face as a screenshot
                save_screenshot(img1[top:bottom, left:right], name, datetime.now().strftime("%Y%m%d%H%M%S"), i + 1)

            # Display the person's name on the image
            cv2.putText(img1, name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

            # Crop the region of interest (ROI) from the original image
            face_roi = img1[top:bottom, left:right]

            # Generate a unique filename with person's name, date, and time
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            filename = f'C:/Users/salty/Desktop/faces/{name}_{timestamp}_face_{i + 1}.png'

            # Save the cropped face as a screenshot
            cv2.imwrite(filename, face_roi)

            winsound.Beep(500, 100)

    # Display the "Recording in Progress" message
    if recording:
        cv2.putText(img1, "Recording in Progress", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)

        # Write the frame to the video file
        if video_writer:
            video_writer.write(img1)

    # Display the original color image with rectangles and motion paths
    cv2.imshow("Security Camera", img1)

    frame_counter += 1

    key = cv2.waitKey(10)
    if key == 27:
        if recording:
            recording = False
            if video_writer:
                video_writer.release()
        break
    elif key == ord('r'):  # Press 'r' to start recording
        recording = True
        start_time = time.time()

        # Define the codec and create a VideoWriter object
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        video_filename = f'{records_output_folder}/record_{timestamp}.avi'
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        video_writer = cv2.VideoWriter(video_filename, fourcc, desired_fps, (640, 480))

webcam.release()
cv2.destroyAllWindows()

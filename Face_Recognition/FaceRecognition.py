import cv2
import winsound
from datetime import datetime
import os
import time

# Function to create required folders
def create_folders():
    script_directory = os.path.dirname(os.path.abspath(__file__))
    face_properties_folder = os.path.join(script_directory, 'Face Properties')

    folders = ["faces", "unwanted_people", "recordings", "intruders", "known_faces"]
    for folder in folders:
        folder_path = os.path.join(face_properties_folder, folder)
        os.makedirs(folder_path, exist_ok=True)

# Create required folders if they don't exist
create_folders()

# Load images and their corresponding names from the "known_faces" folder
known_faces_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Face Properties', 'known_faces')
known_face_names = []
known_face_images = []

for file_name in os.listdir(known_faces_folder):
    if file_name.endswith(".jpg") or file_name.endswith(".png"):
        file_path = os.path.join(known_faces_folder, file_name)
        known_image = cv2.imread(file_path)
        known_face_names.append(os.path.splitext(file_name)[0])
        known_face_images.append(known_image)

# Load images and their corresponding names from the "unwanted_people" folder
unwanted_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Face Properties', 'unwanted_people')
unwanted_face_names = []
unwanted_face_images = []

for file_name in os.listdir(unwanted_folder):
    if file_name.endswith(".jpg") or file_name.endswith(".png"):
        file_path = os.path.join(unwanted_folder, file_name)
        unwanted_image = cv2.imread(file_path)
        unwanted_face_images.append(unwanted_image)
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

faces_output_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Face Properties', 'faces')
os.makedirs(faces_output_folder, exist_ok=True)

records_output_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Face Properties', 'records')
os.makedirs(records_output_folder, exist_ok=True)

video_writer = None

def save_screenshot(face_img, name, timestamp, face_index):
    filename = os.path.join(faces_output_folder, f'{name}_{timestamp}_face_{face_index}.png')
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

    # Convert the image to grayscale for face detection
    gray = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)

    # Use a face detection cascade classifier
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5, minSize=(30, 30))

    for i, (x, y, w, h) in enumerate(faces):
        # Draw a rectangle around the detected face
        face_roi = img1[y:y+h, x:x+w]

        # Check if the current face matches any unwanted faces
        intruder_name = None
        for j, unwanted_image in enumerate(unwanted_face_images):
            # Resize unwanted image to match the detected face size
            unwanted_resized = cv2.resize(unwanted_image, (w, h))

            # Compare the faces using structural similarity index (SSI)
            result = cv2.matchTemplate(face_roi, unwanted_resized, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, _ = cv2.minMaxLoc(result)

            if max_val > 0.7:  # Adjust this threshold as needed
                intruder_name = unwanted_face_names[j]
                break

        # Draw a rectangle around the detected face
        if intruder_name:
            rectangle_color = (0, 0, 255)  # Red for unwanted faces
            winsound.Beep(1000, 100)

            # Mark unwanted person as "INTRUDER"
            cv2.putText(img1, f"INTRUDER: {intruder_name}", (x, y - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

            # Save the screenshot of the intruder to the "intruders" folder
            intruder_filename = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Face Properties', 'intruders', f'{intruder_name}_{datetime.now().strftime("%Y%m%d%H%M%S")}_intruder_{i + 1}.png')
            cv2.imwrite(intruder_filename, face_roi)
        else:
            rectangle_color = (0, 255, 0)  # Green for known faces

            # Initialize 'name' before using it
            name = "Unknown"

            # Use a unique identifier for each face
            face_id = hash((x, y, w, h))

            # Update or initialize the motion path for the current face
            if face_id not in motion_paths:
                motion_paths[face_id] = []
            motion_paths[face_id].append(((x + w) // 2, (y + h) // 2))  # Record the center of the face

            # Draw a dot to track the motion of the face
            if len(motion_paths[face_id]) > 0:
                last_point = motion_paths[face_id][-1]
                #cv2.circle(img1, last_point, 5, (0, 255, 0), -1)

            # Check if the current face matches any known faces
            matches = []

            for known_face_image in known_face_images:
                # Resize known face image to match the detected face size
                known_resized = cv2.resize(known_face_image, (w, h))

                # Compare the faces using structural similarity index (SSI)
                result = cv2.matchTemplate(face_roi, known_resized, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, _ = cv2.minMaxLoc(result)
                matches.append(max_val)

            if any(match > 0.7 for match in matches):  # Adjust this threshold as needed
                first_match_index = matches.index(max(matches))
                name = known_face_names[first_match_index]

                # Save the cropped face as a screenshot
                save_screenshot(face_roi, name, datetime.now().strftime("%Y%m%d%H%M%S"), i + 1)

            # Display the person's name on the image
            cv2.putText(img1, name, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

            # Generate a unique filename with person's name, date, and time
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            filename = os.path.join(faces_output_folder, f'{name}_{timestamp}_face_{i + 1}.png')

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
        if key == ord('s'):
            recording = False
            if video_writer:
                video_writer.release()
        
        # Define the codec and create a VideoWriter object
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        video_filename = os.path.join(records_output_folder, f'record_{timestamp}.avi')
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        video_writer = cv2.VideoWriter(video_filename, fourcc, desired_fps, (640, 480))

webcam.release()
cv2.destroyAllWindows()

import socket 

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(("raspberrypi", 5000))

# File to store received sensor data
file_path = "received_sensor_data.txt"

while True:
    # Receive data from the server
    data = s.recv(1024)

    if not data:
        break

    # Decode the received data (assuming it's in JSON format)
    sensor_data = (data.decode('utf-8'))

    # Process or display the received sensor_data
    print("Received Sensor Data:", sensor_data)

    # Append the sensor data to the text file
    with open(file_path, "a") as file:
        file.write((sensor_data) + "\n")

# Close the socket when done
s.close()



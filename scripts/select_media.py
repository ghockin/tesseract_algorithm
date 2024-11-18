import cv2
import data_storage
import os

ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv'}

def allowed_file(filename):
    """Check if the uploaded file has a valid video extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def time_to_seconds(time_str):
    """Convert HH:MM:SS or MM:SS to seconds."""
    try:
        time_parts = time_str.split(":")
        time_parts = [int(part) for part in time_parts]
        
        if len(time_parts) == 3:
            return time_parts[0] * 3600 + time_parts[1] * 60 + time_parts[2]
        elif len(time_parts) == 2:
            return time_parts[0] * 60 + time_parts[1]
        return int(time_parts[0])
    except (ValueError, IndexError):
        return None

def get_video_duration(video_path):
    """Retrieve the total duration of the video in seconds."""
    vidcap = cv2.VideoCapture(video_path)
    fps = vidcap.get(cv2.CAP_PROP_FPS)
    frame_count = vidcap.get(cv2.CAP_PROP_FRAME_COUNT)
    duration = frame_count / fps
    return duration

def extract_frames(video_path, start_time, end_time, interval_time):
    """Extract frames from the video based on the specified start time, end time, and interval."""
    # Open the video file
    vidcap = cv2.VideoCapture(video_path)
    
    # Get the frame rate (fps) of the video
    fps = vidcap.get(cv2.CAP_PROP_FPS)
    
    # Convert time (in seconds) to frame numbers
    start_frame = int(start_time * fps)
    end_frame = int(end_time * fps)
    interval_frames = int(interval_time * fps)  # Frames to skip based on interval time
    
    current_frame = start_frame
    vidcap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)  # Move to the start frame

    extracted_frame_count = 0  # Initialize frame counter

    # Initialize the list to store timestamps for each extracted frame
    data_storage.extraction_times_in_seconds = []  # Ensure this list is initialized before use
    data_storage.list_of_images = []  # Ensure this list is initialized before use

    while current_frame <= end_frame:
        # Set the video position to the current frame
        vidcap.set(cv2.CAP_PROP_POS_FRAMES, current_frame)
        
        # Read the frame at this position
        success, image = vidcap.read()
        if not success:
            break  # Stop if there's an issue reading the frame
        
        # Save the current frame with a numerical name
        frame_path = os.path.join(data_storage.image_frames_path, f"frame_{extracted_frame_count}.jpg")
        cv2.imwrite(frame_path, image)
        data_storage.list_of_images.append(frame_path)
        
        # Calculate the timestamp in seconds
        timestamp = current_frame / fps  # Convert frame number to seconds
        data_storage.extraction_times_in_seconds.append(timestamp)  # Store the timestamp
        
        # Move to the next frame based on the interval
        current_frame += interval_frames
        
        # Increment the extracted frame counter
        extracted_frame_count += 1

    vidcap.release()  # Release the video capture object when done

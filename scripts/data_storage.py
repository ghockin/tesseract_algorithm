# scripts/data_storage.py
image_frames_path = 'static/images/frames/'
image_output_path = 'static/images/output/'
uploads_path = 'uploads/'
video_path = 'uploads/converted_video.mp4'
# extraction of video
extraction_times_in_seconds = []

# Variables to store extracted text and data
extracted_text = []
coordinate_data = []
number_data = []
time_data = []
list_of_images = []

# Video properties
video_length = 0  # Length of the video in seconds
file_path = None

# Logo placement settings
LOGO_X = 1.08
LOGO_Y = -0.1
logo_path = 'static/Logo.png'

#index graphs
index_coordinate = 1
index_number = 1
index_time = 1

#plot path
plot_path = 'static/plots/'
show_timestamps = None
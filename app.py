from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, abort, send_file, make_response
import os
import sys
sys.path.append(os.path.join(os.getcwd(), 'scripts'))
from select_media import allowed_file, time_to_seconds, get_video_duration, extract_frames
from tesseract_utils import select_roi_and_extract, extract_coordinates, extract_numbers, extract_time, process_images_in_folder
from plot_utils import plot_coordinate_graph, plot_number_graph, plot_time_graph
import data_storage as data_storage  # Import shared variables from data_storage
from check_folder_exists import check_folder  # Import shared variables from data_storage
import re
import csv
import subprocess

app = Flask(__name__)
app.secret_key = 'super secret key'

def new_load():
    check_folder(data_storage.image_frames_path)
    check_folder(data_storage.image_output_path)
    check_folder(data_storage.plot_path)
    check_folder(data_storage.uploads_path)

@app.route('/')
def index():  
    new_load()
    return render_template('index.html')

def convert_video():
    current_directory = os.path.dirname(os.path.abspath(__file__))
    bat_file = r"convert_video_script.bat"
    bat_file_path = os.path.join(current_directory, bat_file)
    result = subprocess.run(bat_file_path)


@app.route('/upload', methods=['POST'])
def upload_video():
    # Check if the 'video' key is in the request and if a file was uploaded
    if 'video' not in request.files or request.files['video'].filename == '':
        flash("No video file uploaded. Please select a video file.", 'error')
        return redirect(url_for('index'))

    video = request.files['video']
    
    # Check if the file has a valid video extension
    if not allowed_file(video.filename):
        flash("Invalid file format. Please upload a video file (MP4, AVI, MOV, MKV).", 'error')
        return redirect(url_for('index'))
    
    
    # Save video file to a temporary location
    video_path = os.path.join(data_storage.uploads_path, "video.mp4")
    video.save(video_path)
    
    convert_video()
    
    return redirect(url_for('get_edit_video'))


@app.route('/get_edit_video', methods=['GET'])
def get_edit_video():
    return render_template('edit_video.html')

@app.route('/edit_video', methods=['POST'])
def edit_video():
    video = data_storage.video_path
      
    # Get start_time, end_time, and interval_time from the form
    start_time_str = request.form['start_time']
    end_time_str = request.form['end_time']
    interval_time_str = request.form['interval_time']
    
    # Convert HH:MM:SS to total seconds
    start_time = time_to_seconds(start_time_str)
    end_time = time_to_seconds(end_time_str)
    interval_time = time_to_seconds(interval_time_str)
    
    # Check if time conversion was successful
    if start_time is None or end_time is None or interval_time is None:
        flash("Invalid time format! Please use HH:MM:SS format.", 'error')
        return redirect(url_for('index'))
   
    
    # Get the total video duration
    video_duration = get_video_duration(video)
    data_storage.video_length = video_duration

    # Check if start_time or end_time exceeds video duration
    if start_time > video_duration:
        flash(f"Start time exceeds video duration! The video is only {int(video_duration // 3600)}h {int((video_duration % 3600) // 60)}m {int(video_duration % 60)}s long.", 'error')
        return redirect(url_for('index'))
    
    if end_time > video_duration:
        flash(f"End time exceeds video duration! The video is only {int(video_duration // 3600)}h {int((video_duration % 3600) // 60)}m {int(video_duration % 60)}s long.", 'error')
        return redirect(url_for('index'))

    # Check if start_time is less than end_time
    if start_time >= end_time:
        flash("End time must be greater than Start time!", 'error')
        return redirect(url_for('index'))
    

    # Extract frames from video based on time range and interval
    extract_frames(video, start_time, end_time, interval_time)
    
    return redirect(url_for('select_data'))

@app.route('/select_data', methods=['GET', 'POST'])
def select_data():
    if request.method == 'POST':
        # Safely access 'data_type' using .get() to avoid KeyError
        data_type = request.form.get('data_type')

        # If 'data_type' is not selected, flash an error message and stay on the same page
        if not data_type:
            flash("No data type selected. Please select a data type.", 'error')
            return render_template('select_data.html', 
                                   coordinate_data=data_storage.coordinate_data, 
                                   number_data=data_storage.number_data, 
                                   time_data=data_storage.time_data)

        data_key = request.form.get('data_key')  # Capture the data key from the form
        
        # Process data based on selected data type
        if data_type == 'coordinate':
            extracted_data = process_images_in_folder(False)
            data_storage.coordinate_data.append({data_key: extracted_data['coordinates']})
        elif data_type == 'number':
            extracted_data = process_images_in_folder(True)
            data_storage.number_data.append({data_key: extracted_data['numbers']})
        elif data_type == 'time':
            extracted_data = process_images_in_folder(False)
            data_storage.time_data.append({data_key: extracted_data['times']})

    # Render select_data page with current data and any flashed messages
    return render_template('select_data.html', 
                           coordinate_data=data_storage.coordinate_data, 
                           number_data=data_storage.number_data, 
                           time_data=data_storage.time_data)


@app.route('/results')
def results():
    return render_template(
        'results.html',
        coordinate_data=data_storage.coordinate_data,
        number_data=data_storage.number_data,
        time_data=data_storage.time_data,
        enumerate=enumerate
    )


@app.route('/update_results', methods=['POST'])
def update_results():
    
    # Coordinate
    # Initialize an empty dictionary to hold parsed coordinates with dynamic keys
    parsed_coordinates = {}

    # Iterate over the form data to manually reconstruct the coordinates structure
    for key in request.form:
        if key.startswith('coordinate'):
            # Extract the actual coordinate key (e.g., 'number') and the field (degree, minute, etc.)
            key_parts = key.replace('coordinate[', '').replace(']', '').split('[')
            coord_key = key_parts[0]  # The key, e.g., 'number'
            coord_index = int(key_parts[1])  # The index, e.g., 0, 1, 2
            field = key_parts[2]  # The field, e.g., 'degree', 'minute', 'direction'

            # Initialize the dictionary for this key if it doesn't exist
            if coord_key not in parsed_coordinates:
                parsed_coordinates[coord_key] = []

            # Expand the list for this key if necessary
            while len(parsed_coordinates[coord_key]) <= coord_index:
                parsed_coordinates[coord_key].append({'degree': '', 'minute': '', 'direction': ''})

            # Retrieve and normalize the value (convert to uppercase for direction if needed)
            value = request.form[key].strip()
            if field == 'direction':
                value = value.upper()

            # Assign the value to the appropriate field
            parsed_coordinates[coord_key][coord_index][field] = value

    # Update the data storage with the parsed coordinates
    for key, coord_list in parsed_coordinates.items():
        if len(data_storage.coordinate_data) == 0:
            data_storage.coordinate_data.append({})

        existing_entry = None
        for entry in data_storage.coordinate_data:
            if key in entry:
                existing_entry = entry
                break

        if existing_entry is None:
            existing_entry = {key: ['' for _ in range(len(coord_list))]}
            data_storage.coordinate_data.append(existing_entry)

        # Fixing the degree and direction split correctly
        for coord_index, coord_values in enumerate(coord_list):
            degree_value = coord_values['degree']
            minute_value = coord_values['minute']
            direction_value = coord_values['direction']
            
            # Correctly format the coordinates by combining degree, minutes, and direction
            formatted_coord = f"{direction_value}{degree_value}°{minute_value}'"

            if coord_index < len(existing_entry[key]):
                existing_entry[key][coord_index] = formatted_coord
            else:
                existing_entry[key].append(formatted_coord)
                
    #Number
    # Initialize a dictionary to hold parsed number data
    parsed_numbers = {}

    # Iterate over the form data to reconstruct the number data structure
    for key in request.form:
        if key.startswith('number'):
            # Extract the number key and index
            key_parts = key.replace('number[', '').replace(']', '').split('[')
            number_key = key_parts[0]  # Dynamic data name (e.g., 'number_data_key')
            number_index = int(key_parts[1])  # Index of the number

            # Initialize the dictionary if the key doesn't exist
            if number_key not in parsed_numbers:
                parsed_numbers[number_key] = []

            # Add the value from the form to the appropriate index
            parsed_numbers[number_key].append(request.form[key])

    for number_key, values in parsed_numbers.items():
        for i, value in enumerate(values):
            # Assuming data_storage.number_data structure allows updating
            if len(data_storage.number_data) > 0 and number_key in data_storage.number_data[0]:
                data_storage.number_data[0][number_key][i] = value
            else:
                # If the key doesn't exist, initialize it
                data_storage.number_data.append({number_key: values})
                
    #Time
    for time_dict in data_storage.time_data:
        for key in time_dict.keys():
            for time_index in range(len(time_dict[key])):
                # Retrieve the updated hours, minutes, and seconds from the form
                hours = request.form.get(f"{key}_{time_index}_hours")
                minutes = request.form.get(f"{key}_{time_index}_minutes")
                seconds = request.form.get(f"{key}_{time_index}_seconds")

                # Combine them back into the HH:MM:SS format
                if hours and minutes and seconds:
                    seconds_float = float(seconds)
                    seconds_formatted = f"{seconds_float:.2f}"
                    time_dict[key][time_index] = f"{int(hours):02}:{int(minutes):02}:{seconds_formatted}"

    print(data_storage.coordinate_data)
    return redirect(url_for('results'))


@app.route('/show_graphs', methods=['GET', 'POST'])
def show_graphs():
    if request.method == 'POST':
        # Check if the checkbox for showing timestamps is checked
        data_storage.show_timestamps = 'show_timestamps' in request.form
        return redirect(url_for('get_plots'))  # Redirect to the plots generation route

    # GET request - load the graph page
    plot_filenames = os.listdir(data_storage.plot_path)
    
    return render_template('graphs.html', 
                           coordinate_data=data_storage.coordinate_data, 
                           number_data=data_storage.number_data, 
                           time_data=data_storage.time_data, 
                           plot_filenames=plot_filenames, 
                           show_timestamps=data_storage.show_timestamps,  # Pass show_timestamps to template
                           enumerate=enumerate)


@app.route('/get_plots', methods=['GET'])
def get_plots():
    index = 1  # Initialize indices for the plots
    if data_storage.coordinate_data:
        plot_coordinate_graph(data_storage.show_timestamps)  # No need to pass an index; it handles it internally

    if data_storage.number_data:
        plot_number_graph(data_storage.show_timestamps)  # No need to pass an index; it handles it internally

    if data_storage.time_data:
        plot_time_graph(data_storage.show_timestamps)  # No need to pass an index; it handles it internally

    return redirect(url_for('show_graphs'))


@app.route('/download/<filename>')
def download_file(filename):
    try:
        # Assuming data_storage.plot_path is the directory where plots are saved
        return send_from_directory(data_storage.plot_path, filename, as_attachment=True)
    except Exception as e:
        print(f"Error: {e}")
        abort(404)  # Return a 404 error if the file is not found



@app.route('/download_csv_coordinate', methods=['POST'])
def download_csv_coordinate():
    csv_file = 'output.csv'
    data = data_storage.coordinate_data
    # Extract the fieldnames (the keys from each dictionary)
    fieldnames = [key for entry in data for key in entry.keys()]

    # Assuming each key in the dictionary has the same number of entries
    num_entries = len(data[0][fieldnames[0]])  # Take the length from the first key's list
    
    # Prepare the data in row format (combine values by index)
    combined_data = []
    for i in range(num_entries):
        row = {key: entry[key][i] for entry in data for key in entry}
        combined_data.append(row)

    # Write to CSV
    with open(csv_file, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(combined_data)

    # Send the CSV file to the client
    with open(csv_file, 'rb') as file:
        response = make_response(file.read())
        response.headers['Content-Disposition'] = f'attachment; filename={csv_file}'
        response.headers['Content-Type'] = 'text/csv'
        return response

@app.route('/download_csv_number', methods=['POST'])
def download_csv_number():
    csv_file = 'output.csv'
    data = data_storage.number_data
    # Extract the fieldnames (the keys from each dictionary)
    fieldnames = [key for entry in data for key in entry.keys()]

    # Assuming each key in the dictionary has the same number of entries
    num_entries = len(data[0][fieldnames[0]])  # Take the length from the first key's list
    
    # Prepare the data in row format (combine values by index)
    combined_data = []
    for i in range(num_entries):
        row = {key: entry[key][i] for entry in data for key in entry}
        combined_data.append(row)

    # Write to CSV
    with open(csv_file, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(combined_data)

    # Send the CSV file to the client
    with open(csv_file, 'rb') as file:
        response = make_response(file.read())
        response.headers['Content-Disposition'] = f'attachment; filename={csv_file}'
        response.headers['Content-Type'] = 'text/csv'
        return response

@app.route('/download_csv_time', methods=['POST'])
def download_csv_time():
    csv_file = 'output.csv'
    data = data_storage.time_data
    # Extract the fieldnames (the keys from each dictionary)
    fieldnames = [key for entry in data for key in entry.keys()]

    # Assuming each key in the dictionary has the same number of entries
    num_entries = len(data[0][fieldnames[0]])  # Take the length from the first key's list
    
    # Prepare the data in row format (combine values by index)
    combined_data = []
    for i in range(num_entries):
        row = {key: entry[key][i] for entry in data for key in entry}
        combined_data.append(row)

    # Write to CSV
    with open(csv_file, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(combined_data)

    # Send the CSV file to the client
    with open(csv_file, 'rb') as file:
        response = make_response(file.read())
        response.headers['Content-Disposition'] = f'attachment; filename={csv_file}'
        response.headers['Content-Type'] = 'text/csv'
        return response


if __name__ == '__main__':
    app.run(debug=True)
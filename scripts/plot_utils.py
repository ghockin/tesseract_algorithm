import os
import matplotlib
matplotlib.use('Agg')  # Use a non-interactive backend for Flask
import matplotlib.pyplot as plt
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from matplotlib.ticker import FuncFormatter
import sys
sys.path.append(os.path.join(os.getcwd(), 'scripts'))
import data_storage as data_storage  # Import shared variables from data_storage

def dms_to_decimal(degrees, minutes, seconds):
    return degrees + (minutes / 60) + (seconds / 3600)

def convert_geographic_coordinate(coordinates):
    converted_coordinates = []
    
    for coord in coordinates:
        # Split the degrees part
        degree_part, remainder = coord.split('°')

        # Default values for minutes and seconds in case they are missing
        minute_part = '00'
        second_part = '00'

        # Try to split the minutes and seconds
        if "'" in remainder:
            minute_part, remainder = remainder.split("'")
            if '"' in remainder:
                second_part = remainder.split('"')[0]
        else:
            minute_part = remainder.split('"')[0] if '"' in remainder else '00'

        # Convert degree, minute, and second to decimal degrees
        degrees = float(degree_part)
        minutes = float(minute_part)
        seconds = float(second_part)  # Handles both whole and decimal seconds

        decimal_degrees = degrees + (minutes / 60) + (seconds / 3600)
        converted_coordinates.append(decimal_degrees)
    
    return converted_coordinates


# Function to convert HH:MM:SS to total seconds
def time_to_seconds(hms):
    h, m, s = map(float, hms.split(':'))
    return h * 3600 + m * 60 + s

# Function to format seconds back into HH:MM:SS for axis ticks
def seconds_to_hms(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = seconds % 60
    return f'{hours:02}:{minutes:02}:{seconds:05.2f}'

def calculate_timestamps(num_points, video_duration):
    return [i * (video_duration / (num_points - 1)) for i in range(num_points)]

def format_time_ticks(seconds):
    return seconds_to_hms(seconds)

def plot_coordinate_graph(show_timestamps):
    for index, coordinate_dict in enumerate(data_storage.coordinate_data):
        key = next(iter(coordinate_dict))  # Get the first key (user-provided)
        coordinates = coordinate_dict[key]  # Directly access the coordinate list
        data_plot = convert_geographic_coordinate(coordinates)

        # Use stored timestamps for plotting
        time_points = data_storage.extraction_times_in_seconds[:len(data_plot)]  # Ensure you only use relevant timestamps

        plt.figure(figsize=(10, 5))
        ax = plt.gca()

        ax.plot(time_points, data_plot, marker='o', linestyle='-', color='green')
        ax.set_title(f'Coordinate Values over Time - Plot {key}')
        ax.set_xlabel('Time Points (HH:MM:SS)')
        ax.set_ylabel('Coordinates (Decimal Degrees)')
        
        # Format x-axis to show HH:MM:SS
        ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: seconds_to_hms(x)))

        # Add timestamps if the option is selected
        if show_timestamps:
            for i, time in enumerate(time_points):
                ax.annotate(f"{seconds_to_hms(time)}", (time, data_plot[i]), textcoords="offset points", xytext=(0,10), ha='center')

        ax.grid(True)

        # Add logo to the plot
        logo_img = plt.imread(data_storage.logo_path)
        imagebox = OffsetImage(logo_img, zoom=0.5)
        ab = AnnotationBbox(imagebox, (data_storage.LOGO_X, data_storage.LOGO_Y), xycoords='axes fraction', frameon=False, box_alignment=(1, 0))
        ax.add_artist(ab)

        # Save the plot with the new filename format
        file_path = f'{data_storage.plot_path}{key}_plot_{index}.jpg'  # Save with dictionary name and index
        plt.savefig(file_path, bbox_inches='tight', pad_inches=0.3)
        plt.close()

def plot_number_graph(show_timestamps):
    for index, number_dict in enumerate(data_storage.number_data):
        key = next(iter(number_dict))  # Get the first key (user-provided)
        data_plot = number_dict[key]  # Directly access the number list
        
        plt.figure(figsize=(10, 5))
        ax = plt.gca()

        num_points = len(data_plot)

        # Calculate time points based on video duration
        time_points = calculate_timestamps(num_points, data_storage.video_length)

        ax.plot(time_points, data_plot, marker='o', linestyle='-', color='blue')
        ax.set_title(f'Number Values over Time - Plot {key}')
        ax.set_xlabel('Time Points (HH:MM:SS)')
        ax.set_ylabel('Numbers')

        # Format x-axis to show HH:MM:SS
        ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: format_time_ticks(x)))

        # Add timestamps if the option is selected
        if show_timestamps:
            for i, time in enumerate(time_points):
                ax.annotate(f"{seconds_to_hms(time)}", (time, data_plot[i]), textcoords="offset points", xytext=(0,10), ha='center')

        ax.grid(True)

        # Add the logo to the plot
        logo_img = plt.imread(data_storage.logo_path)
        imagebox = OffsetImage(logo_img, zoom=0.5)
        ab = AnnotationBbox(imagebox, (data_storage.LOGO_X, data_storage.LOGO_Y), xycoords='axes fraction', frameon=False, box_alignment=(1, 0))
        ax.add_artist(ab)

        # Save the plot with the new filename format
        file_path = f'{data_storage.plot_path}{key}_plot_{index}.jpg'  # Save with dictionary name and index
        plt.savefig(file_path, bbox_inches='tight', pad_inches=0.3)
        plt.close()

def plot_time_graph(show_timestamps):
    for index, time_dict in enumerate(data_storage.time_data):
        key = next(iter(time_dict))  # Get the first key (user-provided)
        data_plot = time_dict[key]  # Directly access the time list for the current dictionary

        plt.figure(figsize=(10, 5))
        ax = plt.gca()

        # Convert the time data to seconds
        data_plot_seconds = [time_to_seconds(t) for t in data_plot]
        num_points = len(data_plot_seconds)

        # Generate time points based on the video length
        time_points = calculate_timestamps(num_points, data_storage.video_length)

        # Plot the time data
        ax.plot(time_points, data_plot_seconds, marker='o', linestyle='-', color='red')
        ax.set_title(f'Time Values over Time - Plot {key}')
        ax.set_xlabel('Time Points (HH:MM:SS)')
        ax.set_ylabel('Time (seconds)')

        # Format the Y-axis to show HH:MM:SS
        ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: seconds_to_hms(int(x))))

        # Format x-axis to show HH:MM:SS
        ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: format_time_ticks(x)))

        # Add timestamps if the option is selected
        if show_timestamps:
            for i, time in enumerate(time_points):
                ax.annotate(f"{seconds_to_hms(time)}", (time, data_plot_seconds[i]), textcoords="offset points", xytext=(0,10), ha='center')

        ax.grid(True)

        # Add the logo to the plot
        logo_img = plt.imread(data_storage.logo_path)
        imagebox = OffsetImage(logo_img, zoom=0.5)
        ab = AnnotationBbox(imagebox, (data_storage.LOGO_X, data_storage.LOGO_Y), xycoords='axes fraction', frameon=False, box_alignment=(1, 0))
        ax.add_artist(ab)

        # Save the plot with the new filename format
        file_path = f'{data_storage.plot_path}{key}_plot_{index}.jpg'  # Save with dictionary name and index
        plt.savefig(file_path, bbox_inches='tight', pad_inches=0.3)
        plt.close()

import cv2
import pytesseract
import re
import unicodedata
import os
import data_storage
current_dir = os.path.dirname(__file__)
parent_dir = os.path.abspath(os.path.join(current_dir, "../"))
file_path = os.path.join(parent_dir, "assets\\Tesseract-OCR\\Tesseract-OCR\\tesseract.exe")
pytesseract.pytesseract.tesseract_cmd = file_path

def select_roi_and_extract(filepath, is_number):
    img = cv2.imread(filepath)
    clone = img.copy()

    if img is None:
        print("Error: Could not load the image. Please check the file path.")
        return None, None

    roi = cv2.selectROI("Select ROI", img, fromCenter=False, showCrosshair=False)
    cv2.destroyAllWindows()

    x, y, w, h = roi
    if w and h:
        roi_img = clone[y:y+h, x:x+w]
        gray = cv2.cvtColor(roi_img, cv2.COLOR_BGR2GRAY)
        if is_number:
            text = pytesseract.image_to_string(roi_img, config="--psm 7 -c tessedit_char_whitelist=0123456789")
        else:
            text = pytesseract.image_to_string(gray, config='--psm 7')

        return text, (x, y, w, h)
    
    return None, None

def extract_time(text):
    if text is None:
        return '00:00:00'  # Return a default value if text is None
    time_pattern = r'(\b[0-1]?[0-9]:[0-5][0-9](?::[0-5][0-9])?\s?(?:AM|PM)?\b)'
    times = re.findall(time_pattern, text.strip())
    return times[0] if times else '00:00:00'

def extract_numbers(text):
    if text is None:
        return '0'  # Return a default value if text is None
    number_pattern = re.sub(r'[^0-9]+', '', text.strip())
    return number_pattern if number_pattern else '0'

def transform_coordinate(coord):
    # Check if the coordinate is already in the correct format
    if is_correct_format(coord):
        return coord  # If already correct, return as is

    # Extract the direction (last character)
    direction = coord[-1]  # Last character (E, W, N, S)
    degree_part = coord[:-1]  # Everything except the direction

    # Ensure the degree part contains exactly one degree symbol
    if '°' not in degree_part:
        raise ValueError("Input coordinate does not contain a degree symbol.")

    # Split at the degree symbol
    degree_parts = degree_part.split('°')
    if len(degree_parts) != 2:
        raise ValueError("Invalid coordinate format. Expected format: 'degrees°minutesseconds'.")

    degrees = degree_parts[0]  # Extract the degrees
    minutes_seconds = degree_parts[1]  # The rest after the degree symbol

    # Initialize minutes and seconds
    minutes = '00'
    seconds = '00.0'  # Default seconds format with decimal

    # Determine minutes and seconds based on length of minutes_seconds
    if len(minutes_seconds) >= 4:
        minutes = minutes_seconds[:2]  # First two characters are minutes
        seconds = minutes_seconds[2:]  # Remaining characters are seconds
        if len(seconds) == 0:  # In case of no seconds provided
            seconds = '0.0'  # Default to 0.0
        elif len(seconds) == 1:  # If only one digit is provided
            seconds = seconds + '0.0'  # Pad with a zero and add .0
        elif len(seconds) > 2:  # More than two digits in seconds
            seconds = seconds[:2] + '.0'  # Keep only the first two digits for seconds

    elif len(minutes_seconds) == 3:  # If we have three characters
        minutes = '00'  # Assume minutes are 00
        seconds = minutes_seconds + '0'  # Assume they are seconds and add .0
        seconds = seconds[:2] + '.0'  # Ensure it has a decimal point
    elif len(minutes_seconds) == 2:  # If we only have two characters
        minutes = minutes_seconds  # Assume they are minutes
        seconds = '00.0'  # Default seconds
    elif len(minutes_seconds) == 1:  # If we have one character
        minutes = '0' + minutes_seconds  # Pad to two digits
        seconds = '00.0'  # Default seconds

    # Format into the desired structure
    transformed_coord = f"{degrees}°{minutes}'{seconds}\"{direction}"
    return transformed_coord


def is_correct_format(coord):
    """Check if the coordinate is in the correct format: degrees°minutes'seconds.s"direction."""
    
    # Basic checks to ensure the string has enough length and expected characters
    if len(coord) < 5:  # Minimum length to contain degrees, minutes, seconds, and direction
        return False

    # Check for presence of necessary characters
    if '°' not in coord or "'" not in coord or '"' not in coord:
        return False
    
    # Ensure the degree part is correct
    degree_index = coord.index('°')
    if degree_index + 1 >= len(coord) or not coord[degree_index + 1].isdigit():
        return False

    # Ensure there is a single quote after degrees and it has digits
    minute_index = coord.index("'")
    if minute_index <= degree_index + 1 or not coord[degree_index + 1:minute_index].isdigit():
        return False

    # Ensure there is a double quote after minutes and it has valid seconds
    second_index = coord.index('"')
    if second_index <= minute_index + 1 or not coord[minute_index + 1:second_index].replace('.', '', 1).isdigit():
        return False

    # Check that the last character is a valid direction
    return coord[-1] in "NSEW"





def extract_coordinates(text):
    if text is None:
        return '00°00\'00.0"E'  # Return a default value if text is None
    
    # Normalize and clean the text
    normalized_text = unicodedata.normalize('NFKC', text.strip())
    cleaned_text = normalized_text.replace(' ', '').replace('\\', '').replace(',', '.')

    # Check for a hyphen and prepare a prefix
    prefix = '-' if '-' in cleaned_text else ''

    # Regular expression pattern to match coordinates, making ' and " optional
    coordinate_pattern = r'(\d{1,3}°\d{1,2}\'?\d{1,2}[.,]?\d{1,2}"?[NS]?)|(\d{1,3}°\d{1,2}\'?\d{1,2}[.,]?\d{1,2}"?[EW]?)'
    
    # Find coordinates in the text
    coordinates = re.findall(coordinate_pattern, cleaned_text)
    flattened_coordinates = [coord for sublist in coordinates for coord in sublist if coord]
    
    # Check if any coordinate is found
    if flattened_coordinates:
        coord = flattened_coordinates[0]
        
        # Add the prefix if present
        coord = prefix + coord
        
        # Check if the coordinate has no direction and add default "E" if necessary
        if coord[-1] not in "NSEW":  # Last character not a direction
            coord += "E"
        
        print("Original coordinate:", coord)  # Debugging statement
        
        # Transform the coordinate and capture the result
        transformed_coord = transform_coordinate(coord)
        
        # Append the transformed coordinate to the extracted text
        data_storage.extracted_text.append(transformed_coord)
        
        return transformed_coord
    
    return '00°00\'00.0"E'  # Default if no valid coordinate found




def process_images_in_folder(folder_path, is_number):
    first_image = True
    roi_coords = None
    
    results = {
        'coordinates': [],
        'numbers': [],
        'times': []
    }

    for filename in os.listdir(folder_path):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            filepath = os.path.join(folder_path, filename)

            if first_image:
                text, roi_coords = select_roi_and_extract(filepath, is_number)
                first_image = False
            else:
                img = cv2.imread(filepath)
                roi_img = img[roi_coords[1]:roi_coords[1]+roi_coords[3], roi_coords[0]:roi_coords[0]+roi_coords[2]]
                gray = cv2.cvtColor(roi_img, cv2.COLOR_BGR2GRAY)
                if is_number:
                    text = pytesseract.image_to_string(roi_img, config="--psm 7 -c tessedit_char_whitelist=0123456789")
                else:
                    text = pytesseract.image_to_string(gray, config='--psm 7')

            # Collect data based on extracted text
            if text:  # Ensure text is not None
                coordinates = extract_coordinates(text)
                numbers = extract_numbers(text)
                times = extract_time(text)

                # Ensure longitude is non-empty
                if not coordinates:
                    coordinates = '00°00\'00.0"E'  # Default value for empty coordinates

                if not numbers:
                    numbers = '0'  # Default value for empty numbers

                results['coordinates'].append(coordinates)
                results['numbers'].append(numbers)
                results['times'].append(times)
            else:
                # Append default values if no text is found
                results['coordinates'].append('00°00\'00.0"E')
                results['numbers'].append('0')
                results['times'].append('00:00:00')
    print(results['coordinates'])
    return results



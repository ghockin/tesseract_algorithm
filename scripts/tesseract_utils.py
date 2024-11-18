import cv2
import pytesseract
import re
import unicodedata
import os
import data_storage
import ctypes

# Set Tesseract executable path
current_dir = os.path.dirname(__file__)
parent_dir = os.path.abspath(os.path.join(current_dir, "../"))
file_path = os.path.join(parent_dir, "assets\\Tesseract-OCR\\Tesseract-OCR\\tesseract.exe")
pytesseract.pytesseract.tesseract_cmd = file_path

# Function to select ROI and extract text
def select_roi_and_extract(filepath, is_number):
    img = cv2.imread(filepath)
    clone = img.copy()

    if img is None:
        print("Error: Could not load the image. Please check the file path.")
        return None, None

    # Get screen resolution using ctypes for Windows
    user32 = ctypes.windll.user32
    screen_width, screen_height = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)

    # Get image size
    img_height, img_width = img.shape[:2]

    # Calculate scale factor while maintaining aspect ratio
    scale_factor = min(screen_width / img_width, screen_height / img_height)

    # If the scale factor is less than 1, resize to fit the screen, else use original size
    if scale_factor < 1:
        new_width = int(img_width * scale_factor)
        new_height = int(img_height * scale_factor)
        img_display = cv2.resize(img, (new_width, new_height))
    else:
        img_display = img  # No resize needed if the image is already smaller than the screen

    # Create a named window and resize it to the scaled size for display
    cv2.namedWindow("Select ROI", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Select ROI", img_display.shape[1], img_display.shape[0])

    # Show the resized image to select ROI
    roi = cv2.selectROI("Select ROI", img_display, fromCenter=False, showCrosshair=False)
    cv2.destroyAllWindows()

    x, y, w, h = roi
    if w and h:
        roi_img = clone[y:y+h, x:x+w]  # Use the original image for ROI extraction
        gray = cv2.cvtColor(roi_img, cv2.COLOR_BGR2GRAY)
        if is_number:
            text = pytesseract.image_to_string(roi_img, config="--psm 7 -c tessedit_char_whitelist=0123456789")
        else:
            text = pytesseract.image_to_string(gray, config='--psm 7')

        return text, (x, y, w, h)

    return None, None

def transform_coordinate(coord, direction=None):
    # If the direction is not passed explicitly, we check if it is part of the coordinate.
    if direction is None:
        direction = re.match(r"([nsewNSEW])", coord)
        direction = direction.group(1) if direction else 'N'  # Default to 'N' if no direction
    
    # Remove invalid characters (retain digits, °, ., and nsewNSEW)
    sanitized_coord = re.sub(r"[^nsewNSEW\d°.\s]", "", coord)
    
    # Match the coordinate pattern (degrees and minutes with optional direction)
    match = re.match(r"(\d{1,2})°(\d+)(\.\d+)?", sanitized_coord)
    
    if not match:
        raise ValueError(f"Invalid coordinate format. Could not parse: {coord}")
    
    # Extract degrees and minutes
    degrees = match.group(1)
    minutes = match.group(2) + (match.group(3) if match.group(3) else "")  # Ensure minutes are captured

    # Ensure degrees have two digits (padding with 0 if necessary)
    if len(degrees) == 1:
        degrees = '0' + degrees
    
    # Uppercase the direction and attach it
    direction = direction.upper()

    # Combine into a properly formatted coordinate
    transformed_coord = f"{direction}{degrees}°{minutes}"
    
    return transformed_coord

def extract_coordinates(text):
    # Regex pattern to match coordinates (direction + degree format with potential spaces)
    coord_pattern = r"([nsewNSEW]?\d{1,2})°(\d+)(\.\d+)?"
    
    for match in re.finditer(coord_pattern, text):
        coord = match.group(0)
        
        # Extract the direction explicitly (if present) and pass it along with the coordinate
        direction = match.group(1) if match.group(1) in 'nsewNSEW' else None
        transformed_coord = transform_coordinate(coord, direction)
        #coordinates.append(transformed_coord)  # Keep it as a list of lists, as per your output structure
    
    return transformed_coord

# Extract numbers
def extract_numbers(text):
    if text is None:
        return '0'  # Return a default value if text is None
    number_pattern = re.sub(r'[^0-9]+', '', text.strip())
    return number_pattern if number_pattern else '0'

# Extract time from text
def extract_time(text):
    if text is None:
        return '00:00:00'  # Return a default value if text is None
    time_pattern = r'(\b[0-1]?[0-9]:[0-5][0-9](?::[0-5][0-9])?\s?(?:AM|PM)?\b)'
    times = re.findall(time_pattern, text.strip())
    return times[0] if times else '00:00:00'

# Process images in folder
def process_images_in_folder(is_number):
    first_image = True
    roi_coords = None

    results = {
        'coordinates': [],
        'numbers': [],
        'times': []
    }

    for filename in data_storage.list_of_images:
        if first_image:
            text, roi_coords = select_roi_and_extract(filename, is_number)
            first_image = False
        else:
            img = cv2.imread(filename)
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
                coordinates = '00°00.00E'  # Default value for empty coordinates (as a list of lists)

            if not numbers:
                numbers = '0'  # Default value for empty numbers

            # Append coordinates, numbers, and times independently
            results['coordinates'].append(coordinates)
            results['numbers'].append(numbers)
            results['times'].append(times)
        else:
            # Append default values if no text is found
            results['coordinates'].append('00°00.00E')
            results['numbers'].append('0')
            results['times'].append('00:00:00')
    
    return results

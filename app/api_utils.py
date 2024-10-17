from flask import jsonify

def extract_and_validate_json(request, required_fields, numeric_fields=None):
    """
    Extracts JSON data from the request and validates that all required fields are present and optionally checks if some fields are numeric.
    
    Args:
        request: The incoming request object.
        required_fields: List of fields that must be present in the JSON data.
        numeric_fields: Optional list of fields that must be numeric.
    
    Returns:
        Tuple: (data, error) - where 'data' is the extracted JSON data (or None if invalid), 
        and 'error' is a string message (or None if valid).
    """
    data = request.get_json()
    if not data:
        return None, 'No data provided'
    
    # Check for missing required fields
    missing_fields = [field for field in required_fields if field not in data or data[field] is None]
    if missing_fields:
        return None, f"Missing fields: {', '.join(missing_fields)}"
    
    # If numeric_fields are specified, check if those fields are numbers
    if numeric_fields:
        for field in numeric_fields:
            if field in data and not isinstance(data[field], (int, float)):
                return None, f"{field} must be a number"
    
    return data, None


def generate_response(data=None, error=None, status_code=200):
    """
    Generate a JSON response.
    
    Args:
        data: The data to include in the response.
        error: An error message, if any.
        status_code: The HTTP status code for the response.
    
    Returns:
        Flask JSON response.
    """
    if error:
        return jsonify({'error': error}), status_code
    return jsonify(data), status_code

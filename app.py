import os
import json
from flask import Flask, request, render_template, jsonify
import openai
import logging

# Initialize Flask app
app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# OpenAI API Key
openai.api_key = "KEY HERE"

# Path to JSON data file
DATA_FILE = '/Users/travis/Desktop/Projects/tamuHack25/Tamuhack_25_new/static/data/nyc_schools_energy_dynamodb.json'

def load_borough_data(file_path, borough):
    """Load and filter data for a specific borough from a JSON file."""
    logger.debug(f"Checking if file exists: {file_path}")
    if not os.path.exists(file_path):
        logger.error(f"{file_path} not found.")
        raise FileNotFoundError(f"{file_path} not found.")

    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        logger.debug("JSON file loaded successfully")

        # Filter data by borough
        borough_data = [entry for entry in data if entry['Borough'].lower() == borough.lower()]
        return borough_data
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON file: {e}")
        raise

def predict_with_openai(borough_data, prompt):
    """
    Use OpenAI API to predict the next year's energy usage and suggestions
    based on borough-specific historical data and user inputs.
    """
    logger.debug("--- Prompt Sent to OpenAI ---")
    logger.debug(prompt)

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant for predicting energy usage."},
                {"role": "user", "content": prompt}
            ]
        )

        logger.debug("--- Raw OpenAI Response ---")
        raw_response = response["choices"][0]["message"]["content"].strip()
        logger.debug(raw_response)

        # Parse the response as JSON
        try:
            parsed_response = json.loads(raw_response)
            return {
                "predictions": parsed_response.get("predictions", {}),
                "suggestions": parsed_response.get("suggestions", {})
            }
        except json.JSONDecodeError:
            logger.error("Failed to parse OpenAI response. Returning raw text.")
            return {"error": raw_response}

    except Exception as e:
        logger.error("--- Error Occurred ---")
        logger.error(str(e))
        raise RuntimeError(f"Error using OpenAI API: {str(e)}")

@app.route('/')
def home():
    """Render the home page."""
    logger.info("Rendering home page.")
    return render_template('home.html')

@app.route('/about')
def about():
    """Render the About page."""
    logger.info("Rendering about page.")
    return render_template('about.html')

@app.route('/statistics')
def statistics():
    """Render the Statistics page."""
    logger.info("Rendering statistics page.")
    return render_template('statistics.html')

@app.route('/optimize', methods=['GET', 'POST'])
@app.route('/optimize', methods=['GET', 'POST'])
def optimize():
    """Render the Optimization page and include prediction data."""
    try:
        if request.method == 'POST':
            user_inputs = request.get_json() or {}

            logger.debug(f"User Inputs (Raw): {user_inputs}")

            # Validate required inputs
            required_fields = [
                "borough", "squareFootage", "staffOccupancy", "studentOccupancy", "numberOfFloors",
                "windowInsulation", "hvacSystem", "averageHoursOperation", "peakHours"
            ]

            missing_fields = [field for field in required_fields if not user_inputs.get(field)]

            if missing_fields:
                error_message = f"Missing required fields: {', '.join(missing_fields)}"
                logger.warning(error_message)
                return jsonify({"error": error_message, "predictions": {}, "suggestions": {}})

            borough = user_inputs.get("borough")
            borough_data = load_borough_data(DATA_FILE, borough)

            if not borough_data:
                error_message = f"No data found for borough: {borough}"
                logger.warning(error_message)
                return jsonify({"error": error_message, "predictions": {}, "suggestions": {}})

            # Batch API Request
            all_features = ["ElectricityCost", "GasUsage", "SteamUsage", "TotalUsage"]
            historical_data = {feature: [entry[feature] for entry in borough_data][-12:] for feature in all_features}

            # Prepare prompt
            prompt = (
                "Given the following historical data for a borough and user-specific inputs, "
                "predict the energy usage for the next 12 months as a JSON object. The object must include:\n"
                "1. `predictions`: A dictionary with keys for each feature (`ElectricityCost`, `GasUsage`, "
                "`SteamUsage`, `TotalUsage`) containing an array of 12 numbers each.\n"
                "2. `suggestions`: A dictionary with keys for each feature and up to 1 unique suggestions for "
                "eco-friendly improvements.\n\n"
                f"Historical Data: {json.dumps(historical_data, indent=2)}\n\nUser Inputs: {json.dumps(user_inputs, indent=2)}\n\nJSON Object:"
            )

            response = predict_with_openai(borough_data, prompt)

            if "error" in response:
                logger.warning("Failed to get predictions. Returning error response.")
                return jsonify({"error": response["error"], "predictions": {}, "suggestions": {}})

            logger.debug(f"Predictions and Suggestions: {response}")
            return jsonify(response)

        return render_template('optimize.html', predictions={}, suggestions=[])

    except Exception as e:
        logger.error(f"Error in Optimize Route: {e}")
        return jsonify({"error": str(e), "predictions": {}, "suggestions": {}})

if __name__ == "__main__":
    logger.info("--- Starting Flask App ---")
    app.run(debug=True, port=8000)

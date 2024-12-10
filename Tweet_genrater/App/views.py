from django.shortcuts import render
from django.http import JsonResponse
import pandas as pd
import google.generativeai as genai
import os
import logging
import traceback

from django.http import JsonResponse

def zyb_tracker_statistics_action(request):
    # Log the incoming request for analysis
    logging.debug(f"Received request at /hybridaction/zybTrackerStatisticsAction: {request.GET}")
    return JsonResponse({"message": "Endpoint is not implemented"}, status=404)
# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Configure Gemini API using environment variable
API_KEY = "AIzaSyCAfrJKPuP1GpBEdUl1j0vWAevWBXuTSlA"
if not API_KEY:
    logging.error("Gemini API key is not set in environment variables")
    API_KEY = ""  # Placeholder to avoid crashes

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# File paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TWEETS_FILE = os.path.join(BASE_DIR, "tweets.csv")
LINKEDIN_FILE = os.path.join(BASE_DIR, "linkedin.csv")
FACEBOOK_FILE = os.path.join(BASE_DIR, "facebook.csv")
BIODATA_FILE = os.path.join(BASE_DIR, "biodata.txt")

def index(request):
    # This will render the index.html template
    return render(request, "index.html")

def generate_tweet(request):
    try:
        if request.method == "POST":
            # Get the topic from the POST request
            data = request.POST.get("topic", "").strip()

            # Log received topic for debugging
            logging.debug(f"Received topic: {data}")

            # Validate file existence
            if not os.path.exists(TWEETS_FILE):
                logging.error(f"File not found: {TWEETS_FILE}")
                return JsonResponse({"error": "tweets.csv file not found!"}, status=400)

            # Load tweets data
            tweets_df = pd.read_csv(TWEETS_FILE)
            if "TweetText" not in tweets_df.columns:
                return JsonResponse({"error": "'TweetText' column missing in tweets.csv!"}, status=400)

            # Load additional context
            linkedin_context, facebook_context, biodata_context = "", "", ""

            if os.path.exists(LINKEDIN_FILE):
                linkedin_df = pd.read_csv(LINKEDIN_FILE)
                linkedin_context = "\n\n".join(
                    [f"LinkedIn Post: {row.get('postText', '')}" for _, row in linkedin_df.iterrows()]
                )

            if os.path.exists(FACEBOOK_FILE):
                facebook_df = pd.read_csv(FACEBOOK_FILE)
                facebook_context = "\n\n".join(
                    [f"Facebook Author: {row.get('Author', '')}\nContent: {row.get('Content', '')}\nPostedAt: {row.get('Posted At', '')}" for _, row in facebook_df.iterrows()]
                )

            if os.path.exists(BIODATA_FILE):
                with open(BIODATA_FILE, "r") as file:
                    biodata_context = file.read().strip()

            # Combine all contexts
            context_parts = [
                f"Author: {row.get('Author', '')}\nType: {row.get('Type', '')}\nTweet: {row.get('TweetText', '')}\nCreatedAt: {row.get('CreatedAt', '')}\nMedia: {row.get('Media', '')}"
                for _, row in tweets_df.iterrows()
            ]
            context = "\n\n".join(context_parts)
            combined_context = f"{context}\n\n{linkedin_context}\n\n{facebook_context}\n\nBiodata:\n{biodata_context}"

            # Add the user's topic to the prompt if provided
            if data:
                combined_context += f"\n\nTopic: {data}"

            # Create the prompt
            prompt = (
                f"Forget all prior data. "
                f"DO NOT repeat tweets previously generated. "
                f"If a topic is provided, create tweets focused on that topic: {data}.\n\n"
                f"Based on the person's past posts and context:\n{combined_context}\n\n"
                f"Generate 10 realistic tweets that match the tone, style, and beliefs of the user, without mentioning real-time events or recent activities."
            )

            # Generate tweets using Gemini API
            response = model.generate_content(prompt)

            if response and response.text:
                generated_tweets = [tweet.strip() for tweet in response.text.split("\n") if tweet.strip()]
                logging.debug(f"Generated tweets: {generated_tweets}")
                return JsonResponse({"tweets": generated_tweets}, status=200)
            else:
                return JsonResponse({"error": "No tweets could be generated"}, status=400)
        else:
            return JsonResponse({"error": "Invalid request method"}, status=405)

    except Exception as e:
        # Detailed error logging
        logging.error(f"Error in generate_tweet: {str(e)}")
        logging.error(traceback.format_exc())
        return JsonResponse({"error": f"An unexpected error occurred: {str(e)}"}, status=500)

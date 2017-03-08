import urllib2
import json


def lambda_handler(event, context):
    # if (event["session"]["application"]["applicationId"] !=
    #         "amzn1.ask.skill.???"):
    #     raise ValueError("Invalid Application ID")
    if event["request"]["type"] == "LaunchRequest":
        return on_launch(event["request"], event["session"])
    elif event["request"]["type"] == "IntentRequest":
        return on_intent(event["request"], event["session"])


def on_launch(launch_request, session):
    card_title = "Welcome"
    speech_output = "Recipe assistant, what recipe would you like to make?"
    return build_response(build_speechlet_response(speech_output, card_title))


def on_intent(intent_request, session):
    intent = intent_request["intent"]
    intent_name = intent_request["intent"]["name"]

    # if "attributes" in session and session["attributes"].get("example", False):
    #     pass

    if intent_name == "FindIntent":
        return find_recipe(intent)

    elif intent_name == "AMAZON.CancelIntent":
        return handle_session_end_request()
    elif intent_name == "AMAZON.StopIntent":
        return handle_session_end_request()

    else:
        raise ValueError("Invalid intent")


def find_recipe(intent):
    recipes = json.loads(urllib2.urlopen("https://ffgh18ctp9.execute-api."
        "us-east-1.amazonaws.com/prod/RecipeUpdate?TableName=Recipes").read())
    query = intent["slots"]["SearchTerms"]["value"].lower()
    for recipe in recipes["Items"]:
        if recipe["RecipeName"].lower() == query:
            return begin_recipe(recipe)

    card_title = "Recipe not found"
    speech_output = "Sorry, I couldn't find your recipe."
    return build_response(build_speechlet_response(speech_output, card_title))


def begin_recipe(recipe):
    card_title = "Found recipe!"
    speech_output = "I found your recipe for {}.".format(recipe["RecipeName"])
    session_attributes = {"recipe": recipe}
    return build_response(build_speechlet_response(speech_output, card_title),
        session_attributes)


def handle_session_end_request():
    card_title = "Thank you!"
    speech_output = "Thank you for using Recipe Assistant."
    return build_response(build_speechlet_response(speech_output, card_title,
        should_end_session=True))


def build_speechlet_response(speech_output, card_title=None,
    card_output=None, reprompt_text=None, should_end_session=False):

    if card_output is None:
        card_output = speech_output

    return {
        "outputSpeech": {
            "type": "PlainText",
            "text": speech_output
        },
        "card": {
            "type": "Simple",
            "title": card_title,
            "subtitle": "Recipe Assistant",
            "content": card_output
        },
        "reprompt": {
            "outputSpeech": {
                "type": "PlainText",
                "text": reprompt_text
            }
        },
        "shouldEndSession": should_end_session
    }


def build_response(speechlet_response, session_attributes={}):
    return {
        "version": "1.0",
        "response": speechlet_response,
        "sessionAttributes": session_attributes
    }

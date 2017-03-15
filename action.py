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

    if "attributes" in session and session["attributes"].get("inRecipe", False):
        if intent_name == "HomeIntent":
            return go_to_home(intent, session)
        elif session["attributes"].get("readingIngredients", False):
            if intent_name == "PrevIngredIntent":
                session["attributes"]["ingredientIndex"] -= 1
            elif intent_name == "NextIngredIntent":
                session["attributes"]["ingredientIndex"] += 1
            elif intent_name == "RestartIntent":
                session["attributes"]["ingredientIndex"] = 0
            return read_ingredient(intent, session)
        elif session["attributes"].get("readingDirections", False):
            if intent_name == "PrevInstIntent":
                session["attributes"]["directionIndex"] -= 1
            elif intent_name == "NextInstIntent":
                session["attributes"]["directionIndex"] += 1
            elif intent_name == "RestartIntent":
                session["attributes"]["directionIndex"] = 0
            return read_direction(intent, session)
        elif intent_name == "StartIngredIntent":
            return read_ingredient(intent, session)
        elif intent_name == "StartInstIntent":
            return read_direction(intent, session)

    elif intent_name == "GeneralQueryIntent":
        return general_query_message(intent, session)

    elif intent_name == "FindIntent":
        return find_recipe(intent)

    elif intent_name == "HomeIntent":
        return go_to_home(intent, session)

    else:
        raise ValueError("Invalid intent")


def general_query_message(intent, session):
    card_title = "Answer General Query"
    speech_output = (
        "You are at the main menu. You can ask me to find any of "
        "the recipes that you have added on the website. If I find the "
        "recipe, you can ask me to read the ingredient list or to read the "
        "recipe. If asked, I will read off each item one by one. After an "
        "item is stated, you can move on to the next item, or, go back to the "
        "previous item. You can restart the list at any time. You can exit "
        "the ingredients, recipe list, or recipe itself and will be taken "
        "back to the main menu."
    )
    return build_response(build_speechlet_response(speech_output, card_title))


def find_recipe(intent):
    recipes = json.loads(urllib2.urlopen("https://ffgh18ctp9.execute-api."
        "us-east-1.amazonaws.com/prod/RecipeUpdate?TableName=Recipes").read())
    query = intent["slots"]["SearchTerms"]["value"].lower()
    for recipe in recipes["Items"]:
        if recipe["RecipeName"].lower() == query:
            return begin_recipe(recipe)

    card_title = "Recipe not found"
    speech_output = ('Sorry, I could not find "' + query
        + '" in your list of recipes.')
    return build_response(build_speechlet_response(speech_output, card_title))


def begin_recipe(recipe):
    card_title = "Found recipe!"
    speech_output = "I found your recipe for {}.".format(recipe["RecipeName"])
    session_attributes = {
        "inRecipe": True,
        "name": recipe["RecipeName"],
        "ingredients": recipe["Ingredients"].split("\n"),
        "directions": recipe["Directions"].split("\n"),
        "ingredientIndex": 0,
        "directionIndex": 0
    }
    return build_response(build_speechlet_response(speech_output, card_title),
        session_attributes)


def read_ingredient(intent, session):
    session_attributes = session.get("attributes", {})
    session_attributes["readingIngredients"] = True
    session_attributes["readingDirections"] = False
    session_attributes["directionIndex"] = 0
    card_title = session_attributes["name"] + " Ingredients"
    i = session_attributes["ingredientIndex"]
    if i <= 0:
        session_attributes["ingredientIndex"] = 0
        speech_output = "The first ingredient is {}.".format(
            session_attributes["ingredients"][0])
    elif i >= len(session_attributes["ingredients"]) - 1:
        session_attributes["ingredientIndex"] = len(
            session_attributes["ingredients"]) - 1
        speech_output = ('The last ingredient is {}. To start recipe '
            'directions, please say "read recipe."'.format(
            session_attributes["ingredients"][-1]))
    else:
        speech_output = session_attributes["ingredients"][i]
    return build_response(build_speechlet_response(speech_output, card_title),
        session_attributes)


def read_direction(intent, session):
    session_attributes = session.get("attributes", {})
    session_attributes["readingDirections"] = True
    session_attributes["readingIngredients"] = False
    session_attributes["ingredientIndex"] = 0
    card_title = session_attributes["name"] + " Directions"
    i = session_attributes["directionIndex"]
    if i <= 0:
        session_attributes["directionIndex"] = 0
        speech_output = "First, " + session_attributes["directions"][0]
    elif i >= len(session_attributes["directions"]) - 1:
        session_attributes["directionIndex"] = len(
            session_attributes["directions"]) - 1
        speech_output = "Finally, " + session_attributes["directions"][-1]
    else:
        speech_output = "Next, " + session_attributes["directions"][i]
    return build_response(build_speechlet_response(speech_output, card_title),
        session_attributes)


def go_to_home(launch_request, session):
    card_title = "Back to home"
    speech_output = "What recipe would you like to make?"
    return build_response(build_speechlet_response(speech_output, card_title))


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

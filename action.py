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

    #if "attributes" in session and session["attributes"].get("example", False):
    #     pass
    if intent_name == "FindIntent":
        return find_recipe(intent)
        
    elif ("attributes" in session) and ("recipe" in session["attributes"]):
        # we are in recipe and we will look for start ingredients list
        # or start recipe and anything that is related to those two.
        if intent_name == "HomeIntent":
            return go_to_home(intent, session)
        elif "inIngred" in session["attributes"]:
            if intent_name == "PrevIngredIntent":
                return get_prev_ingred(intent, session)
            elif intent_name == "NextIngredIntent":
                return get_next_ingred(intent, session)
            elif intent_name == "RestartIntent":
                return start_ingred(intent, session)
        elif "inInst" in session["attributes"]:
            if intent_name == "PrevInstIntent":
                return get_prev_inst(intent, session)
            elif intent_name == "NextInstIntent":
                return get_next_inst(intent, session)
            elif intent_name == "RestartIntent":
                return start_inst(intent, session)
        elif intent_name == "StartIngredIntent":
            return start_ingred(intent, session)
        elif intent_name == "StartInstIntent":
            return start_inst(intent, session)
        elif (intent_name == "AMAZON.CanelIntent") or (intent_name == "AMAZON.StopIntent"):
            return go_to_home(intent, session)
    
    elif (intent_name == "AMAZON.CancelIntent") or (intent_name == "AMAZON.StopIntent"):
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

def start_ingred(intent, session):
    card_title = "First Ingredient"
    ingred_start = 0
    ingred_end = 0
    recipe = session["attributes"]["recipe"]
    ingredients = recipe["Ingredients"]
    while ingredients[ingred_end] != "\n":
        ingred_end+= 1
    first_ingred = ingredients[ingred_start: ingred_end] # ingred_end is the \n character
    speech_output = "the first ingredient is " + first_ingred
    session_attributes = {"recipe": recipe, "ingred_start": ingred_start, "ingred_end": ingred_end, "inIngred": 0}
    return build_response(build_speechlet_response(speech_output, card_title), session_attributes)

def start_inst(intent, session):
    card_title = "First Instruction"
    inst_start = 0
    inst_end = 0
    recipe = session["attributes"]["recipe"]
    instructions = recipe["Directions"]
    while instructions[inst_end] != "\n":
        inst_end += 1
    first_inst = instructions[inst_start: inst_end]
    speech_output = first_inst
    session_attributes = {"recipe": recipe, "inst_start": inst_start, "inst_end": inst_end, "inInst": 0}
    return build_response(build_speechlet_response(speech_output, card_title), session_attributes)

def get_next_ingred(intent, session):
    ingred_start = session["attributes"]["ingred_start"]
    ingred_end = session["attributes"]["ingred_end"]
    recipe = session["attributes"]["recipe"]
    ingredients = recipe["Ingredients"]
    ingred_end = ingred_end + 1
    ingred_start = ingred_end # skip over \n character
    while ((ingred_end + 1) != len(ingredients)) and (ingredients[ingred_end] != "\n"):
        ingred_end+= 1
    next_ingred = ingredients[ingred_start: ingred_end]
    
    if (ingred_end + 1) == len(ingredients):
        card_title = "Final Ingredient"
        speech_output = "the final ingredient is " + next_ingred
        session_attributes = {"recipe": recipe}
        return build_response(build_speechlet_response(speech_output, card_title), session_attributes)
    
    card_title = "Next Ingredient"
    speech_output = next_ingred
    session_attributes = {"recipe": recipe, "ingred_start": ingred_start, "ingred_end": ingred_end, "inIngred": 0}
    return build_response(build_speechlet_response(speech_output, card_title), session_attributes)

def get_next_inst(intent, session):
    inst_start = session["attributes"]["inst_start"]
    inst_end = session["attributes"]["inst_end"]
    recipe = session["attributes"]["recipe"]
    instructions = recipe["Directions"]
    inst_end = inst_end + 1
    inst_start = inst_end
    while ((inst_end + 1) != len(instructions)) and (instructions[inst_end] != "\n"):
        inst_end += 1
    next_inst = instructions[inst_start: inst_end]
    
    if (inst_end + 1) == len(instructions):
        card_title = "Last Instruction"
        speech_output = "last, " + next_inst
        session_attributes = {"recipe": recipe}
        return build_response(build_speechlet_response(speech_output, card_title), session_attributes)
    
    card_title = "Next Instruction"
    speech_output = next_inst
    session_attributes = {"recipe": recipe, "inst_start": inst_start, "inst_end": inst_end, "inInst": 0}
    return build_response(build_speechlet_response(speech_output, card_title), session_attributes)

def get_prev_ingred(intent, session):
    card_title = "Prev Ingredient"
    ingred_start = session["attributes"]["ingred_start"]
    ingred_end = session["attributes"]["ingred_end"]
    recipe = session["attributes"]["recipe"]
    ingredients = recipe["Ingredients"]
    ingred_end = ingred_start - 1
    ingred_start = ingred_start - 2
    while ingred_start != 0 and ingredients[ingred_start] != "\n":
        ingred_start-= 1
    if ingredients[ingred_start] == "\n":
        ingred_start+= 1
    prev_ingred = ingredients[ingred_start: ingred_end]
    speech_output = prev_ingred
    session_attributes = {"recipe": recipe, "ingred_start": ingred_start, "ingred_end": ingred_end, "inIngred": 0}
    return build_response(build_speechlet_response(speech_output, card_title), session_attributes)

def get_prev_inst(intent, session):
    card_title = "Prev Instruction"
    inst_start = session["attributes"]["inst_start"]
    inst_end = session["attributes"]["inst_end"]
    recipe = session["attributes"]["recipe"]
    instructions = recipe["Directions"]
    inst_end = inst_start - 1
    inst_start-= 2
    while inst_start != 0 and instructions[inst_start] != "\n":
        inst_start -= 1
    if instructions[inst_start] == "\n":
        ingred_start += 1
    prev_inst = instructions[inst_start: inst_end]
    speech_output = prev_ints
    session_attributes = {"recipe": recipe, "inst_start": inst_start, "inst_end": inst_end, "inInst": 0}
    return build_response(build_speechlet_response(speech_output, card_title), session_attributes)

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

import json
import hashlib
import os
import sys
# Add the parent directory to the sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import guidelines

def create_uuid_from_string(string):
    hex_string = int(hashlib.sha1(string.encode("utf-8")).hexdigest(), 16) % (10 ** 10)
    return str(hex_string)


"""
Script for high fat items
All the saturated fat elements will be gathered here.
Graph Structure to be created: item --> USFDA category --> Diabetes Cateory (from MayoClinic and other places) --> Recommend/Avoid
Create ids for all these elements here. So that it will be easy to create graph

"""

DIABETES_DECISION = {'label':"Caution", 'id': create_uuid_from_string('Caution')}

DIABETES_CATEGORY = {'label': 'Medium Fat', 
                    'id':create_uuid_from_string('Medium Fat'),
                    'disease_knowledge_url': "https://www.healthline.com/health/diabetes/how-much-fat-can-a-diabetic-have-a-day#nutrition-labels",
                    'disease_knowledge_name':  "Healthline",
                    'example_items':{},
                    'description':"""This food item has medium fat and recommended with caution. Due to increased association with heart disease, high fat items are suggested to be avoided for diabetes as well. Source:https://www.healthline.com/health/diabetes/how-much-fat-can-a-diabetic-have-a-day#nutrition-labels
                    The amount of fat considered to be high, medium and low can be found at - https://www.nhs.uk/live-well/eat-well/food-types/different-fats-nutrition/"""
                    }




# Open all the files
foundational_data = json.load(open("../data/foundation_2024-04-18.json", "r"))
foundational_data = foundational_data['FoundationFoods']
sr_data = json.load(open("../data/sr_legacy_2021-10-28.json", "r"))
sr_data = sr_data['SRLegacyFoods']
survey_data = json.load(open("../data/survey_2022-10-28.json", "r"))
survey_data = survey_data['SurveyFoods']

usfda_data = foundational_data + sr_data + survey_data

final_data = {}
no_match_items = []

base_url = 'https://fdc.nal.usda.gov/fdc-app.html#/food-details/{}/nutrients'


def format_nutrition(nutrition_data):
    nutrition_dict = {}
    for item in nutrition_data:
        curr_nutrient = item['nutrient']
        name = curr_nutrient['name']
        src_id = curr_nutrient['id']
        importance = curr_nutrient['rank']
        unit = curr_nutrient['unitName']
        try:
            amount = item['amount']
            nutrition_dict[name] = {'amount':amount, 'unit': unit, 'importance_rank': importance, 'USFDA_srcID':src_id}
        except KeyError:
            pass
        
    return nutrition_dict


# If healthy carb add. If tag is none, look for keyword based match
tag_counter = 0
counter = 0
# FOUNDATIONAL DATA
for item in usfda_data:
    nutrition_data = item['foodNutrients']
    nutrition_formatted = format_nutrition(nutrition_data)
    guideline_res = guidelines.check_fat_amount(nutrition_formatted)
    if guideline_res['tag'] == 'medium fat': 
        tag_counter += 1
        # creating own id based on food item name so that if it is under two category, it will map
        name = item['description']
        try:
            category = item['foodCategory']['description']
        except:
            category = item['wweiaFoodCategory']['wweiaFoodCategoryDescription']
        item_id = create_uuid_from_string(name)
        fdc_id = item['fdcId']
        src_url = base_url.format(fdc_id)
        # TODO - There is InputFoods field if needed
        final_data[str(item_id)] = {'name': name,
                                'USFDA_category': category,
                                # same category can be present in 'recommend' and 'avoid' buckets. Append to avoid
                                'USFDA_cat_id': create_uuid_from_string(str(name + category)), 
                                'item_url': src_url,
                                'item_src':'USFDA',
                                'FDC_ID': fdc_id,
                                'nutrition': nutrition_formatted,
                                'diabetes_categories': DIABETES_CATEGORY,
                                'diabetes_decision': DIABETES_DECISION,
                                'contains': [],
                                'path_explanation':guideline_res}


print("Length of Data:", len(final_data))
print("Tag based addition:", tag_counter)
print("Keyword based addition:", counter)
json.dump(final_data, open('../result_data/medium_fats.json', 'w'))
print(("File saved"))

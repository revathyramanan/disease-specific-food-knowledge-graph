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
Aim for no more than 2,300 mg of sodium a day. Your health care provider may suggest you aim for a smaller amount if you have high blood pressure.

Src - https://www.mayoclinic.org/diseases-conditions/diabetes/in-depth/diabetes-diet/art-20044295

Another src - https://www.vichealth.vic.gov.au/news-publications/research-publications/how-much-salt-should-i-eat
"""

DIABETES_DECISION = {'label':"Recommend", 'id': create_uuid_from_string('Recommend')}


DIABETES_CATEGORY = {'label': 'Low Sodium', 
                    'id':create_uuid_from_string('Low Sodium'),
                    'disease_knowledge_url': "https://www.mayoclinic.org/diseases-conditions/diabetes/in-depth/diabetes-diet/art-20044295",
                    'disease_knowledge_name':  "MayoClinic",
                    'example_items':{},
                    'description':"""Aim for no more than 2,300 mg of sodium a day. Your health care provider may suggest you aim for a smaller amount if you have high blood pressure. Src - https://www.mayoclinic.org/diseases-conditions/diabetes/in-depth/diabetes-diet/art-20044295"""
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
    guideline_res = guidelines.check_sodium_amount(nutrition_formatted)
    if guideline_res['tag'] == 'low sodium': 
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
json.dump(final_data, open('../result_data/low_sodium.json', 'w'))
print(("File saved"))

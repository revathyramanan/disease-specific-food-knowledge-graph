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
All the Low Fibre rich elements will be gathered here.
Graph Structure to be created: item --> USFDA category --> Diabetes Cateory (from MayoClinic and other places) --> Recommend/Avoid
Create ids for all these elements here. So that it will be easy to create graph

TODO:
14g/1000kcal is recommended. All add foods that satisfy this condition
https://www.mayoclinic.org/healthy-lifestyle/nutrition-and-healthy-eating/in-depth/high-fiber-foods/art-20050948
1g fibre = 2kcal
Src - https://www.fao.org/4/y5022e/y5022e04.htm#:~:text=Energy%20values%20for%20dietary%20fibre,%2Dfermentable%20fibre%20(FAO%2C%201998
"""
#----------------------------------KNOWLEDGE-------------------------

DIABETES_DECISION = {'label':"Caution", 'id': create_uuid_from_string('Caution')}
DIABETES_CATEGORY = {'label': 'Low Fiber', 
                    'id':create_uuid_from_string('Low Fiber'),
                    'disease_knowledge_url': "https://www.mayoclinic.org/diseases-conditions/diabetes/in-depth/diabetes-diet/art-20044295",
                    'disease_knowledge_name': "MayoClinic",
                    'example_items':{},
                    'description':"""For diabetes, high fibre food items are suggested as it can manage diabetes well. A low-fiber diet is not very helpful for people with diabetes or prediabetes, as fiber can help manage diabetes and improve overall health.
                    You can have these food items with caution. Source:https://www.cdc.gov/diabetes/healthy-eating/fiber-helps-diabetes.html#:~:text=Health%20benefits%20of%20fiber&text=But%20most%20US%20adults%20only,lose%20or%20maintain%20your%20weight."""
                    }
                    


#--------------------------------------PROCESSING AND EXTRACTION SCRIPTS--------------------------------

# open all the files
foundational_data = json.load(open("../data/foundation_2024-04-18.json", "r"))
foundational_data = foundational_data['FoundationFoods']
sr_data = json.load(open("../data/sr_legacy_2021-10-28.json", "r"))
sr_data = sr_data['SRLegacyFoods']
survey_data = json.load(open("../data/survey_2022-10-28.json", "r"))
survey_data = survey_data['SurveyFoods']

usfda_data = foundational_data + sr_data + survey_data

final_data = {}
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


counter = 0

for item in usfda_data:
    nutrition_data = item['foodNutrients']
    nutrition_formatted = format_nutrition(nutrition_data)
    guideline_res = guidelines.check_fiber_amount(nutrition_formatted)

    if guideline_res['tag'] == 'low fiber':
        # creating own id based on food item name so that if it is under two category, it will map
        name = item['description']
        try:
            category = item['foodCategory']['description']
        except KeyError:
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
print("Keyword based addition:", counter)
json.dump(final_data, open('../result_data/low_fiber.json', 'w'))
print(("File saved"))

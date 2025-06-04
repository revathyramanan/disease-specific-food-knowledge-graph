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
All the heart healthy elements will be gathered here. Items with Omega-3 are heart healthy items
Graph Structure to be created: item --> USFDA category --> Diabetes Cateory (from MayoClinic and other places) --> Recommend/Avoid
Create ids for all these elements here. So that it will be easy to create graph
"""
#----------------------------------KNOWLEDGE-------------------------

# List of keywords for this category
# url tells where this keywords are obtained from to search for these items in USFDA database
fish = {'keywords':['sardines', 'sardine', 'mackerel', 'mackerels', 'tuna', 'salmon', 'oysters', 'anchovies', 'caviar'],
'url': 'https://www.mayoclinic.org/diseases-conditions/diabetes/in-depth/diabetes-diet/art-20044295'}

others = {'keywords':['flaxseed', 'flaxseeds', 'chia seeds', 'walnut', 'walnuts', 'soybeans', 'hemp seeds'],
          'url':'https://www.healthline.com/nutrition/12-omega-3-rich-foods#13-Other-foods'}

# check for all of these labels in category and names
labels = fish['keywords']

DIABETES_DECISION = {'label':"Recommend", 'id': create_uuid_from_string('Recommend')}
DIABETES_CATEGORY = {'label': 'Heart Healthy Items', 
                    'id':create_uuid_from_string('Heart Healthy Items'),
                    'disease_knowledge_url' : "https://www.mayoclinic.org/diseases-conditions/diabetes/in-depth/diabetes-diet/art-20044295",
                    'disease_knowledge_name' : "MayoClinic",
                    'example_items':{'fish': fish, 'others':others}, 
                    'description':"Omega-3 fatty acids are considered food for heart health. Source: https://ods.od.nih.gov/factsheets/Omega3FattyAcids-HealthProfessional/. As diabetes is associated with heart disease (source:https://www.cdc.gov/diabetes/diabetes-complications/diabetes-and-your-heart.html#:~:text=People%20with%20diabetes%20are%20at,your%20risk%20for%20heart%20disease.), omega-3 fatty acids are recommended my MayoClinic for diabetes. "
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




# If omega-3 is present add; If tag == "", check for keyword match
counter = 0
for item in usfda_data:
    nutrition_data = item['foodNutrients']
    nutrition_formatted = format_nutrition(nutrition_data)
    guideline_res = guidelines.omega3(nutrition_formatted)
    if guideline_res['tag'] == 'omega-3 fatty acids':
        # creating own id based on food item name so that if it is under two category, it will map
        name = item['description']
        try:
            category = item['foodCategory']['description']
        except:
            category = item['wweiaFoodCategory']['wweiaFoodCategoryDescription']
        item_id = create_uuid_from_string(name)
        fdc_id = item['fdcId']
        src_url = base_url.format(fdc_id)
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
                                'path_explanation': guideline_res}
    
    elif guideline_res['tag'] == '':
        try:
            category = item['foodCategory']['description'].lower()
        except:
            category = item['wweiaFoodCategory']['wweiaFoodCategoryDescription'].lower()
        name = item['description'].lower()
        # Get the list of labels which are present in the name and category
        match_labels = [label for label in labels if label in category] + [label for label in labels if label in name]
        if len(match_labels) > 0: # if there is a match with keywords
            counter += 1
            # creating own id based on food item name so that if it is under two category, it will map
            name = item['description']
            try:
                category = item['foodCategory']['description']
            except:
                category = item['wweiaFoodCategory']['wweiaFoodCategoryDescription']
            item_id = create_uuid_from_string(name)
            fdc_id = item['fdcId']
            src_url = base_url.format(fdc_id)
            nutrition_data = item['foodNutrients']
            nutrition_formatted = format_nutrition(nutrition_data)
            guideline_res = guidelines.omega3(nutrition_formatted)
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
                                    'path_explanation': guideline_res}
    

print("Length of Data:", len(final_data))
print("Keyword based addition:", counter)
json.dump(final_data, open('../result_data/heart_healthy.json', 'w'))
print(("File saved"))
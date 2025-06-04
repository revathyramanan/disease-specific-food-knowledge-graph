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
All the recommended animal protein elements will be gathered here.
Graph Structure to be created: item --> USFDA category --> Diabetes Cateory (from MayoClinic and other places) --> Recommend/Avoid
Create ids for all these elements here. So that it will be easy to create graph
"""
#----------------------------------KNOWLEDGE-------------------------

#TODO - eggs: https://www.healthline.com/health/diabetes/eggs
# List of keywords for this category
# url tells where this keywords are obtained from to search for these items in USFDA database

others = {'keywords': ['milk', 'yogurt', 'lactose free milk'], 'url':'https://www.niddk.nih.gov/health-information/diabetes/overview/diet-eating-physical-activity'}

# check for all of these labels in category and names
labels = others['keywords'] 



DIABETES_DECISION = {'label':"Recommend", 'id': create_uuid_from_string('Recommend')}
DIABETES_CATEGORY = {'label': 'Non Fat Low Fat', 
                    'id':create_uuid_from_string('Non Fat Low Fat'),
                    'disease_knowledge_url': "https://www.niddk.nih.gov/health-information/diabetes/overview/diet-eating-physical-activity",
                    'disease_knowledge_name': "NIDDK",
                    'example_items':{'others':others},
                    'description':""
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



# If animal protein add. If tag is none, look for keyword based match
counter = 0
# FOUNDATIONAL DATA
for item in usfda_data:
    nutrition_data = item['foodNutrients']
    nutrition_formatted = format_nutrition(nutrition_data)
    guideline_res = guidelines.check_fat_amount(nutrition_formatted)
    if guideline_res['tag'] in ['fat free', 'low fat']: 
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
# print("Keyword based addition:", counter)
json.dump(final_data, open('../result_data/non_fat_low_fat.json', 'w'))
print(("File saved"))

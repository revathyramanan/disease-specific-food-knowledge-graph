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

https://www.mayoclinichealthsystem.org/hometown-health/speaking-of-health/are-you-getting-too-much-protein#:~:text=General%20recommendations%20are%20to%20consume,30%20grams%20at%20one%20time.
https://nutritionsource.hsph.harvard.edu/what-should-you-eat/protein/
10%-35% of calories from protein
Protein % calcualtor - https://www.capitalstrength.com/omn-30-protein-rule/
"""
#----------------------------------KNOWLEDGE-------------------------

#TODO - eggs: https://www.healthline.com/health/diabetes/eggs
# List of keywords for this category
# url tells where this keywords are obtained from to search for these items in USFDA database

# they keywords from the URL are optimized for search in USFDA
nuts = {'keywords': ['nut', 'nuts', 'almond', 'cashewnut', 'walnut', 'hazelnut'],
'url': 'https://www.mayoclinic.org/diseases-conditions/diabetes/in-depth/diabetes-diet/art-20044295'}

others = {'keywords': ['peanuts', 'peanut', 'beans', 'chickpeas', 'pea', 'peas', 'split peas', 'split pea',
                       'tofu', 'lentils', 'lentil', 'legume', 'legumes','edamame', 'tempeh', 'hummus', 'soybeans',
                       'soy nuts'],
'url':'https://www.niddk.nih.gov/health-information/diabetes/overview/diet-eating-physical-activity, https://diabetes.org/food-nutrition/reading-food-labels/protein'}

labels = nuts['keywords'] + others['keywords']

DIABETES_DECISION = {'label':"Recommend", 'id': create_uuid_from_string('Recommend')}
DIABETES_CATEGORY = {'label': 'Plant Protein', 
                    'id':create_uuid_from_string('Plant Protein'),
                    'disease_knowledge_url': "https://www.niddk.nih.gov/health-information/diabetes/overview/diet-eating-physical-activity",
                    'disease_knowledge_name': "NIDDK",
                    'example_items':{'lean meat': nuts, 'others':others},
                    'description':"These food item have protein source that are from plants or with absence of cholestrol. Read more on impact of plant based protein or protein without cholestrol here - https://www.niddk.nih.gov/health-information/diabetes/overview/diet-eating-physical-activity"}
                    

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
    guideline_res = guidelines.check_protein_type_amount(nutrition_formatted)
    if guideline_res['protein_type'] == 'plant': 
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

    # if the nutrition based tag is empty, go with keywords
    elif guideline_res['protein_type'] == '':
        try:
            category = item['foodCategory']['description'].lower()
        except KeyError:
            category = item['wweiaFoodCategory']['wweiaFoodCategoryDescription'].lower()
        name = item['description'].lower()
        # Get the list of labels which are present in the name and category
        match_labels = [label for label in labels if label in category] + [label for label in labels if label in name]
        if len(match_labels) >0 :
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
            guideline_res = guidelines.check_protein_type_amount(nutrition_formatted)
            counter += 1
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
json.dump(final_data, open('../result_data/plant_protein.json', 'w'))
print(("File saved"))

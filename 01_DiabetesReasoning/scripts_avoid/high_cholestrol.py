import json
import hashlib
import saturated_fats, trans_fats
import os
import sys
# Add the parent directory to the sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import guidelines

def create_uuid_from_string(string):
    hex_string = int(hashlib.sha1(string.encode("utf-8")).hexdigest(), 16) % (10 ** 10)
    return str(hex_string)

"""
All the Cholestrol elements will be gathered here.
Graph Structure to be created: item --> USFDA category --> Diabetes Cateory (from MayoClinic and other places) --> Recommend/Avoid
Create ids for all these elements here. So that it will be easy to create graph

Most of the labels already captured in trans and saturated fat. Just reuse them

TODO: check for everything that has protein more than xg per 100g. 
Make sure they are not in avoid category. Caution category is okay

TODO: Differentiate animal protein vs plant protein using cholestrol?

https://medlineplus.gov/ency/patientinstructions/000838.htm#:~:text=All%20fats%20contain%209%20calories,found%20in%20carbohydrates%20and%20protein.
TODO: do the calcualtion
"""

#----------------------------------KNOWLEDGE-------------------------

# List of keywords for this category
# url tells where this keywords are obtained from to search for these items in USFDA database

high_fat_dairy = saturated_fats.dairy_items

high_fat_animal_protein = saturated_fats.meat_items

liver = {'keywords':['liver'],
         'url':''}

egg_yolks = {'keywords': ['egg yolk'],
             'url':''}

organ_meat = {'keywords': saturated_fats.red_meat['keywords']['offal'],
              'url':'https://www.ncbi.nlm.nih.gov/books/NBK507973/'}

labels = high_fat_dairy['keywords'] + high_fat_animal_protein['keywords'] + liver['keywords'] + egg_yolks['keywords'] + organ_meat['keywords']

DIABETES_DECISION = {'label':"Avoid", 'id': create_uuid_from_string('Avoid')}

DIABETES_CATEGORY = {'label': 'High Cholestrol', 
                    'id':create_uuid_from_string('High Cholestrol'),
                    'disease_knowledge_url': "https://www.mayoclinic.org/diseases-conditions/diabetes/in-depth/diabetes-diet/art-20044295",
                    'disease_knowledge_name':  "MayoClinic",
                    'example_items':{'high fat dairy': high_fat_dairy, 'high fat animal protein': high_fat_animal_protein,
                                     'liver': liver, 'egg yolks': egg_yolks, 'organ meat': organ_meat},
                    'description':"""It is suggested that individuals with risk factors of heart disease should not have more than 200 milligrams of cholestrol per day - https://www.ucsfhealth.org/education/cholesterol-content-of-foods"""}


explanations = {
    'high_cholestrol': """This food item has {} milligrams of cholestrol per 100 grams(~ 3.5 ounces). Individuals should not have more than 200 milligrams of cholestrol per day as per - https://www.ucsfhealth.org/education/cholesterol-content-of-foods.""",
    'low_cholestrol': """This food item has {} milligrams of cholestrol per 100 grams (~ 3.5 ounces). Allowed daily value limit of cholestrol is https://www.ucsfhealth.org/education/cholesterol-content-of-foods. If you already had food items with cholestrol that add up to 200 milligrams, its better to avoid this""",
    'keyword_match': """Even though these food items may not have cholestrol in nutrition, MayoClinic suggests to avoid these items. Source: https://www.mayoclinic.org/diseases-conditions/diabetes/in-depth/diabetes-diet/art-20044295 """
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
    guideline_res = guidelines.check_cholesterol_amount(nutrition_formatted)
    if guideline_res['tag'] == 'high cholesterol': 
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

    # if the nutrition based tag is empty, go with keywords
    elif guideline_res['tag'] == '':
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
            guideline_res = guidelines.check_cholesterol_amount(nutrition_formatted)
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
print("Tag based addition:", tag_counter)
print("Keyword based addition:", counter)
json.dump(final_data, open('../result_data/high_cholestrol.json', 'w'))
print(("File saved"))

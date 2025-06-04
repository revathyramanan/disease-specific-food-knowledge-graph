
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
All the Good-fat elements will be gathered here.
Graph Structure to be created: item --> USFDA category --> Diabetes Cateory (from MayoClinic and other places) --> Recommend/Avoid
Create ids for all these elements here. So that it will be easy to create graph

NOTE: Do the following additional check for this case
1) First Filter: Check for keywords, PUFA, MUFA
2) Second Filter: If item in Bad fat, don't add (caution or avoid)
Compute all the bad fat related items and store first. Then execute this script. There is an overlap between good fat and abd fat rules.
So items that satisfy good fat rules, if they are present in bad fat, they are avoided. This challenge occurs in "Survey Foods". Other categories are fine
"""

#--------------------------------------------------------------

# source which said these items are recommended
disease_knowledge_url = "https://www.mayoclinic.org/diseases-conditions/diabetes/in-depth/diabetes-diet/art-20044295"
disease_knowledge_name = "MayoClinic"

nuts = {'keywords': ['nut', 'nuts'],
'url': 'https://www.mayoclinic.org/diseases-conditions/diabetes/in-depth/diabetes-diet/art-20044295'}

others = {'keywords': ['olive oil', 'peanut oil', 'canola oil', 'avocado'],
'url': 'https://www.mayoclinic.org/diseases-conditions/diabetes/in-depth/diabetes-diet/art-20044295'}

# these are searched in nutrition
polyunsaturated_fat = {'keywords':['PUFA', 'Fatty acids', 'polyunsaturated'], 
'url':'https://fdc.nal.usda.gov/fdc-app.html#/food-details/173688/nutrients'}

monounsaturated_fat = {'keywords':['MUFA','Fatty acids','monounsaturated'], 
'url':'https://fdc.nal.usda.gov/fdc-app.html#/food-details/173688/nutrients'}

omega3_labels = {'keywords':['5 n-3 (DPA)', 'ALA', 'DHA'],
'url': 'https://link.springer.com/article/10.1007/s00253-017-8691-9'}

# not including omega-3 as it is part of polyunsaturated_fat. It is used for check_omega3 function
labels = nuts['keywords'] + others['keywords'] + polyunsaturated_fat['keywords'] + monounsaturated_fat['keywords']


DIABETES_DECISION = {'label':"Recommend", 'id': create_uuid_from_string('Recommend')}
DIABETES_CATEGORY = {'label': 'Good Fats', 
                    'id':create_uuid_from_string('Good Fats'),
                    'disease_knowledge_url': "https://www.mayoclinic.org/diseases-conditions/diabetes/in-depth/diabetes-diet/art-20044295",
                    'disease_knowledge_name': "MayoClinic",
                    'example_items': {'nuts': nuts, 'others':others, 'polyunsaturated fat': polyunsaturated_fat, 'monounsaturated fat':monounsaturated_fat, 'omega-3': omega3_labels},
                    'description': """Foods that contain Polyunsatured fat and Monounsaturated fat are considered as good fat. Omega-3 and Omega-6 are polyunsaturated fat. Read more about subcategories on - https://www.researchgate.net/figure/Classification-of-fatty-acids-based-on-their-carbon-chain-length-and-their-number-of_fig3_321847709 or https://nutritionsource.hsph.harvard.edu/what-should-you-eat/fats-and-cholesterol/types-of-fat/"""}
  




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


def merge_guideline_res(res1, res2):
    if res1['tag'] == '' and res2['tag'] == '':
        return {'tag':''}
    if res1['tag'] == '' and res2['tag']!= "":
        return res2
    if res1['tag'] != "" and res2['tag'] == "":
        return res1
    if res1['tag'] != "" and res2['tag'] != "":
        return {'tag':[res1['tag'], res2['tag']],
                'allowed': """{}:{} \n {}:{}""".format(res1['tag'], res1['allowed'], res2['tag'], res2['allowed']),
                'present': """{}:{} \n {}:{}""".format(res1['tag'], res1['present'], res2['tag'], res2['present']),
                'explanation': """{}:{} \n {}:{}""".format(res1['tag'], res1['explanation'], res2['tag'], res2['explanation'])}
        


# if pufa or mufa is present (low or high), tag as good fat. If tag is empty, go for keyword match
counter = 0
tag_counter = 0
tags = ['low monosaturated fatty acids', 'high monosaturated fatty acids', 'low polyunsaturated fatty acids', 'high polyunsaturated fatty acids']
for item in usfda_data:
    nutrition_data = item['foodNutrients']
    nutrition_formatted = format_nutrition(nutrition_data)
    guideline_res1 = guidelines.check_polyunsaturated_fat(nutrition_formatted)
    guideline_res2 = guidelines.check_monounsaturated_fat(nutrition_formatted)
    guideline_res = merge_guideline_res(guideline_res1, guideline_res2)
    if len(set(guideline_res['tag']).intersection(tags)) > 0:
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
        if len(match_labels) > 0 :
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
            guideline_res1 = guidelines.check_polyunsaturated_fat(nutrition_formatted)
            guideline_res2 = guidelines.check_monounsaturated_fat(nutrition_formatted)
            guideline_res = merge_guideline_res(guideline_res1, guideline_res2)
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


print("Tag based addition:", tag_counter)
print("Keyword based addition:", counter)
print("Length of Data:", len(final_data))
json.dump(final_data, open('../result_data/good_fats.json', 'w'))
print(("File saved"))


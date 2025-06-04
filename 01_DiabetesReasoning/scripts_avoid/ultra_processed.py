import json
import hashlib
import os
import sys
# Add the parent directory to the sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import guidelines
from tqdm import tqdm

def create_uuid_from_string(string):
    hex_string = int(hashlib.sha1(string.encode("utf-8")).hexdigest(), 16) % (10 ** 10)
    return str(hex_string)

items = {'keywords':['hot dogs', 'hotdog', 'fried fish sticks', 'fast food burgers', 'potato fries', 'chicken nuggets', 'fried', 'deep fried'],
         'url':'https://www.verywellhealth.com/type-2-diabetes-food-6744460'}


# check for all of these labels in category and names
labels = items['keywords'] 


DIABETES_DECISION = {'label':"Avoid", 'id': create_uuid_from_string('Avoid')}

DIABETES_CATEGORY = {'label': 'Ultraprocessed', 
                    'id':create_uuid_from_string('Unltraprocessed'),
                    'disease_knowledge_url': "https://www.verywellhealth.com/type-2-diabetes-food-6744460",
                    'disease_knowledge_name':  "Verywell Health",
                    'example_items':{'Items': items},
                    'description':"""Avoid consuming large quantities of full-fat dairy products and dairy foods that come as part of ultra-processed and fast food items. 
                    These are high in saturated fat and often sodium. Source:https://www.verywellhealth.com/type-2-diabetes-food-6744460 """
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



def merge_guideline_res(res1, res2, res3):
    if res1['tag'] == '' and res2['tag'] == '' and res3['tag'] == '': # return empty
        return {'tag':''}
    
    if res1['tag'] == '' and res2['tag'] == "" and res3['tag'] != '': # return trans
        return {'tag':[res3['tag']],
                'allowed': """{}:{}""".format(res3['tag'], res3['allowed']),
                'present': """{}:{}""".format(res3['tag'], res3['present']),
                'explanation': """Ultraprocessed foods are high in saturated fats, high in trans fats and high in sodium. {}:{} """.format(res3['tag'], res3['explanation'])}
    
    if res1['tag'] == "" and res2['tag'] != "" and res3['tag'] == '': # return empty
        return {'tag':''}
    
    if res1['tag'] == "" and res2['tag'] != "" and res3['tag'] != '': # return trans
        return {'tag':[res3['tag']],
                'allowed': """{}:{}""".format(res3['tag'], res3['allowed']),
                'present': """{}:{}""".format(res3['tag'], res3['present']),
                'explanation': """Ultraprocessed foods are high in saturated fats, high in trans fats and high in sodium. {}:{} """.format(res3['tag'], res3['explanation'])}
    
    if res1['tag'] != "" and res2['tag'] == "" and res3['tag'] == '': # return empty
        return {'tag':''}
    
    if res1['tag'] != "" and res2['tag'] == "" and res3['tag'] != '': # return empty
        return {'tag':''}
    
    if res1['tag'] != "" and res2['tag'] != "" and res3['tag'] == '': # return saturated fat and sodium
        return {'tag':[res1['tag'], res2['tag']],
                'allowed': """{}:{} \n {}:{}""".format(res1['tag'], res1['allowed'], res2['tag'], res2['allowed']),
                'present': """{}:{} \n {}:{}""".format(res1['tag'], res1['present'], res2['tag'], res2['present']),
                'explanation': """Ultraprocessed foods are high in saturated fats, high in trans fats and high in sodium. {}:{} \n {}:{}""".format(res1['tag'], res1['explanation'], res2['tag'], res2['explanation'])}
        
    if res1['tag'] != "" and res2['tag'] != "" and res3['tag'] != '': # return all
        return {'tag':[res1['tag'], res2['tag'], res3['tag']],
                'allowed': """{}:{} \n {}:{} \n {}:{}""".format(res1['tag'], res1['allowed'], res2['tag'], res2['allowed'], res3['tag'], res3['allowed']),
                'present': """{}:{} \n {}:{} \n {}:{}""".format(res1['tag'], res1['present'], res2['tag'], res2['present'], res3['tag'], res3['present']),
                'explanation': """Ultraprocessed foods are high in saturated fats, high in trans fats and high in sodium. {}:{} \n {}:{} \n {}:{}""".format(res1['tag'], res1['explanation'], res2['tag'], res2['explanation'], res3['tag'], res3['explanation'])}
        



# IFind food items with high saturated fat and high sodium, high trans fat
counter = 0
# FOUNDATIONAL DATA
for item in usfda_data:
    nutrition_data = item['foodNutrients']
    nutrition_formatted = format_nutrition(nutrition_data)
    guideline_res1 = guidelines.check_sodium_amount(nutrition_formatted)
    guideline_res2 = guidelines.check_saturated_fat_amount(nutrition_formatted)
    guideline_res3 = guidelines.check_trans_fat_amount(nutrition_formatted)
    guideline_res = merge_guideline_res(guideline_res1, guideline_res2, guideline_res3)
    if guideline_res['tag'] == ['high sodium', 'high saturated fat'] or guideline_res['tag'] == ['high sodium', 'high saturated fat', 'high trans fat'] or guideline_res['tag'] == ['high trans fat']: 
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
            # guideline_res = guidelines.check_carb_type(nutrition_formatted)
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
                                    'path_explanation': {'tag':''}}




print("Keyword based addition:", counter)
print("Length of Data:", len(final_data))
json.dump(final_data, open('../result_data/ultraprocessed.json', 'w'))
print(("File saved"))

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
All the trans fats elements will be gathered here.
Graph Structure to be created: item --> USFDA category --> Diabetes Cateory (from MayoClinic and other places) --> Recommend/Avoid
Create ids for all these elements here. So that it will be easy to create graph

"""
#----------------------------------KNOWLEDGE-------------------------

# List of keywords for this category
# url tells where this keywords are obtained from to search for these items in USFDA database

processed_snacks = {'keywords':['processed snacks'],
'url': ''}

baked_goods = {'keywords':['baked products', 'baked', 'baked goods'],
'url':'https://www.mayoclinic.org/diseases-conditions/diabetes/in-depth/diabetes-diet/art-20044295'}

shortening = {'keywords':['shortening', 'lard', 'vegetable shortening', 'margraine', 'margarines', 'butter', 'stick margraines'],
'url':'https://www.britannica.com/topic/shortening, https://www.mayoclinic.org/diseases-conditions/diabetes/in-depth/diabetes-diet/art-20044295'}

refrigerated_doughs = {'keywords': ['refrigerated doughs', 'refrigerated doughs', 'canned dough', 'canned doughs', 
                                    'canned pastry dough', 'canned pastry doughs', 'sheet dough', 'sheet doughs','cookie dough', 
                                    'cookie doughs', 'cookies dough', 'cookies doughs', 'pizza dough', 'pizza doughs', 'ready to bake'],
'url': 'https://cooklist.com/products/baking-goods/refrigerated-doughs , https://www.amazon.com/Refrigerated-Doughs/b?ie=UTF8&node=6520474011'}

other_items = {'keywords': ['cookies', 'cookie', 'candy', 'crackers', 'cracker', 'pies', 'pie', 'stick butter replacements', 
                            'pastry', 'pastries', 'nondairy coffee creamer', "popcorn, microwave", 'french fries', 'doughnut', 'beignet', 'fried'],
'url': 'https://www.mayoclinic.org/diseases-conditions/diabetes/in-depth/diabetes-diet/art-20044295 , https://www.mayoclinic.org/diseases-conditions/high-blood-cholesterol/in-depth/trans-fat/art-20046114'}



DIABETES_DECISION = {'label':"Avoid", 'id': create_uuid_from_string('Avoid')}

DIABETES_CATEGORY = {'label': 'High Trans Fat', 
                    'id':create_uuid_from_string('High Trans Fat'),
                    'disease_knowledge_url': "https://www.mayoclinic.org/diseases-conditions/diabetes/in-depth/diabetes-diet/art-20044295",
                    'disease_knowledge_name':  "MayoClinic",
                    'example_items':{'processed snacks': processed_snacks, 'baked goods': baked_goods, 'shortening': shortening, 
                    'refrigerated doughs': refrigerated_doughs, 'other items': other_items},
                    'description':"""According to World Health Organization, one can consume only 2.2g of trans-fat per day. Read more on - https://www.who.int/news-room/fact-sheets/detail/trans-fat"""             }
                    


# check for all of these labels in category and names
labels = processed_snacks['keywords'] + baked_goods['keywords'] + shortening['keywords'] + refrigerated_doughs['keywords'] + other_items['keywords']


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



# If healthy carb add. If tag is none, look for keyword based match
tag_counter = 0
counter = 0
# FOUNDATIONAL DATA
for item in usfda_data:
    nutrition_data = item['foodNutrients']
    nutrition_formatted = format_nutrition(nutrition_data)
    guideline_res = guidelines.check_trans_fat_amount(nutrition_formatted)
    if guideline_res['tag'] == 'high trans fat': 
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
            guideline_res = guidelines.check_trans_fat_amount(nutrition_formatted)
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
json.dump(final_data, open('../result_data/high_trans_fats.json', 'w'))
print(("File saved"))

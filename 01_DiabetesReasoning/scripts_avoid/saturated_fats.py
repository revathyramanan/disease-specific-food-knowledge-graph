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
Combined script for - saturated_fat_animal_protein, saturated_fat_high_fat_dairy
All the saturated fat elements will be gathered here.
Graph Structure to be created: item --> USFDA category --> Diabetes Cateory (from MayoClinic and other places) --> Recommend/Avoid
Create ids for all these elements here. So that it will be easy to create graph

"""



# Keywords for dairy
dairy_items = {'keywords':['butter', 'cheese', 'cream', 'heavy cream', 'whole milk cheese', 'whole milk yogurt', 'ice cream', 'icecream', 'whole milk'],
'url':'https://www.mayoclinic.org/healthy-lifestyle/nutrition-and-healthy-eating/in-depth/fat/art-20045550'} 
# soft_cheese = {'keywords':['camembert', 'brie', 'danish blue', 'stilton', 'mascarpone'],
# 'url':'https://www.webmd.com/diet/foods-high-in-fats', 'https://www.bhf.org.uk/informationsupport/heart-matters-magazine/nutrition/cheese/the-good-the-bad-and-the-ugly'}

# keywords for animal fat
# TODO - capture poultry with skin
meat_items = {'keywords':['beef', 'hotdog', 'hotdogs', 'hot dog', 'sausage', 'sausages', 'bacon', 'lamb', 'pork', 'fatty meat'], 
'url':'https://www.mayoclinic.org/diseases-conditions/diabetes/in-depth/diabetes-diet/art-20044295'}


red_meat = {'keywords': {
  "red_meat": ["beef", "veal", "pork", "lamb", "mutton", "horse", "goat"],
  "offal": ["scrotum", "small intestine", "heart", "brain", "kidney", "liver", "thymus", "pancreas", "testicle", "tongue", "tripe", "stomach"],
  "cured_meat": ["raw beef", "raw ham", "cooked beef", "cooked ham", "corned beef", "bacon"],
  "fresh_industrial_processed_meat": ["sausage", "kebab"],
  "precooked_ready_to_eat": ["frankfurter", "mortadella", "liver sausage", "blood sausage", "canned corned beef", "liver pâté"],
  "fermented_sausages": ["salami", "chorizo", "pepperoni", "nem"],
  "dried_meat": ["dried meat strips", "dried meat flat pieces", "beef jerky", "biltong", "tasajo"]
},'url': 'https://www.ncbi.nlm.nih.gov/books/NBK507973/'}


other_items = {'keywords':['palm oil', 'palm oils', 'coconut oil', 'coconut oils'],
'url':'https://www.verywellhealth.com/type-2-diabetes-food-6744460a'}

# LABELS
red_meat_keywords = []
for key_item in red_meat['keywords']:
    red_meat_keywords += red_meat['keywords'][key_item]
labels = meat_items['keywords'] + other_items['keywords'] + red_meat_keywords

DIABETES_DECISION = {'label':"Avoid", 'id': create_uuid_from_string('Avoid')}

DIABETES_CATEGORY = {'label': 'Saturated Fats', 
                    'id':create_uuid_from_string('Saturated Fats'),
                    'disease_knowledge_url': "https://www.mayoclinic.org/diseases-conditions/diabetes/in-depth/diabetes-diet/art-20044295",
                    'disease_knowledge_name':  "MayoClinic",
                    'example_items':{'Dairy': dairy_items, 'Meat related': meat_items, 'Others': other_items},
                    'description':"""Saturated fat appears to be associated with insulin resistance and an increased risk of type 2 diabetes 
                    (source: https://mcpress.mayoclinic.org/diabetes/three-diet-changes-to-help-lose-weight-and-better-manage-your-type-2-diabetes/#:~:text=Saturated%20fat%20appears%20to%20be,Check%20food%20labels.) 
                    All the items with saturated fat 5g per 100g portion size is considered as high saturated fat. 
                    More on National Health Service from UK - https://www.nhs.uk/live-well/eat-well/how-to-eat-a-balanced-diet/eat-less-saturated-fat/#:~:text=Look%20out%20for%20%22saturates%22%20or,and%205g%20saturates%20per%20100g."""
                    }



explanations = {
    'high_sfa': """The food item has {} grams of total saturated fats per 100 grams (~ 3.5 ounces), which considered high and not recommended as per https://www.nhs.uk/live-well/eat-well/how-to-eat-a-balanced-diet/eat-less-saturated-fat/#:~:text=Look%20out%20for%20%22saturates%22%20or,and%205g%20saturates%20per%20100g.""",
    'low_med_sfa': """The food item has {} gram(s) of total saturated fat per 100 grams (~ 3.5 ounces). Eventhough this is considered low or medium saturated fat, it is suggested to avoid or have it in moderation. Source - https://mcpress.mayoclinic.org/diabetes/three-diet-changes-to-help-lose-weight-and-better-manage-your-type-2-diabetes/#:~:text=Saturated%20fat%20appears%20to%20be,Check%20food%20labels.""",
    'keyword_match': """These food items may not have saturated fat listed in their nutrition. However, MayoClinic suggests to avoid these food items. Source:https://www.webmd.com/diet/foods-high-in-saturated-fat"""
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
    guideline_res = guidelines.check_saturated_fat_amount(nutrition_formatted)
    if guideline_res['tag'] == 'high saturated fat': 
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
            guideline_res = guidelines.check_saturated_fat_amount(nutrition_formatted)
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
json.dump(final_data, open('../result_data/saturated_fats.json', 'w'))
print(("File saved"))

import json
import os
from tqdm import tqdm
from openai import OpenAI


# Set up your API key
API_KEY = ""
client = OpenAI(api_key = API_KEY)

"""
create a dict of ingredients from USFDA. For each ingredient, create a reduced version of that ingredient using gemma2_27b
"""

def get_chatgpt_response(prompt):
    completion = client.chat.completions.create(
        model="gpt-4o",
        store=True,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    return completion.choices[0].message.content


# # TODO - use KG to get ingredients
# def get_all_ings():
#     result_filename = "../data/USFDA_Reduced_Ingredients.json"
#     curr_data = json.load(open(result_filename, 'r'))
#     new_data = {}
#     for ing_id in curr_data:
#         new_data[ing_id] = {'name': curr_data['name'], 'FDC_ID': curr_data['FDC_ID']}
#     return new_data


def reduce_ingredients():
    result_filename = "../data/USFDA_Reduced_Ingredients_Chatgpt.json"
    src_filename = "../data/USFDA_Reduced_Ingredients.json"
    data = json.load(open(src_filename, 'r'))

    counter = 0
    for ing_id in tqdm(data):
        prompt = """ Give me the main ingredient of the ingredient given below. Look at few examples below:
        Ingredient 'Cheese, pasteurized process, American, vitamin D fortified'
        Main Ingredient: 'American Cheese'
        Ingredient 'Milk, reduced fat, fluid, 2% milkfat, with added vitamin A and vitamin D'
        Main Ingredinet: '2% reduced fat milk'
        NOTE:In your response, include only the main ingredient for the ingredient given below.
        Ingredient:{}""".format(data[ing_id]['name'])
        res = get_chatgpt_response(prompt)
        data[ing_id]['main_ing'] = res
        counter +=1
        if counter %100 == 0:
            json.dump(data, open(result_filename, "w"))
    json.dump(data, open(result_filename, "w"))


def post_process():
    counter = 0
    result_filename = "../data/USFDA_Reduced_Ingredients_Chatgpt.json"
    data = json.load(open(result_filename, 'r'))
    for rid in data:
        curr_item = data[rid]
        string = curr_item['main_ing'].replace("\n", "")
        string = string.strip()
        print(string)
        data[rid]['main_ing'] = string

    json.dump(data, open(result_filename, 'w'))




# reduce_ingredients()
post_process()
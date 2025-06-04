import json
import os
from tqdm import tqdm
from langchain_community.llms import Ollama
llm = Ollama(model="gemma2:27b")


"""
create a dict of ingredients from USFDA. For each ingredient, create a reduced version of that ingredient using gemma2_27b
"""

def reduce_ingredients():
    # base_dir = 'data'
    # files = os.listdir(base_dir)

    result_filename = "../data/USFDA_Reduced_Ingredients.json"
    curr_data = json.load(open(result_filename, 'r'))

    # counter = 0
    for ing_id in tqdm(curr_data):
        main_ing = curr_data[ing_id]['main_ing']
        prompt = """ Give me the main ingredient of the ingredient given below. For example, the main ingredient is 'Cheese' in ingredient 'Cheese, pasteurized process, American, vitamin D fortified'. In your response, include only the main ingredient for the ingredient given below.
        Ingredient:{}""".format(curr_data[ing_id]['name'])
        res = llm.invoke(prompt)
        curr_data[ing_id]['main_ing'] = res
        counter +=1
        if counter %100 == 0:
            json.dump(curr_data, open("USFDA_Reduced_Ingredients.json", "w"))
    json.dump(curr_data, open("USFDA_Reduced_Ingredients.json", "w"))


def post_process():
    counter = 0
    result_filename = "../data/USFDA_Reduced_Ingredients.json"
    data = json.load(open(result_filename, 'r'))
    for rid in data:
        curr_item = data[rid]
        string = curr_item['main_ing'].replace("\n", "")
        string = string.strip()
        print(string)
        data[rid]['main_ing'] = string

    json.dump(data, open(result_filename, 'w'))

post_process()
# reduce_ingredients()
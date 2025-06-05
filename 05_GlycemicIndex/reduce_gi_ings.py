"""
Execute this before gi.py. If gi_processed.json is available in GI folder, then you can skip.
"""

import pandas as pd
from tqdm import tqdm
from openai import OpenAI
import os
import json


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


def reduce_ingredients():
    result_filename = "../GI/gi_processed.json"
    src_filename = "../GI/GI_data.csv"
    df = pd.read_csv(src_filename)
    data = []
    for i in tqdm(range(0,len(df))):
        data_dict = {'food_name': df['Food Name'][i], 'GI':str(df['GI'][i]), 'food_manufacturer':df['Food Manufacturer'][i],
                     'product_category':df['Product Category'][i], 'country':df['Country'][i],
                     'serving_size':df['Serving Size (g)'][i], 'carbs':df['Carbs per serve (g)'][i], 
                     'GL':str(df['GL'][i]), 'reference':df['Reference'][i]}
        prompt = """ Give me the main ingredient of the ingredient given below. Look at few examples below:
        Ingredient 'Apple muffin, made rolled oats and without sugar'
        Main Ingredient: 'Apple muffin'
        Ingredient 'Apricot Breakfast Bar, chewy",85,"Norganic Foods Pty Ltd, Australia'
        Main Ingredinet: 'Apricot Breakfast Bar'
        NOTE:In your response, include only the main ingredient for the ingredient given below.
        Ingredient:{}""".format(data_dict['food_name'])
        res = get_chatgpt_response(prompt)
        data_dict['reduced_ing'] = res
        data.append(data_dict)
        if len(data) %100 == 0:
            json.dump(data, open(result_filename, "w"))
    json.dump(data, open(result_filename, "w"))


def post_process():
    result_filename = "../GI/gi_processed.json"
    data = json.load(open(result_filename, 'r'))
    for rid in data:
        curr_item = data[rid]
        string = curr_item['reduced_ing'].replace("\n", "")
        string = string.strip()
        print(string)
        data[rid]['reduced_ing'] = string

    json.dump(data, open(result_filename, 'w'))




reduce_ingredients()
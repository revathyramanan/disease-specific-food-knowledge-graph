"""
This file will establish relationships between ingredients and cooking methods that produce carcinogens
This fill will create csv files which will then be loaded to neo4j
It only creates relationship files as the required nodes are already loaded via DiabetesReasoning and Cooking_Methods

Dependent on files at:
../LoadNeo4j/neo4j_source_data/DiabetesReasoning/ingredients.csv
../LoadNeo4j/neo4j_source_data/CookingMethods/cooking_methods.csv
"""

import hashlib
from dotenv import load_dotenv
import os
import json
import sys
import spacy
import csv
from tqdm import tqdm
from carcinogen_keywords import *
# Add the parent directory to the sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from python_neo4j.neo4j_connection import Neo4jConnection

DEST_DIR = '../LoadNeo4j/neo4j_source_data/CarcinogenCausal'

# Load English tokenizer
nlp = spacy.load("en_core_web_lg")
# python -m spacy download en_core_web_lg


load_dotenv('../LoadNeo4j/.env')

# Credentials to establish connect to neo4j
URI = 'bolt://localhost:7687'
USER = os.getenv("NEO4J_USER_NAME")
PASSWORD = os.getenv("NEO4J_PASSWD")
AUTH = (os.getenv("NEO4J_USER_NAME"), os.getenv("NEO4J_PASSWD"))

# Instantiate Neo4j connection
neo4j_obj = Neo4jConnection(uri=URI, 
                    user=USER,
                    pwd=PASSWORD)

# function to create unique ids
def create_uuid_from_string(string):
    hex_string = int(hashlib.sha1(string.encode("utf-8")).hexdigest(), 16) % (10 ** 10)
    return str(hex_string)

def get_ingredients():
    # Define the path to the ingredients CSV file
    filepath = "../LoadNeo4j/neo4j_source_data/DiabetesReasoning/ingredients.csv"
    
    # Initialize an empty list to hold the rows as dictionaries
    ingredients = []

    # Open the CSV file and read it
    with open(filepath, mode='r', newline='', encoding='utf-8') as file:
        csv_reader = csv.DictReader(file)  # Automatically reads the header and maps them as keys
        for row in csv_reader:
            ingredients.append(row)  # Add each row as a dictionary to the list

    return ingredients

# dict where other_names are keys and id is the value
def get_cooking_methods():
    filepath = "../LoadNeo4j/neo4j_source_data/CookingMethods/cooking_methods.csv"
    data_dict = {}

    # Open the CSV file and read it
    with open(filepath, mode='r', newline='', encoding='utf-8') as file:
        csv_reader = csv.DictReader(file)  # Automatically reads the header and maps them as keys
        for row in csv_reader:
            other_names = json.loads(row['other_names'])
            cid = row['id']
            for name in other_names:
                try: # in case same other name is present in two nodes, it handles it
                    ext_cid = data_dict[name]
                    data_dict[name] = ext_cid + [cid]
                except KeyError:
                    data_dict[name] = [cid]
    return data_dict


def tokenize(phrase):
    # Tokenize each input
    tokenized_inputs = [token.text for token in nlp(phrase)]
    return [t.lower() for t in tokenized_inputs]


def tuple_to_csv(headers, tuples_list, filepaths):
    """
    headers: column names of csv file to be generated. Type: list of strings
    tuple_list: list of tuples, where each tuple is a row
    filepath: destination filepath of the csv file to be saved
    """
    for filepath in filepaths:
        with open(filepath,'w') as out:
            csv_out=csv.writer(out)
            csv_out.writerow(headers)
            for row in tuples_list:
                csv_out.writerow(row)
        print("File saved at:", filepath)

################################# PAH ##########################

def get_pah_relationships():
    pah_ingredients = ['red meat', 'processed meat', 'fish', 'meat', "well-done meats", "beef", "pork", "muscle meat"]
    pah_cooking_actions = ["grilling", "smoking", "roasting", "frying", 
                        "barbecuing", "char grilled", "charcoal broil", "well done", 
                        "pan frying", "open flame grilling"]
    pah_temperature_max_C = 300
    pah_temperature_min_C = 150
    name = "Polycyclic Aromatic Hydrocarbons"
    # TODO - add the sources from the document
    pah_sources = "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC8199595/ , https://superfund.oregonstate.edu/resources/all-about-pahs"
    pah_add_info = "Meat over a direct flame results in fat/meat juices dripping onto the hot fire which leads to formation of PolyAromatic Hydrocarbons (PAH). Deep frying also produces PAH - https://pmc.ncbi.nlm.nih.gov/articles/PMC3756514/ "

    
    # create a node for PAH (:Carcinogen) Properties - keywords, temp, sources, additional_info
    pah_node_id = create_uuid_from_string(name)
    parameters = {'id':pah_node_id, 'name':name, 'max_temp_C': pah_temperature_max_C, 'ingredients':json.dumps(pah_ingredients),
                'cooking_methods':json.dumps(pah_cooking_actions),'sources': pah_sources, 'additional_info': pah_add_info}
    query_node = """CREATE (n:Carcinogen)
    SET n.itemID = $id, n.name = $name, n.maxTempC = $max_temp_C, n.ingredients = $ingredients, n.cookingMethods=$cooking_methods, n.sources = $sources, n.additionalInfo = $additional_info
    RETURN n"""

    res = neo4j_obj.query(query_node, parameters)
    print("Insertion of PAH node:", res)
    print("\n")

    print("Gathering all ingredient nodes...")
    ingredient_nodes = get_ingredients()
    print("Gathering all cooking method nodes...")
    cooking_method_dict = get_cooking_methods()

    # find ingredients with above mentioned keywords
    keywords = muscle_meat_keywords + processed_meat_keywords + red_meat_keywords + meat_keywords + fish_keywords + seafood_keywords
    keywords = list(set([i.lower() for i in keywords]))

    # if cooked, this happens
    rels_new = []

    # already undergone cooking method
    rels_done = []

    print("Creating PAH relationships..")
    for ing in tqdm(ingredient_nodes):
        ing_id = ing['id']
        name = ing['name']
        category = ing['USFDA_Category']
        all_tokens = tokenize(name) + tokenize(category)
        common = set(all_tokens).intersection(set(keywords))
        if len(common) >= 1: #if it is a meat or any ingredient of interest,
            # check if has already been grilled or roasted
            ca_performed = set(USFDA_CA_keywords_PAH).intersection(set(all_tokens))
            if len(ca_performed) >= 1: # if it has already undergone any of those cooking methods,
                # Ing --hasUndergone--> CookingMethod --mayProduced--> Carcinogen
                for ca in list(ca_performed):
                    method_ids = cooking_method_dict[ca.lower()]
                    for m in method_ids:
                     rels_done.append((ing_id, m, pah_node_id))

            else: # if it did not undergo any cooking method and it is a meat/fish product, add relationships
                #Ing --ifUndergoes--> CookingMethod --mayProduce--> Carcinogen
                for ca in pah_cooking_actions:
                    method_ids = cooking_method_dict[ca.lower()]
                    for m in method_ids:
                        rels_new.append((ing_id, m, pah_node_id))

    # Relationships - since all relationships are child_of, one rel file is created
    tuple_to_csv(headers=['ing_id', 'cooking_method_id', 'carcinogen_id'], tuples_list=rels_new, filepaths=[os.path.join(DEST_DIR,'rel_pah_mayProduce.csv')])
    tuple_to_csv(headers=['ing_id', 'cooking_method_id', 'carcinogen_id'], tuples_list=rels_done, filepaths=[os.path.join(DEST_DIR,'rel_pah_mayProduced.csv')])



##################################### HCA ##########################################
def get_hca_relationships():
    hca_ingredients = ["chicken", "steak", "meat", "fish", "fowl", "muscle meat", "beef", "pork", "poultry"]
    hca_cooking_actions = ["grilling", "smoking", "roasting", "frying", 
                        "barbecuing", "char grilled", "charcoal broil", "well done", 
                        "pan frying", "open flame grilling", "deep frying", "churrasco", "Brazilian barbecuing"]
    hca_temperature_max_C = 300
    hca_temperature_min_C = 100
    # TODO - add the sources from the document
    hca_sources = ["https://www.precisionnutrition.com/all-about-cooking-carcinogens", "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC2850217/"]
    hca_add_info = """HeteroCyclic Amines (HCA) form when amino acids and creatine react at high cooking temperatures and are formed in greater quantities when meats are overcooked or blackened. Cooking for a long period of time also results in such toxic components.
    To add, deep frying also introduces HCA - https://pmc.ncbi.nlm.nih.gov/articles/PMC3756514/"""

    # toasting bread or potato - overcooking starchy food - https://www.wcrf.org/about-us/news-and-blogs/burnt-toast-and-cancer-how-strong-is-the-evidence/
    
    # create a node for HCA (:Carcinogen) Properties - keywords, temp, sources, additional_info
    name = 'HeteroCyclic Amines'
    pah_node_id = create_uuid_from_string(name)
    parameters = {'id':pah_node_id, 'name':name, 'max_temp_C': hca_temperature_max_C, 'ingredients':json.dumps(hca_ingredients),
                'cooking_methods':json.dumps(hca_cooking_actions),'sources': hca_sources, 'additional_info': hca_add_info}
    query_node = """CREATE (n:Carcinogen)
    SET n.itemID = $id, n.name = $name, n.maxTempC = $max_temp_C, n.ingredients = $ingredients, n.cookingMethods=$cooking_methods, n.sources = $sources, n.additionalInfo = $additional_info
    RETURN n"""

    res = neo4j_obj.query(query_node, parameters)
    print("Insertion of HCA node:", res)
    print("\n")

    print("Gathering all ingredient nodes...")
    ingredient_nodes = get_ingredients()
    print("Gathering all cooking method nodes...")
    cooking_method_dict = get_cooking_methods()

    # find ingredients with above mentioned keywords
    keywords = muscle_meat_keywords + processed_meat_keywords + red_meat_keywords + meat_keywords + fish_keywords + seafood_keywords
    keywords = list(set([i.lower() for i in keywords]))
    
    # if cooked, this happens
    rels_new = []
    # already undergone cooking method
    rels_done = []

    print("Creating HCA relationships..")
    for ing in tqdm(ingredient_nodes):
        ing_id = ing['id']
        name = ing['name']
        category = ing['USFDA_Category']
        all_tokens = tokenize(name) + tokenize(category)
        common = set(all_tokens).intersection(set(keywords))
        if len(common) >= 1: #if it is a meat or any ingredient of interest,
            # check if has already been grilled or roasted
            ca_performed = set(USFDA_CA_keywords_HCA).intersection(set(all_tokens))
            if len(ca_performed) >= 1: # if it has already undergone any of those cooking methods,
                # Ing --hasUndergone--> CookingMethod --mayProduced--> Carcinogen
                for ca in list(ca_performed):
                    method_ids = cooking_method_dict[ca.lower()]
                    for m in method_ids:
                     rels_done.append((ing_id, m, pah_node_id))

            else: # if it did not undergo any cooking method and it is a meat/fish product, add relationships
                #Ing --ifUndergoes--> CookingMethod --mayProduce--> Carcinogen
                for ca in hca_cooking_actions:
                    method_ids = cooking_method_dict[ca.lower()]
                    for m in method_ids:
                        rels_new.append((ing_id, m, pah_node_id))

    # Relationships - since all relationships are child_of, one rel file is created
    tuple_to_csv(headers=['ing_id', 'cooking_method_id', 'carcinogen_id'], tuples_list=rels_new, filepaths=[os.path.join(DEST_DIR,'rel_hca_mayProduce.csv')])
    tuple_to_csv(headers=['ing_id', 'cooking_method_id', 'carcinogen_id'], tuples_list=rels_done, filepaths=[os.path.join(DEST_DIR,'rel_hca_mayProduced.csv')])




get_hca_relationships()
get_pah_relationships()


"""
calculate starchy food - add it to USFDA_Diabets :Contains

In carcinogen, get these starchy food - add relation as Ing + toast --> AGE
TODO: check if toasting applies to PAH and HCA
"""
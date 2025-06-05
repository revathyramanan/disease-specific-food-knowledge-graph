import json
import csv
import hashlib
import os

"""
converts the json files in result_data to csv files that neo4j can batch load
Graph Structure: ingredient --> Diabetes Cateory (from MayoClinic and other places) --> Recommend/Avoid/Caution

Labels - USFDAIngredient, DiabetesCategory, DiabetesLabel
"""
base_dir = '../result_data'
DEST_DIR = '../LoadNeo4j/neo4j_source_data/DiabetesReasoning'

def create_uuid_from_string(string):
    hex_string = int(hashlib.sha1(string.encode("utf-8")).hexdigest(), 16) % (10 ** 10)
    return str(hex_string)

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


def write_to_csv(data, filepaths):
    # writing to a csv file
    csv_data = data

    for filepath in filepaths:
        csv_data_file = open(filepath, 'w')
        # create the csv writer object
        csv_writer = csv.writer(csv_data_file)

        # Counter variable used for writing
        # headers to the CSV file
        count = 0
        for element in csv_data:
            if count == 0:
                # Writing headers of CSV file
                header = element.keys()
                csv_writer.writerow(header)
                count += 1
            # Writing data of CSV file
            csv_writer.writerow(element.values())
        csv_data_file.close()
        print("File saved at:", filepath)




files = os.listdir(base_dir)
diabetes_decision = {}
diabetes_category = {}
usfda_category = {}
ingredients = {}
contains = {}

rel_ing_diab_cat = []
rel_diab_cat_diab_des = []
rel_ing_contain = []


for f in files:
    print("Creating Nodes and Relationships for Diabetes-Specific KG from:",f)
    data = json.load(open(os.path.join(base_dir, f), 'r'))
    for item_id in data:
        curr_item = data[item_id]
        ingredients[item_id] = {'id':item_id, 'name': curr_item['name'], 'USFDA_Category': curr_item['USFDA_category'], 'nutrition':json.dumps(curr_item['nutrition']), 'src_url':curr_item['item_url'], 'fdc_id':curr_item['FDC_ID']} #serialize nutrition to load to python dict. Later create list of nutrition
        path_exp = curr_item['path_explanation']
        # TODO: add all the keys to path explanation and check using if tag == '':
        # TODO: in some cases, the tag has list of items. Think how to handle it
                          
        # diabetes category:
        curr_diab_cat = curr_item['diabetes_categories']
        diabetes_category[curr_diab_cat['id']] = curr_diab_cat

        if path_exp['tag'] == "":
            rel_ing_diab_cat.append((item_id, curr_diab_cat['id'], "NA", "NA", "NA", "NA"))
        else:
            rel_ing_diab_cat.append((item_id, curr_diab_cat['id'], path_exp['tag'], path_exp['allowed'], path_exp['present'], path_exp['explanation']))
            

        # diabetes decision
        diabetes_decision[curr_item['diabetes_decision']['id']] = curr_item['diabetes_decision']
        rel_diab_cat_diab_des.append((curr_diab_cat['id'], curr_item['diabetes_decision']['id']))

        # tags in path explanation will also be created as a separate node: contains
        if path_exp['tag'] != "":
            if isinstance(path_exp['tag'], str):
                contains_id = str(create_uuid_from_string(path_exp['tag']))
                contains[contains_id] = {'id':contains_id, 'name':path_exp['tag']}
                rel_ing_contain.append((item_id, contains_id))
            if isinstance(path_exp['tag'], list):
                for element in path_exp['tag']:
                    contains_id = str(create_uuid_from_string(element))
                    contains[contains_id] = {'id':contains_id, 'name':element}
                    rel_ing_contain.append((item_id, contains_id))
        
        

# save all the files
# Nodes
write_to_csv(data=[ingredients[i] for i in ingredients], filepaths=[os.path.join(DEST_DIR, 'ingredients.csv')])
write_to_csv(data=[contains[i] for i in contains], filepaths=[os.path.join(DEST_DIR,'contains.csv')])
# write_to_csv(data=[usfda_category[i] for i in usfda_category], filepaths=['usfda_category.csv'])
write_to_csv(data=[diabetes_category[i] for i in diabetes_category], filepaths=[os.path.join(DEST_DIR,'diabetes_category.csv')])
write_to_csv(data=[diabetes_decision[i] for i in diabetes_decision], filepaths=[os.path.join(DEST_DIR,'diabetes_decision.csv')])


# Relationships
tuple_to_csv(headers=['id1', 'id2', 'tag', 'allowed', 'present', 'explanation'], tuples_list=rel_ing_diab_cat, filepaths=[os.path.join(DEST_DIR,'rel_ing_diab_cat.csv')])
# tuple_to_csv(headers=['id1', 'id2'], tuples_list=list(set(rel_usfda_cat_diab_cat)), filepaths=['rel_usfda_cat_diab_cat.csv'])
tuple_to_csv(headers=['id1', 'id2'], tuples_list=list(set(rel_diab_cat_diab_des)), filepaths=[os.path.join(DEST_DIR,'rel_diab_cat_diab_des.csv')])
tuple_to_csv(headers=['id1', 'id2'], tuples_list=list(set(rel_ing_contain)), filepaths=[os.path.join(DEST_DIR,'rel_ing_contain.csv')])

import json
import csv
import hashlib
import os
import pandas as pd


"""
converts the cooking techniques into csv files that neo4j can batch load
Graph Structure: taxonomy

"""

DEST_DIR = '../LoadNeo4j/neo4j_source_data/CookingMethods'
src_file = 'cooking_methods.csv'
# column headers - DBpediaLink,WikidataLink,Title,Names,Type,SuperClass1,SuperClass2,Description

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

"""
As per CSV, this is the hierarchy
root --> type(class1) --> superclass1(class2) --> superclass2(class3) --> cooking methods
"""

cooking_method_nodes = []
other_nodes = []
relationships = []

df = pd.read_csv(src_file)

root = {'name': 'cooking_methods', 'id': create_uuid_from_string('cooking_methods')}



type = {}
for i in list(set(df['Type'])):
    if isinstance(i, float):
        pass
    elif "," in i:
        elements = i.split(",")
        for e in elements:
            type[e.lower().strip()] = create_uuid_from_string(e.lower().strip())
    else:
        type[i.lower().strip()] = create_uuid_from_string(i.lower().strip())


super_class1 = {}
for i in list(set(df['SuperClass1'])):
    if isinstance(i, float):
        pass
    elif "," in i:
        elements = i.split(",")
        for e in elements:
            super_class1[e.lower().strip()] = create_uuid_from_string(e.lower().strip())
    else:
        super_class1[i.lower().strip()] = create_uuid_from_string(i.lower().strip())

super_class2 = {}
for i in list(set(df['SuperClass2'])):
    if isinstance(i, float):
        pass
    elif "," in i:
        elements = i.split(",")
        for e in elements:
            super_class2[e.lower().strip()] = create_uuid_from_string(e.lower().strip())
    else:
        super_class2[i.lower().strip()] = create_uuid_from_string(i.lower().strip())


# DBpediaLink,WikidataLink,Title,Names,Type,SuperClass1,SuperClass2,Description
for i in range(0,len(df)):
    cooking_method = df['Title'][i].lower().strip()
    cooking_method_id = create_uuid_from_string(cooking_method)
    other_names = df['Names'][i]
    other_names = [oth.lower().strip() for oth in other_names.split(",")]
    desc = str(df['Description'][i]) 
    desc = desc.replace(",", "") # "," will interfere with csv format when read by neo4j
    dbpedia_url = df['DBpediaLink'][i]
    wiki_url = df['WikidataLink'][i]
    data_dict = {'id': cooking_method_id, 
                 'name': cooking_method, 
                 'other_names': json.dumps(other_names), # serialize this and later convert it back to 
                 'dbpedia_url': dbpedia_url, 
                 'wiki_url': wiki_url,
                 'description': desc}
    cooking_method_nodes.append(data_dict)

    type_ = [t.lower().strip() for t in df['Type'][i].split(",")]
    superclass1_ = [sc.lower().strip() for sc in str(df['SuperClass1'][i]).split(",")]
    superclass2_ = [sc.lower().strip() for sc in str(df['SuperClass2'][i]).split(",")]


    if superclass2_ == ['nan']:
        if superclass1_== ['nan']:
            # create edge between cooking method and type
            for t in type_:
                relationships.append((cooking_method_id, type[t]))
        else:
            for s in superclass1_:
                relationships.append((cooking_method_id, super_class1[s]))
            # add relationship between superclass1 and type
    else:
        for s2_ in superclass2_:
            relationships.append((cooking_method_id, super_class2[s2_]))
        # if superclass2 is present, superclass1 is always present
        for s2 in superclass2_:
            for s1 in superclass1_:
                relationships.append((super_class2[s2], super_class1[s1]))
        # add relationship between superclass1 and type
        for ty in type:
            for sc1 in superclass1_:
                relationships.append((super_class1[s1], type[ty]))



# gather rest of the nodes from the dict above
for key, uuid in type.items():
    other_nodes.append({'id': str(uuid), 'name':key})

for key, uuid in super_class1.items():
    other_nodes.append({'id':str(uuid), 'name':key})

for key, uuid in super_class2.items():
    other_nodes.append({'id': str(uuid), 'name':key})


# save all the files
# Nodes
write_to_csv(data=cooking_method_nodes, filepaths=[os.path.join(DEST_DIR, 'cooking_methods.csv')])
write_to_csv(data=other_nodes, filepaths=[os.path.join(DEST_DIR,'other_nodes.csv')])

# Relationships - since all relationships are child_of, one rel file is created
tuple_to_csv(headers=['id1', 'id2'], tuples_list=list(set(relationships)), filepaths=[os.path.join(DEST_DIR,'rel_cooking_methods.csv')])


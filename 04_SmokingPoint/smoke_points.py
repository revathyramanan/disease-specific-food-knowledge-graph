
import pandas as pd
import json
import torch
import csv
import h5py
import os
import hashlib
from sentence_transformers import SentenceTransformer
import torch.nn.functional as F

src_url = "https://www.chhs.colostate.edu/krnc/monthly-blog/cooking-with-fats-and-oils/"
additional_info = """Though these oils have higher smoke points, they are delicate and can become bitter when heated 
too much. They are recommended to be used as finishing oils to maintain their flavor and aroma."""

reduced_ings = json.load(open("../01_DiabetesReasoning/data/USFDA_Reduced_Ingredients_Chatgpt.json", "r"))

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model =  SentenceTransformer('all-mpnet-base-v2').to(DEVICE)

# open h5py file to load emebddings
with h5py.File('../Recommendation/ingredient_embeddings.h5', 'r') as f:
    usfda_ids = [id.decode('utf-8') for id in f['ingredient_ids'][:]]   # Convert to list of strings
    full_ing_embeddings = torch.tensor(f['name_embeddings'][:]).to(DEVICE)
    short_ing_embeddings = torch.tensor(f['reduced_name_embeddings'][:]).to(DEVICE)

# open smoke point file. Removed Hemp seed oil and Macademic nutoil from this csv file as they are not in USFDA
df = pd.read_csv("../smoke_points/smoke_points.csv")
DEST_DIR = "../load_neo4j/neo4j_source_data/Smoke_Points"

# map query ingredient to USFDA ingredients using the short name and return all ingredient list that matches
def get_usfda_ings(query_ing):
    query_embedding = model.encode(query_ing.lower(), convert_to_tensor=True).to(DEVICE).view(1, -1)  # Torch tensor

    # Compute cosine similarity using PyTorch
    cos_sim = F.cosine_similarity(
        query_embedding, short_ing_embeddings, dim=-1
    )

    # Round off to three decimal places
    cos_sim = torch.round(cos_sim * 1000) / 1000
    # Get the max value
    max_value = torch.max(cos_sim).item()
    # Get all indexes where this max value is present
    max_indices = torch.nonzero(cos_sim == max_value, as_tuple=False)
    matching_usfda_ids = []
    for idx in max_indices:
        matching_usfda_ids.append(usfda_ids[idx])

    return matching_usfda_ids

# function to create unique ids
def create_uuid_from_string(string):
    hex_string = int(hashlib.sha1(string.encode("utf-8")).hexdigest(), 16) % (10 ** 10)
    return str(hex_string)

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

nodes = []
relationships = []

smk_categories = list(set(df['Max Cooking Heat']))
for s in smk_categories:
    nodes.append({'smk_category':s, 'id':create_uuid_from_string(s)})

for i in range(0,len(df)):
    ing_name = df['Fats and Oils'][i]
    smk_category = df['Max Cooking Heat'][i]
    smk_id = create_uuid_from_string(smk_category)
    matching_usfda_ids = get_usfda_ings(ing_name)
    # print(ing_name)
    # print([reduced_ings[x] for x in matching_usfda_ids])
    # print("\n")
    for x in matching_usfda_ids:
        if df['Max Cooking Heat'][i] in ['No-Low', 'No Heat']:
            exp = additional_info
        else:
            exp = "NA"
        rels = {'id1':str(x), 
                'id2': str(smk_id), 
                'main_fat_type':df['Max Cooking Heat'][i],
                'smoke_point':df['Smoke Points'][i],
                'src_ing_name': ing_name,
                'src_url': src_url, 
                'additional_info': exp}

        relationships.append(rels)

write_to_csv(data=nodes, filepaths=[os.path.join(DEST_DIR, 'nodes.csv')])
write_to_csv(data=relationships, filepaths=[os.path.join(DEST_DIR, 'relationships.csv')])
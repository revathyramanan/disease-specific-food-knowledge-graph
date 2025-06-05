
low_min = 0
low_max = 55
med_min = 56
med_max = 69
high_min = 70
limit_url = "https://www.health.harvard.edu/healthbeat/a-good-guide-to-good-carbs-the-glycemic-index"
db_url = "https://glycemicindex.com/"
src_name = "University of Sydney Glycemic Index Research and GI News"

import json
import hashlib
import csv
import os
import torch
import h5py
from tqdm import tqdm
from sentence_transformers import SentenceTransformer
import torch.nn.functional as F

gi_data = json.load(open("../GI/gi_processed.json", "r"))
DEST_DIR = "../load_neo4j/neo4j_source_data/GI"

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model =  SentenceTransformer('all-mpnet-base-v2').to(DEVICE)

with h5py.File('../Recommendation/ingredient_embeddings.h5', 'r') as f:
    usfda_ids = [id.decode('utf-8') for id in f['ingredient_ids'][:]]   # Convert to list of strings
    full_ing_embeddings = torch.tensor(f['name_embeddings'][:]).to(DEVICE)
    short_ing_embeddings = torch.tensor(f['reduced_name_embeddings'][:]).to(DEVICE)

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

# Function to map query ingredient to USFDA ingredients using cosine similarity
def get_usfda_ings(query_ing):
    query_ing = query_ing.replace("\"", "")
    query_embedding = model.encode(query_ing.lower(), convert_to_tensor=True).to(DEVICE).view(1, -1)  # Torch tensor

    # Compute cosine similarity using PyTorch
    cos_sim = F.cosine_similarity(query_embedding, short_ing_embeddings, dim=-1)

    # Round off to three decimal places
    cos_sim = torch.round(cos_sim * 1000) / 1000

    # Find indices where cosine similarity > 0.8
    matching_indices = torch.nonzero(cos_sim > 0.75, as_tuple=False).squeeze()
    

    # Get corresponding cosine similarity values
    matching_values = cos_sim[matching_indices]

    # Ensure `matching_indices` is at least 1D, then safely convert
    matching_indices = torch.atleast_1d(matching_indices).tolist()
    matching_values = torch.atleast_1d(matching_values).tolist()

    match_usfda_ids = [usfda_ids[idx] for idx in matching_indices]

    return match_usfda_ids, matching_values  # Return usfda_ids and similarity values


GI_Cat_nodes = []
gi_rels = []
GI_ing_nodes = []
gi_usfda_rels = []


GI_Cat_nodes.append({"category": "Low", "id":create_uuid_from_string("Low GI"), 'src_url':limit_url})
GI_Cat_nodes.append({"category": "Medium", "id":create_uuid_from_string("Medium GI"), 'src_url':limit_url})
GI_Cat_nodes.append({"category": "High", "id":create_uuid_from_string("High GI"), 'src_url':limit_url})

#dict_keys(['food_name', 'GI', 'food_manufacturer', 'product_category', 'country', 'serving_size', 'carbs', 'GL', 'reference', 'reduced_ing'])
for item in tqdm(gi_data):
    gi = int(item['GI'])
    name = item['food_name']
    ing_id = create_uuid_from_string(name)
    serv_size = item['serving_size']
    if serv_size == None:
        serv_size = str("NA")
    else:
        serv_size = str(serv_size)
    
    if gi > high_min:
        gi_rels.append({'id1':ing_id,
                              'id2':create_uuid_from_string("High GI"),
                              'GL': item['GL'],
                              'GI': str(gi)})
    elif gi<med_max and gi>med_min:
        gi_rels.append({'id1':ing_id,
                              'id2':create_uuid_from_string("Medium GI"),
                              'GL': item['GL'],
                              'GI': str(gi)})
    else:
        gi_rels.append({'id1':ing_id,
                              'id2':create_uuid_from_string("Low GI"),
                              'GL': item['GL'],
                              'GI': str(gi)})
    # using json.dumps as there are many special characters in the other fields including comma which iterferes with csv formatting
    GI_ing_nodes.append({
        'id': ing_id, 
        'name': json.dumps(item['food_name']),
        'food_manufacturer': json.dumps(item.get('food_manufacturer', '')),  # Handle missing values
        'product_category': json.dumps(item.get('product_category', '')),
        'country': json.dumps(item.get('country', '')), 
        'GI': item['GI'],
        'GL': item['GL'],
        'reference': json.dumps(str(item.get('reference', ''))),  # Ensure it's a string
        'reduced_name': json.dumps(item['reduced_ing']),
        'src_url': json.dumps(db_url),
        'src': json.dumps(src_name)
    })
    
    matching_usfda_ids, sim_values = get_usfda_ings(item['reduced_ing'])

    for i, x in enumerate(matching_usfda_ids):
        gi_usfda_rels.append({'id1': x,
                              'id2':ing_id,
                              'GI': item['GI'],
                              'cos_sim':sim_values[i]})

# Save all in a file
write_to_csv(data=GI_Cat_nodes, filepaths=[os.path.join(DEST_DIR, "GI_cat_nodes.csv")])
write_to_csv(data=GI_ing_nodes, filepaths=[os.path.join(DEST_DIR, "GI_ing_nodes.csv")])
write_to_csv(data=gi_rels, filepaths=[os.path.join(DEST_DIR, "GI_rels.csv")])
write_to_csv(data=gi_usfda_rels, filepaths=[os.path.join(DEST_DIR, "GI_USFDA_rels.csv")])

# Execute this after saving the files using the code above. Following code to check the format of the csv
def clean_csv(input_file, output_file):
    with open(input_file, "r", encoding="utf-8", newline="") as infile:
        reader = csv.reader(infile, quotechar='"', skipinitialspace=True)
        rows = list(reader)  # Convert to list to check if it's reading properly

        if not rows:
            print("ERROR: No rows read from input file. Check the file format or encoding.")
            return

        print(f" Read {len(rows)} rows from {input_file}. Writing to {output_file}...")

    # Write back the cleaned data
    with open(output_file, "w", encoding="utf-8", newline="") as outfile:
        writer = csv.writer(outfile, quotechar='"', quoting=csv.QUOTE_ALL)
        writer.writerows(rows)

    print(f" Fixed CSV file saved as: {output_file}")


# clean_csv(os.path.join(DEST_DIR, "GI_ing_nodes.csv"), os.path.join(DEST_DIR, "GI_ing_nodes.csv"))
import json
import hashlib



foundational_data = json.load(open("../data/foundation_2024-04-18.json", "r"))
foundational_data = foundational_data['FoundationFoods']
sr_data = json.load(open("../data/sr_legacy_2021-10-28.json", "r"))
sr_data = sr_data['SRLegacyFoods']
survey_data = json.load(open("../data/survey_2022-10-28.json", "r"))
survey_data = survey_data['SurveyFoods']

temp = []
# 
"""
Foundational:
[{'id': 118804, 'value': 2.0, 'measureUnit': {'id': 1001, 'name': 'tablespoon', 'abbreviation': 'tbsp'}, 
'modifier': '', 'gramWeight': 33.9, 'sequenceNumber': 1, 'minYearAcquired': 2015, 'amount': 2.0}]

[{'id': 119431, 'value': 1.0, 'measureUnit': {'id': 1000, 'name': 'cup', 'abbreviation': 'cup'}, 
'modifier': 'cooked', 'gramWeight': 118.0, 'sequenceNumber': 1, 'minYearAcquired': 2015, 'amount': 1.0}]


[{'id': 119501, 'value': 1.0, 'measureUnit': {'id': 1000, 'name': 'cup', 'abbreviation': 'cup'}, 
'gramWeight': 249.0, 'sequenceNumber': 2, 'minYearAcquired': 2003, 'amount': 1.0}, 
{'id': 119500, 'value': 1.0, 'measureUnit': {'id': 1002, 'name': 'teaspoon', 'abbreviation': 'tsp'}, 
'gramWeight': 6.0, 'sequenceNumber': 1, 'minYearAcquired': 2003, 'amount': 1.0}]

-----------------------
sr_Data:
[{'id': 85670, 'measureUnit': {'id': 9999, 'name': 'undetermined', 'abbreviation': 'undetermined'}, 
'modifier': 'fruit', 'gramWeight': 11.0, 'sequenceNumber': 2}, 
{'id': 85669, 'measureUnit': {'id': 9999, 'name': 'undetermined', 'abbreviation': 'undetermined'}, 
'modifier': 'cup', 'gramWeight': 140.0, 'sequenceNumber': 1}]


[{'id': 85671, 'measureUnit': {'id': 9999, 'name': 'undetermined', 'abbreviation': 'undetermined'}, 
'modifier': 'cup sections, without membranes', 'gramWeight': 180.0, 'sequenceNumber': 1}, 
{'id': 85672, 'measureUnit': {'id': 9999, 'name': 'undetermined', 'abbreviation': 'undetermined'}, 
'modifier': 'fruit (2-5/8" dia)', 'gramWeight': 121.0, 'sequenceNumber': 2}]

---------------------
Survey data:
[{'id': 267798, 'measureUnit': {'id': 9999, 'name': 'undetermined', 'abbreviation': 'undetermined'}, 
'modifier': '30000', 'gramWeight': 30.8, 'sequenceNumber': 3, 'portionDescription': '1 fl oz'}, 
{'id': 267797, 'measureUnit': {'id': 9999, 'name': 'undetermined', 'abbreviation': 'undetermined'}, 
'modifier': '90000', 'gramWeight': 0, 'sequenceNumber': 2, 'portionDescription': 'Quantity not specified'}, 
{'id': 267796, 'measureUnit': {'id': 9999, 'name': 'undetermined', 'abbreviation': 'undetermined'}, 
'modifier': '10205', 'gramWeight': 246, 'sequenceNumber': 1, 'portionDescription': '1 cup'}]

[{'id': 280979, 'measureUnit': {'id': 9999, 'name': 'undetermined', 'abbreviation': 'undetermined'}, 
'modifier': '61467', 'gramWeight': 110, 'sequenceNumber': 1, 'portionDescription': '1 miniature'}, 
{'id': 280982, 'measureUnit': {'id': 9999, 'name': 'undetermined', 'abbreviation': 'undetermined'}, 
'modifier': '10205', 'gramWeight': 120, 'sequenceNumber': 4, 'portionDescription': '1 cup'}, 
{'id': 280983, 'measureUnit': {'id': 9999, 'name': 'undetermined', 'abbreviation': 'undetermined'}, 
'modifier': '90000', 'gramWeight': 220, 'sequenceNumber': 5, 'portionDescription': 'Quantity not specified'}, 
{'id': 280980, 'measureUnit': {'id': 9999, 'name': 'undetermined', 'abbreviation': 'undetermined'}, 
'modifier': '64772', 'gramWeight': 220, 'sequenceNumber': 2, 'portionDescription': '1 small/regular'}, 
{'id': 280981, 'measureUnit': {'id': 9999, 'name': 'undetermined', 'abbreviation': 'undetermined'}, 
'modifier': '60919', 'gramWeight': 330, 'sequenceNumber': 3, 'portionDescription': '1 large'}]


"""

def create_uuid_from_string(string):
    hex_string = int(hashlib.sha1(string.encode("utf-8")).hexdigest(), 16) % (10 ** 10)
    return str(hex_string)


data = {}
for item in foundational_data:
    name = item['description']
    uuid = create_uuid_from_string(name)
    try:
        temp = []
        food_portions = item['foodPortions']
        for each in food_portions:
            value = each['value']
            unit = each['measureUnit']['name']
            grams = each['gramWeight']
            temp.append({'value': value, 'unit': unit, 'gram_weight':grams})
        data[str(uuid)] = temp
    except KeyError:
        data[str(uuid)] = []


for item in sr_data:
    name = item['description']
    uuid = create_uuid_from_string(name)
    try:
        temp = []
        food_portions = item['foodPortions']
        for each in food_portions:
            value = 1
            unit = each['modifier']
            grams = each['gramWeight']
            temp.append({'value': value, 'unit': unit, 'gram_weight':grams})
        data[str(uuid)] = temp
    except KeyError:
        data[str(uuid)] = []


for item in survey_data:
    counter = 0
    name = item['description']
    uuid = create_uuid_from_string(name)
    try:
        temp = []
        food_portions = item['foodPortions']
        for each in food_portions:
            portion_desc = str(each['portionDescription'])
            if portion_desc != 'Quantity not specified':
                value = portion_desc.split(" ")[0]
                if "(" in portion_desc:
                    add_info = portion_desc.split("(")[-1]
                    add_info = add_info.split(")")[0]
                else:
                    add_info = "none"
                
                unit = portion_desc.replace(str(add_info), "")
                unit = unit.replace(value, "")
                unit = unit.replace("(", "")
                unit = unit.replace(")", "")

                gram_weight = each['gramWeight']

                temp.append({'value': value, 'unit':unit, 'gram_weight':gram_weight, 'add_info': add_info})
            else:
                pass
        data[str(uuid)] = temp
    except KeyError:
        data[str(uuid)] = []


print(len(data))
json.dump(data, open("../data/measure_units.json", "w"))
"""
This file consists of information from several sources to mark food items as healthy cho, fiber rich, high trans fat and etc
Expected input - Nutrition Information
"""
# import numpy as np


# def sigmoid_scaling(x, k=1, c=1.5):
#     """
#     Apply sigmoid scaling to a value x.
    
#     Parameters:
#     x (float): The input value (e.g., fat content, cholesterol level).
#     k (float): Steepness of the sigmoid (higher = sharper transition).
#     c (float): Midpoint (where the function is 0.5).

#     Returns:
#     float: Scaled value between 0 and 1.
#     """
#     return 1 / (1 + np.exp(-k * (x - c)))

# # Example usage
# values = np.array([0.5, 1, 1.5, 2, 2.5, 3])  # Example values in a range
# scaled_values = sigmoid_scaling(values, k=5, c=1.5)  # Adjust k and c as needed

# print("Original Values:", values)
# print("Sigmoid Scaled Values:", scaled_values)

def range_scaling(min, max, x):
    scaled = (x-min)/(max-min)
    return scaled


"""
High-fiber:
Calculation 1:
14g/1000kcal is recommended and considered high. All add foods that satisfy this condition
https://www.mayoclinic.org/healthy-lifestyle/nutrition-and-healthy-eating/in-depth/high-fiber-foods/art-20050948
1g fiber = 2kcal
Src for g to kcal - https://www.fao.org/4/y5022e/y5022e04.htm#:~:text=Energy%20values%20for%20dietary%20fiber,%2Dfermentable%20fiber%20(FAO%2C%201998
chart of high fiber foods - https://www.mayoclinic.org/healthy-lifestyle/nutrition-and-healthy-eating/in-depth/high-fiber-foods/art-20050948
Calculation 2:
Carb to Fibre ratio: 10:1 - good whole grain food
Why 10:1? That’s about the ratio of fiber to carbohydrate in a genuine whole grain—unprocessed wheat
https://www.health.harvard.edu/blog/the-trick-to-recognizing-a-good-whole-grain-use-carb-to-fiber-ratio-of-10-to-1-201301145794
Going with calculation 2 for consistency with refined vs health carb
"""
# fiber ID is 1079
def check_fiber_amount(nutrition_dict):
    explanation = """
    This food item has {} grams carbs to {} grams of fiber with ratio {}. If the Carb to Fibre ratio is 10:1 or more with fiber, it is considered a whole grain food with food fiber content. 
    Why 10:1? That's about the ratio of fiber to carbohydrate in a genuine whole grain—unprocessed wheat
    https://www.health.harvard.edu/blog/the-trick-to-recognizing-a-good-whole-grain-use-carb-to-fiber-ratio-of-10-to-1-201301145794
    Also as per MayoClinic, 14g per 1000kcal is considered high fiber. Link:https://www.mayoclinic.org/healthy-lifestyle/nutrition-and-healthy-eating/in-depth/high-fiber-foods/art-20050948
    """
    carbs = None
    fiber = None
    for name in nutrition_dict:
        if "Carbohydrate" in name:
            carbs = nutrition_dict[name]['amount']
        if "Fiber, total dietary" in name:
            fiber = nutrition_dict[name]['amount']
            fiber = fiber if fiber > 0 else None
    if fiber is None:
        return {'tag':'', 'allowed':'', 'present':'', 'explanation':''}
    if carbs is None:
        return {'tag':'', 'allowed':'', 'present':'', 'explanation':''}
    if carbs is not None and fiber is not None:
        # Compute Carb-to-Fiber Ratio
        observed_ratio = carbs / fiber
        threshold = 10  # Ideal threshold(10:1)

        #Compute fibre percentage a it is naturally between 0 to 100 and can be converted to 0 to 1
        # Since fibre ratio is relative to carbs in the ratio, the percentage of fibre is also the same
        fibre_percentage = (fiber/carbs)

        ratio_str = "10:"+str(round(((10*fiber)/carbs), 2))
        # For 10 grams of carbs, 1 or more grams of Fibre
        if observed_ratio <= threshold:
            return {'tag': 'high fiber', # recommend
                    'allowed': 'Carb to Fibre ratio: 10:1 is considered high-fibre',
                    'present': 'Carb to Fibre ratio in this item is {}'.format(ratio_str),
                    'risk_factor': fibre_percentage,
                    'explanation': explanation.format(carbs, fiber, ratio_str)}
        else:
            return {'tag': 'low fiber', # caution
                    'allowed': 'Carb to Fibre ratio: 10:1 is considered high-fibre',
                    'present': 'Carb to Fibre ratio in this item is {}'.format(ratio_str),
                    'risk_factor': fibre_percentage,
                    'explanation': explanation.format(carbs, fiber, ratio_str)}
    
    
"""
High Protein
Plant Protein - Does not have Cholesterol
Animal Protein - Has Cholesterol
Anything with 10% to 35% - good protein. More than 35% - high protein
https://www.mayoclinichealthsystem.org/hometown-health/speaking-of-health/are-you-getting-too-much-protein#:~:text=General%20recommendations%20are%20to%20consume,30%20grams%20at%20one%20time.
https://nutritionsource.hsph.harvard.edu/what-should-you-eat/protein/
10%-35% of calories from protein
Protein % calcualtor - https://www.capitalstrength.com/omn-30-protein-rule/
"""


def check_protein_type_amount(nutrition_dict):
    """
    return: ['type', 'protein level',  amount]
    Eg:[plant, good/excellent, 10g]
    """
    explanation = """ This food item has {} grams of protein and {} kcal calories which is {}% protein in calories. As per Mayoclinic, if food has 10-35% calories from protein,
    it is considered good protein and more than 35% is considered high protein. Source: https://www.mayoclinichealthsystem.org/hometown-health/speaking-of-health/are-you-getting-too-much-protein#:~:text=General%20recommendations%20are%20to%20consume,30%20grams%20at%20one%20time.
    """
    protein = None
    cholesterol = None
    calories = []
    for name in nutrition_dict:
        if "Energy" in name:
            calories.append(nutrition_dict[name]['amount'])
        if "Protein" in name:
            protein = nutrition_dict[name]['amount']
        if "Cholesterol" in name:
            cholesterol=nutrition_dict[name]['amount']
            cholesterol = cholesterol if cholesterol > 0 else None
    if calories == []:
        return {'tag':'', 'protein_type': ''}
    calorie = max(calories)
    if calorie == 0:
        return {'tag':'', 'protein_type': ''}
    
    if cholesterol is None:
        protein_type = "plant"
    else:
        protein_type = "animal"
    
    if protein is None:
        return {'tag':'', 'protein_type': ''}
    
    protein_percent = round((protein/calorie)*100, 2)
    if protein_percent > 10 and protein_percent < 35:
        protein_level = "medium protein"
        risk_factor = range_scaling(10, 35, protein_level)
    elif protein_percent > 35:
        protein_level = "high protein"
        risk_factor = range_scaling(35, 100, protein_level)
    else:
        protein_level = "low protein"
        risk_factor = range_scaling(0, 10, protein_level)
    
    return {'protein_type': protein_type,
     'tag': protein_level,
     'present': str(protein_percent)+"%",
     'allowed': 'Anything with 10% to 35% - good protein. More than 35% - high protein',
     'risk_factor': risk_factor,
     'explanation':explanation.format(protein, calorie, protein_percent)}



"""
Refined vs healthy carbs

Carb to Fibre ratio: 10:1 - good whole grain food
Why 10:1? That’s about the ratio of fiber to carbohydrate in a genuine whole grain—unprocessed wheat
https://www.health.harvard.edu/blog/the-trick-to-recognizing-a-good-whole-grain-use-carb-to-fiber-ratio-of-10-to-1-201301145794

10:1:2 - carb:fiber:sugar - good
dual ratio, 10:1 & 1:2 (10g carbohydrate:≥1g dietary fiber & ≤2g free sugars per 1g dietary fiber).
https://pmc.ncbi.nlm.nih.gov/articles/PMC8270120/

no fiber - https://www.cancer.org/cancer/survivorship/coping/nutrition/low-fiber-foods.html#:~:text=Keep%20in%20mind%20that%20low,and%20milk%20as%20noted%20above.

"""
# TODO: handle none cases
# If anything is none, return none
# With none values, we check if one of the two conditions hold

def check_carb_type(nutrition_dict):
    explanation = """
    This food item has {} grams of carbs with {} grams of fiber and {} grams of sugar. If a food item satisfies
    the dual ratio, it is considered healthy carbohydrate. Or, else it is considered refined carbohydrate. The dual ratio is,
    10g:1g or more for carbs:fiber and 10g:less than 2g for carbs:sugar (10g carbohydrate:≥1g dietary fiber & ≤2g free sugars per 1g dietary fiber). 
    (Source: https://pmc.ncbi.nlm.nih.gov/articles/PMC8270120/). For this food item, carbs:fiber ratio is {} and carbs:sugar ratio is {}.
    """
    carbs = None
    fiber = None
    sugars = None
    for name in nutrition_dict:
        if "Carbohydrate" in name:
            carbs = nutrition_dict[name]['amount']
        if "Fiber, total dietary" in name:
            fiber = nutrition_dict[name]['amount']
            fiber = fiber if fiber > 0 else None
        if "sugars, total" in name.lower():
            sugars = nutrition_dict[name]['amount']
            sugars = sugars if sugars > 0 else None

    # Highly unlikely case. But using for sanity check
    if carbs is None:
        return {'tag':''}

    # if there is no fiber or sugar, not enough info to make decision
    if carbs is not None and fiber is None and sugars is None:
        return {'tag':''}

    # if no fiber but has sugar, it is not a good carb
    if carbs is not None and fiber is None and sugars is not None:
        return {'tag':'unhealthy carbohydrate', #avoid
                'allowed': '10g carbohydrate:≥1g dietary fiber & ≤2g free sugars per 1g dietary fiber',
                'present': 'No fiber',
                'explanation':"Carbohydrate without fiber is considered unhealthy carbohydrate and likely that it is refined carbohydrate. Source:https://www.cancer.org/cancer/survivorship/coping/nutrition/low-fiber-foods.html#:~:text=Keep%20in%20mind%20that%20low,and%20milk%20as%20noted%20above , https://pmc.ncbi.nlm.nih.gov/articles/PMC8270120/"}


    if carbs is not None and fiber is not None and sugars is None:
        cf_ratio_str = "10:" + str(round((fiber/carbs)*10, 2))
        return {'tag':'healthy carbohydrate', #recommend
        'allowed': '10g carbohydrate:≥1g dietary fiber & ≤2g free sugars per 1g dietary fiber',
        'present': 'No Sugar; Carb:Fibre ratio is {}'.format(cf_ratio_str),
        'explanation':"Carbohydrate without sugar is considered healthy carbohydrate. Source:https://www.cancer.org/cancer/survivorship/coping/nutrition/low-fiber-foods.html#:~:text=Keep%20in%20mind%20that%20low,and%20milk%20as%20noted%20above , https://pmc.ncbi.nlm.nih.gov/articles/PMC8270120/ ."}


    if carbs is not None and fiber is not None and sugars is not None:
        cf_ratio_str = "10:" + str(round((fiber/carbs)*10, 2))
        # For 10 grams of carbs, there should be at least 1 gram of fiber
        if fiber >= (carbs / 10): 
            carbs_fiber = True
        else:
            carbs_fiber = False


        cs_ratio_str = "10:" + str(round((sugars/carbs)*10, 2))
        # For 10 grams of carbs, there should be no more than 2 grams of sugar
        if sugars <= (carbs / 5):
            carbs_sugar = True
        else:
            carbs_sugar = False

        res = [carbs_fiber, carbs_sugar]

        # both are true
        if all(res): # Recommend
            return {'tag': 'healthy carbohydrate', #recommend
                    'allowed':'10g carbohydrate:≥1g dietary fiber & ≤2g free sugars per 1g dietary fiber',
                    'present': 'Carb:Fibre is {} and Carb:Sugar is {}'.format(cf_ratio_str, cs_ratio_str),
                    'explanation':explanation.format(carbs, fiber, sugars, cf_ratio_str, cs_ratio_str)
            }
        elif carbs_fiber and not carbs_sugar: # some fruits fall here. # Caution
            return {'tag': 'mixed carbohydrate',
                    'allowed':'10g carbohydrate:≥1g dietary fiber & ≤2g free sugars per 1g dietary fiber',
                    'present':'High-fiber and high-sugar; Carb:Fibre is {} and Carb:Sugar is {}'.format(cf_ratio_str, cs_ratio_str),
                    'explanation':'A few food items such as Pears and Apples may have high-fiber and high-sugars. Users with diabetes are advised to have it with caution. Source: https://diabetes.org/food-nutrition/understanding-carbs/get-to-know-carbs#:~:text=Pulses%20(like%20lentils%20and%20peas,wheat%2C%20wheat%20bran%20and%20oats'
                    }
        
        elif not carbs_fiber and carbs_sugar: # Refined carbs # Avoid
            return {'tag': 'refined carbohydrate',
                    'allowed':'10g carbohydrate:≥1g dietary fiber & ≤2g free sugars per 1g dietary fiber',
                    'present': 'Carb:Fibre is {} and Carb:Sugar is {}'.format(cf_ratio_str, cs_ratio_str),
                    'explanation':explanation.format(carbs, fiber, sugars, cf_ratio_str, cs_ratio_str)
            }
        
        elif not carbs_fiber and not carbs_sugar: # Refined or processed # Avoid
            return {'tag': 'refined carbohydrate',
                    'allowed':'10g carbohydrate:≥1g dietary fiber & ≤2g free sugars per 1g dietary fiber',
                    'present': 'Carb:Fibre is {} and Carb:Sugar is {}'.format(cf_ratio_str, cs_ratio_str),
                    'explanation':explanation.format(carbs, fiber, sugars, cf_ratio_str, cs_ratio_str)
            }
        else:
            return {'tag':''}


"""
Trans fat
2.2 gram per day in 2000 kcal
https://www.who.int/news-room/questions-and-answers/item/nutrition-trans-fat#:~:text=International%20expert%20groups%20and%20public,for%20a%202%2C000%2Dcalorie%20diet.
1gram of fat is 9kcal
2.2 gram = 19.8kcal
That is, 0.99% from trans fat. ~1%
"""
#ID: 1257
# "Fatty acids, total trans"


def check_trans_fat_amount(nutrition_dict):
    """
    return:[level, amount, e]
    ID: 1257
    """
    explanation = """
    This food item has {} grams of trans fat with {} kcal calories that is {}% of calories. The World Health Organization (WHO) suggests that
    2.2 gram of trans fat per day in 2000 kcal calories is the allowed limit (Source:https://www.who.int/news-room/questions-and-answers/item/nutrition-trans-fat#:~:text=International%20expert%20groups%20and%20public,for%20a%202%2C000%2Dcalorie%20diet). 1 gram of fat is 9kcal. Converting, 1% of calories from trans fat is the allowed limit.
    """
    trans_fat = None
    calories = []
    for name in nutrition_dict:
        if name == 'Fatty acids, total trans':
            trans_fat = nutrition_dict[name]['amount']
        if "Energy" in name:
            calories.append(nutrition_dict[name]['amount'])
    if calories == []:
        return {'tag':''}
    calorie = max(calories)
    if calorie == 0:
        return {'tag':''}
   
    if trans_fat is None:
        return {'tag':''}
    trans_fat_percent = round(((trans_fat*9)/calorie)*100, 2)
    if  trans_fat_percent > 1:
        return {'tag':'high trans fat', # avoid
                'present': str(trans_fat_percent)+"%",
                'allowed': '1% of calories or 2.2 gram of trans fat per day in 2000 kcal calories',
                'explanation': explanation.format(trans_fat, calorie, trans_fat_percent)}
    else:
         return {'tag':'low trans fat', # caution
                'present': str(trans_fat_percent)+"%",
                'allowed': '1% of calories or 2.2 gram of trans fat per day in 2000 kcal calories',
                'explanation': explanation.format(trans_fat, calorie, trans_fat_percent)}


"""
Saturated Fat
Source 1:
10% of calories saturated fat - https://www.mayoclinic.org/healthy-lifestyle/nutrition-and-healthy-eating/expert-answers/fat-grams/faq-20058496
diabetes specific link - https://diabetes.org/food-nutrition/reading-food-labels/fats#:~:text=The%20goal%20is%20to%20get,you%2C%20talk%20to%20your%20dietitian.

Source 2:
src - https://www.nhs.uk/live-well/eat-well/how-to-eat-a-balanced-diet/eat-less-saturated-fat/#:~:text=Look%20out%20for%20%22saturates%22%20or,and%205g%20saturates%20per%20100g.
Source mentions calculations per 100g
Going based on US source - Calculation 1
Source 3:
5-6% of Saturated fat - https://www.heart.org/en/healthy-living/healthy-eating/eat-smart/fats/saturated-fats
"""


def check_saturated_fat_amount(nutrition_dict):
    """
    return:[level, amount]
    ID: 1258
    """
    explanation = """
    This food item has {} grams of saturated fats in {} kcal calories, accounting for {}% of calories. Mayoclinic suggests that
    10% of calories from saturated fat (Source: 10% of calories saturated fat - https://www.mayoclinic.org/healthy-lifestyle/nutrition-and-healthy-eating/expert-answers/fat-grams/faq-20058496
    diabetes specific link - https://diabetes.org/food-nutrition/reading-food-labels/fats#:~:text=The%20goal%20is%20to%20get,you%2C%20talk%20to%20your%20dietitian)
    """
    saturated_fat = None
    calories = []
    for name in nutrition_dict:
        if name == 'Fatty acids, total saturated':
            saturated_fat = nutrition_dict[name]['amount']
        if "Energy" in name:
            calories.append(nutrition_dict[name]['amount'])
    if calories == []:
        return {'tag':''}
    calorie = max(calories)
    if calorie == 0:
        return {'tag':''}

    if saturated_fat is None:
        return {'tag':''}
    
    saturated_fat_precentage = round(((saturated_fat*9)/calorie)*100, 2)
    if saturated_fat_precentage > 10:
        return {'tag':'high saturated fat', # avoid
                'allowed': '10% of calories from saturated fat',
                'present': str(saturated_fat_precentage) + "%",
                'explanation': explanation.format(saturated_fat, calorie, saturated_fat_precentage)}
    else:
        return {'tag':'low saturated fat', # caution
                'allowed': '10% of calories from saturated fat',
                'present': str(saturated_fat_precentage) + "%",
                'explanation': explanation.format(saturated_fat, calorie, saturated_fat_precentage)}


"""
Cholesterol (read materials in addition to existing calculation)
200 milligram per day if there is a risk of heart disease - https://www.ucsfhealth.org/education/cholesterol-content-of-foods
else, 300 milligram per day
Daily value - 2000 calories(kcal)
That is, 15mg per 100 kcal
NOTE: Cholesterol does not contribute directly to calories. To have a standard benchmark, we use daily value limit of calories.
TODO: Verify this with clinical evaluators
"""


def check_cholesterol_amount(nutrition_dict):
    """
    return: [level, amount]
    ID: 1253
    """
    explanation = """
    This food item has {} milligrams of cholesterol in {} kcal of calories, that is {} milligram per 100kcal.
    Though cholesterol does not contribute directly to calorie count in current methods, UCSF suggests no more than
    200 milligrams per day if there is a risk of heart disease - https://www.ucsfhealth.org/education/cholesterol-content-of-foods.
    CDC shows clear evidence of diabetes patients at the risk of heart disease - https://www.cdc.gov/diabetes/diabetes-complications/diabetes-and-your-heart.html#:~:text=People%20with%20diabetes%20are%20at,your%20risk%20for%20heart%20disease.
    Converting 200 milligrams per day of 2000 calories, allowed limit per 100kcal is 15 milligram of cholesterol.
    """
    cholesterol = None
    calories = []
    for name in nutrition_dict:
        if 'Cholesterol' in name:
            cholesterol = nutrition_dict[name]['amount']
            cholesterol = cholesterol if cholesterol > 0 else None
        if "Energy" in name:
            calories.append(nutrition_dict[name]['amount'])

    if calories == []:
        return {'tag':''}
    calorie = max(calories)
    if calorie == 0:
        return {'tag':''}

    if cholesterol is None:
        return {'tag':''}
    # convert given cholesterol to 100 kcal
    per_kcal = cholesterol/calorie
    cholesterol_amt = round(per_kcal * 100, 2)
    if cholesterol_amt > 15:
        return {'tag':'high cholesterol', # avoid
                'allowed':'200 milligrams per day or 15 milligrams per 100kcal',
                'present': "{} milligrams per 100kcal".format(cholesterol_amt),
                'explanation': explanation.format(cholesterol, calorie, cholesterol_amt)}
    else:
        return {'tag':'low cholesterol', # caution
                'allowed':'200 milligrams per day or 15 milligrams per 100kcal',
                'present': "{} milligrams per 100kcal".format(cholesterol_amt),
                'explanation': explanation.format(cholesterol, calorie, cholesterol_amt)}


"""
Good Fats: polyunsaturated_fat, monounsaturated_fat
Some of these good fats may have omega-3 in them
Classification - https://www.researchgate.net/figure/Classification-of-fatty-acids-based-on-their-carbon-chain-length-and-their-number-of_fig3_321847709
"""
polyunsaturated_fat_labels = {'keywords':['PUFA', 'polyunsaturated'], 
'url':'https://fdc.nal.usda.gov/fdc-app.html#/food-details/173688/nutrients'}

monounsaturated_fat_labels = {'keywords':['MUFA','monounsaturated'], 
'url':'https://fdc.nal.usda.gov/fdc-app.html#/food-details/173688/nutrients'}

omega3_labels = {'keywords':['5 n-3 (DPA)', 'ALA', 'DHA'],
'url': 'https://link.springer.com/article/10.1007/s00253-017-8691-9'}

#TODO : add explanation on total allowed fat percent. If this fat is present, return amount, add it to contains
# If anything has high concentrations, send "high". Think about condition/rule in good fats
#Fatty acids, total polyunsaturated
#ID:1293

def check_polyunsaturated_fat(nutrition_dict):
    explanation = """
    This food item has {} grams of polyunsaturated fat in {} kcal calories, accounting for {}% in calories. 1 gram fat consitutes to 9 kcal calories.
    Due to the unknown potential adverse effects of prolonged intakes of high levels of polyunsaturated fatty acids, 
    the American Heart Association (1968) the National Institutes of Health (1984b), and the National Research Council's 
    Committee on Dietary Allowances (National Research Council, 1980) have all cautioned against exceeding 10 percent 
    of total calories from polyunsaturated fatty acids. Source: https://www.ncbi.nlm.nih.gov/books/NBK218170/#:~:text=This%20committee%20accepts%2C%20for%20adults,both%20animal%20and%20plant%20fats.
    """
    pufa = None
    calories = []
    for name in nutrition_dict:
        if name == "Fatty acids, total polyunsaturated":
            pufa = nutrition_dict[name]['amount']
            pufa = pufa if pufa > 0 else None
        if "Energy" in name:
            calories.append(nutrition_dict[name]['amount'])
    if calories == []:
        return {'tag':''}
    
    if pufa is None:
        return {'tag':''}
    calorie = max(calories)
    if calorie == 0:
        return {'tag':''}
    pufa_percent = round(((pufa*9)/calorie) * 100, 2)
    if pufa_percent>10:
        return {'tag':'high polyunsaturated fatty acids', 
                'allowed':'less than 10% of total calories',
                'present': str(pufa_percent)+"%",
                'explanation': explanation.format(pufa, calorie, pufa_percent)}
    else:
        return {'tag':'low polyunsaturated fatty acids', 
                'allowed':'less than 10% of total calories',
                'present': str(pufa_percent)+"%",
                'explanation': explanation.format(pufa, calorie, pufa_percent)}

# Fatty acids, total monounsaturated
# ID: 1292

def check_monounsaturated_fat(nutrition_dict):
    explanation = """
    This food item has {} grams of monounsaturated fat with {} kcal calories, accounting for {}% of calories. 1 gram fat consitutes to 9 kcal calories.
    Dietary guidelines suggest that 15 percent of calories or less should come from monounsaturated fatty acids, which are found in both animal and plant fat.
    Source: https://www.ncbi.nlm.nih.gov/books/NBK218170/#:~:text=This%20committee%20accepts%2C%20for%20adults,both%20animal%20and%20plant%20fats.
    """
    mufa = None
    calories = []
    for name in nutrition_dict:
        if name == "Fatty acids, total monounsaturated":
            mufa = nutrition_dict[name]['amount']
            mufa = mufa if mufa > 0 else None
        if "Energy" in name:
            calories.append(nutrition_dict[name]['amount'])
    
    if calories == []:
        return {'tag':''}
    calorie = max(calories)
    if calorie == 0:
        return {'tag':''}
    if mufa is None:
        return {'tag':''}
    
    mufa_percent = round(((mufa*9)/calorie) * 100, 2)
    if mufa_percent>15:
        return {'tag':'high monosaturated fatty acids', 
                'allowed':'15 percent of calories or less',
                'present': str(mufa_percent) + "%",
                'explanation': explanation.format(mufa, calorie, mufa_percent)}
    else:
        return {'tag':'low monosaturated fatty acids', 
                'allowed':'15 percent of calories or less',
                'present': str(mufa_percent) + "%",
                'explanation': explanation.format(mufa, calorie, mufa_percent)}
  

def omega3(formatted_nutrients):
    """
    src - https://ods.od.nih.gov/factsheets/Omega3FattyAcids-HealthProfessional/
    Omega-3 fatty acids are not produced by the body and it is recommended by USFDA over other fatty acids.
    It is part of Polyunsaturated fat and hence checked separately
    """
    # keywords created by looking at nutrient labels from USFDA
    isPresent = ''# default
    for name in formatted_nutrients:
        if any(label in name for label in omega3_labels['keywords']):
            isPresent = 'omega-3 fatty acids'
    return {'tag': isPresent, 
            'allowed':'NA',
            'present':'NA',
            'explanation':"""This food item consists of Omega-3 Fatty Acids. 
            Omega-3 fatty acids are considered food for heart health. 
            Source: https://ods.od.nih.gov/factsheets/Omega3FattyAcids-HealthProfessional/. 
            As diabetes is associated with heart disease (source:https://www.cdc.gov/diabetes/diabetes-complications/diabetes-and-your-heart.html#:~:text=People%20with%20diabetes%20are%20at,your%20risk%20for%20heart%20disease.), omega-3 fatty acids are recommended my MayoClinic for diabetes."""}


"""
Sodium
https://www.mayoclinic.org/healthy-lifestyle/nutrition-and-healthy-eating/in-depth/sodium/art-20045479
https://www.mayoclinic.org/diseases-conditions/diabetes/in-depth/diabetes-diet/art-20044295
sodium - 2300mg per day
Daily Value - 2000 calories
115 milligram per 100kcal

Sodium density intake - sodium density intake (<1.1 mg/kcal = 2,300 mg at 2,100 kcal) 
Src - https://pmc.ncbi.nlm.nih.gov/articles/PMC7481988/#:~:text=Mean%20intake%20of%20sodium%20(mg,US%20consumption%20(2%2C100%20kcal).
TODO: Check with domain experts
"""


def check_sodium_amount(nutrition_dict):
    """
    return: [level, explanation]
    ID: 1093
    """
    explanation = """
    This food has {} milligrams of sodium for {} kcal calories that is {} milligram per kcal. Suggested sodium density intake is <1.1 mg/kcal = 2,300 mg at 2,100 kcal. 
    Source: https://pmc.ncbi.nlm.nih.gov/articles/PMC7481988/#:~:text=Mean%20intake%20of%20sodium%20(mg,US%20consumption%20(2%2C100%20kcal).
    """
    sodium = None
    calories = []
    for name in nutrition_dict:
        if 'Sodium' in name:
            sodium = nutrition_dict[name]['amount']
        if "Energy" in name:
            calories.append(nutrition_dict[name]['amount'])
    if calories == []:
        return {'tag':''}
    calorie = max(calories)
    if calorie == 0:
        return {'tag':''}
    if sodium is None:
        return {'tag':''}
    sodium_density = round(sodium/calorie, 2)
    if (sodium/calorie) > 1.1:
        return {'tag': "high sodium", # avoid
                'allowed': '2300mg per day or <1.1 mg/kcal = 2,300 mg at 2,100 kcal',
                'present': str(sodium_density) + " mg/kcal",
                'explanation': explanation.format(sodium, calorie, sodium_density)}
    else:
        return {'tag': "low sodium", # recommend
                'allowed': '2300mg per day or <1.1 mg/kcal = 2,300 mg at 2,100 kcal',
                'present': str(sodium_density) + " mg/kcal",
                'explanation': explanation.format(sodium, calorie, sodium_density)}
    

"""
LOW FAT NON FAT
Rule 1:
Src - https://www.nhs.uk/live-well/eat-well/food-types/different-fats-nutrition/
high fat – more than 17.5g of fat per 100g
low fat – 3g of fat or less per 100g, or 1.5g of fat per 100ml for liquids (1.8g of fat per 100ml for semi-skimmed milk)
fat-free – 0.5g of fat or less per 100g or 100ml

Rule 2:
https://www.healthline.com/nutrition/how-much-fat-to-eat#TOC_TITLE_HDR_7
"""

"Total lipid (fat)"
#ID: 1004


def check_fat_amount(nutrition_dict):
    explanation = """
    Overall fat content in this food is {} grams in 100g of food. As per NHS UK, a food item is considered
    high fat if it has more than 17.5g of fat per 100g; low fat if 3g of fat or less per 100g, or 1.5g of fat per 100ml for liquids (1.8g of fat per 100ml for semi-skimmed milk);
    fat-free if it has 0.5g of fat or less per 100g or 100ml. Source: https://www.nhs.uk/live-well/eat-well/food-types/different-fats-nutrition/
    """
    total_fat = None
    for name in nutrition_dict:
        if 'Total lipid (fat)' in name:
            total_fat = nutrition_dict[name]['amount']
    if total_fat is None:
        return {'tag': ''}
    
    if total_fat >= 17.5:
        return {'tag': 'high fat', # avoid
                'allowed': 'high: more than 17.5g; medium: 3 to 17.5g; low: less than 3g, fat-free: less than 0.5g',
                'present': str(total_fat) + "gram in 100gram of food",
                'explanation': explanation.format(total_fat)}
    if total_fat<17.5 and total_fat >= 3:
        return {'tag': 'medium fat', # caution
                'allowed': 'high: more than 17.5g; medium: 3 to 17.5g; low: less than 3g, fat-free: less than 0.5g',
                'present': str(total_fat) + "gram in 100gram of food",
                'explanation': explanation.format(total_fat)}
    if total_fat<3 and total_fat>=0.5:
        return {'tag': 'low fat', # recommend
                'allowed': 'high: more than 17.5g; medium: 3 to 17.5g; low: less than 3g, fat-free: less than 0.5g',
                'present': str(total_fat) + "gram in 100gram of food",
                'explanation': explanation.format(total_fat)}
    if total_fat<0.5:
        return {'tag': 'fat free', # recommend
                'allowed': 'high: more than 17.5g; medium: 3 to 17.5g; low: less than 3g, fat-free: less than 0.5g',
                'present': str(total_fat) + "gram in 100gram of food",
                'explanation': explanation.format(total_fat)}


"""
Added sugar - less than 10% of total calorie
link - https://www.verywellhealth.com/how-much-sugar-can-a-person-with-diabetes-have-2506616
Kcal - https://www.medicalnewstoday.com/articles/196024#:~:text=Nutritional%20value%20of%20white%20sugar,Energy%201%2C619%20kilojoules%20(387%20kilocalories)
USFDA ID for sugars = 2000
"""

def check_added_sugar(nutrition_dict):
    calories = []
    sugar = None
    for name in nutrition_dict:
        if "Energy" in name:
            calories.append(nutrition_dict[name]['amount'])
        if nutrition_dict[name]['USFDA_srcID'] == 2000:
            sugar = nutrition_dict[name]['amount']
    
    # print(calories, sugar)
    if calories == [] or sugar == None:
        return {'tag':''}
    else:
        calorie = max(calories)
        if calorie == 0:
            return {'tag':''}

        sugar_kcal = sugar * 4
        percent = round((sugar_kcal/calorie) * 100, 2)
        # print(percent)

        if percent >= 20: #less than 10% of added sugar is recommended. Since USFDA has no added sugar separately, this is ball park threshold
            return{'tag': 'high sugar',
                'allowed': 'Less than 10% of added sugar',
                'present': str(percent) +'% of calorie is from total sugars. Total sugar:' + str(sugar),
                'explanation': 'USFDA has total sugars but not added sugars. An empirical cut off of 20% is set to mark items as high added sugar'}
        else: # we cannot really say less than 40% will be less sugar. So just capture high sugar items and leave it
            return {'tag': ''}


########## OTHER LABELS
"""
SELENIUM
The safe upper limit for selenium is 400 micrograms a day in adults. Anything above that is considered an overdose.

Group
Recommended Dietary Allowance
Children 1-3	20 micrograms/day
Children 4-8	30 micrograms/day
Children 9-13	40 micrograms/day
Adults and children 14 and up	55 micrograms/day
During pregnancy	60 micrograms/day
While breastfeeding	70 micrograms/day

"""
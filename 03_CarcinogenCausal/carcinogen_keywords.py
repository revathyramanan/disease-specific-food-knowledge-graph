
# Keywords

muscle_meat_keywords = [
    # General Keywords
    "Beef", "Pork", "Lamb", "Goat", "Chicken", "Turkey", "Duck", "Veal", "Rabbit", "Game meat", "Mutton",
    
    # Specific Cuts
    "Steak", "Tenderloin", "Sirloin", "Ribeye", "Loin", "Flank", "Round", "Brisket", "Ribs", 
    "Shoulder", "Chuck", "Shank",
    
    # Processed Meats
    "Sausage", "Bacon", "Ham", "Salami", "Pastrami", "Jerky", "Corned beef", "Hot dog",
    
    # Cooking Methods
    "Roasted meat", "Grilled meat", "Barbecue", "Smoked meat", "Braised meat",
    
    # Organizational Naming Conventions
    "USDA Prime Beef", "USDA Choice", "USDA Select", "Certified Angus Beef",
    
    # By Animal
    # Beef (Cow)
    "Ground beef", "Beef brisket", "Beef ribs", "Beef stew meat",
    
    # Pork (Pig)
    "Pork chops", "Pork loin", "Pork belly", "Spare ribs",
    
    # Chicken (Poultry)
    "Chicken breast", "Chicken thighs", "Chicken drumsticks", "Chicken wings",
    
    # Lamb/Goat
    "Lamb shank", "Lamb chops", "Goat curry meat",
    
    # Game Meats
    "Venison", "Bison", "Elk", "Wild boar", "Duck breast"
]

red_meat_keywords = [
    # General Red Meats
    "Beef", "Pork", "Lamb", "Goat", "Veal", "Mutton", "Bison", "Venison", "Elk", "Wild boar",
    
    # Specific Cuts of Red Meat
    "Steak", "Tenderloin", "Sirloin", "Ribeye", "Loin", "Flank", "Round", "Brisket", "Ribs", 
    "Shoulder", "Chuck", "Shank", "Roast beef", "Beef stew meat", "Beef ribs", "Beef brisket",
    
    # Ground and Minced
    "Ground beef", "Ground lamb", "Ground pork", "Minced",
    
    # Other Variants
    "Corned beef", "Goat meat", "Lamb chops", "Lamb shank", "Liver (red meat)", "Heart (red meat)"
]


processed_meat_keywords = [
    # Processed Meat Products
    "Sausage", "Bacon", "Ham", "Salami", "Pastrami", "Hot dog", "Pepperoni", "Corned beef", "Jerky",
    
    # Cured and Smoked Meats
    "Smoked beef", "Smoked pork", "Cured ham", "Cured bacon", "Smoked sausage", "Cured sausage",
    
    # Luncheon Meats and Deli Cuts
    "Bologna", "Mortadella", "Turkey bacon", "Deli meat", "Cold cuts", "Luncheon meat",
    
    # Packaged and Pre-Cooked Meats
    "Packaged sausage", "Pre-cooked ham", "Breakfast sausage", "Chicken sausage", "Turkey sausage",
    
    # Canned and Shelf-Stable Meats
    "Canned ham", "Potted meat", "Canned chicken", "Canned beef", "Corned beef (canned)"
]


# USFDA Meat Keywords, manually curated
fish_keywords = ['fish', 'salmon', 'finfish', 'halibut', 'whale', "octopus", "herring", "halibut", "trout", "salmon", "whitefish", "smelt", "cod", "sturgeon", "pike", "anchovies"]
seafood_keywords = ["crab", "shrimp", "clam", "cockles", "seafood", "sea lion",  "ascidians", "oysters", "seal", "walrus", "squid"]
meat_keywords = [
    "meat", "liver", "tongue", "flipper", "blubber", "elk", "buffalo", "moose", "mutton", "squirrel", "bear",  "duck", "sheep", "owl",
     "deer", "venison", "pork", 'beef','chicken', 'veal','goat', 'lamb', 'bacon', 'ham', "pheasant", 'quail', 'poultry', 'fowl']


# There are some ingredients in USFDA that are already roasted or grilled and etc. Capturing those keywords here
USFDA_CA_keywords_PAH = ['roast', 'roasted', 'barbecue', 'grilled', 'grill', 'fried', 'broiled', 'smoked', '']
# The structure is: Ing --hasUndergone--> CookingMethod --produced--> Carcinogen

# There are some ingredients in USFDA that are already roasted or grilled and etc. Capturing those keywords here
USFDA_CA_keywords_HCA = ['roast', 'roasted', 'barbecue', 'grilled', 'grill', 'fried', 'broiled', 'smoked', '']
# The structure is: Ing --hasUndergone--> CookingMethod --produced--> Carcinogen


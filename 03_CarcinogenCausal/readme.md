### Carcinogen Causal Knowledge Graph
This knowledge graph gathers ingredients which when undergone certain cooking methods may produce traces of carcinogens. In this work, we focus on HeteroCyclic Amines (HCA) and PolyAromatic Hydrocarbons (PAH). The resultant graph looks as below.



#### Steps to run
* Make sure you have executed the scripts under the folder `01_DiabetesReasoning` and `02_CookingMethods`
* Ensure you have stood the neo4j up with using docker by following the steps inside `LoadNeo4j`
* Execute the file `python carcinogens.py`
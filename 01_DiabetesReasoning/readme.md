### Diabetes Reasoning Knowledge Graph
This knowledge graph is constructed by reasoning over the ingredients present in USFDA database. The ingredients are gathered from USFDA, the diabetes food groups are gathered from [MayoClinic]() and [NIDDK](). The reasons for mapping are gathered from several sources which are stored as a relationship property. An example can be found below




#### Steps to Run
NOTE: If you want to load the graph directly from the available intermediate dataformat, go to LoadNeo4j folder. If you want to go over the details of creating the diabetes reasoning KG by integrating several sources of infromation, follow the steps below.

* Navigate to `01_DiabetesReasoning` folder where 01 denotes source-01
* Create a folder named `data`. Download the USFDA datasets into the folder from [Drive Link](https://drive.google.com/drive/folders/1W50GviNYxg3Rd6PV2uMmxqVQqty9BHhy?usp=drive_link). The Branded food items are part of future work. Unzip the downloaded datasets. You can also download from USFDA but requires renaming the files
* Create a folder named `result_data`
* Execute the following commands from the terminal

```
cd scripts_avoid
for file in ./*.py; do python "$file"; done

cd scripts_caution
for file in ./*.py; do python "$file"; done

cd scripts_recommend
for file in ./*.py; do python "$file"; done

```
* An intermediatory set of json files will now be generated with reasons and stored under the `result_data` folder. This is then be further converted to csv format that allows batch loading of data into Neo4j. The details are in `Neo4jScripts` folder. If you want to load just this KG, you can move to `Neo4jScripts` folder. Else, process all the other sources of knowledge and then move to `Neo4jScripts` folder
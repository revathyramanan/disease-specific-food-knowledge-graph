
### Steps to Set up Neo4j Graph DB
1. Create the following folders inside `LoadNeo4j` folder
```
mkdir neo4j_source_data # data to be loaded to Neo4j
mkdir neo4j_graph_data # graph data created by neo4j
```

2. Download the data folder from this [Gdrive link](https://drive.google.com/drive/folders/1ocSyWqhwJT8ap01frBXLABQmuLU7V1y3?usp=sharing) and unzip it. The expected directory tree format is

```
neo4j_source_data
-- CarcinogenCausal        
-- DiabetesReasoning       
-- SmokingPoint
-- CookingMethods          
-- GlycemicIndex
```

3. Set up docker by following the steps 
* Download the most recent version of docker as per your OS from here - https://docs.docker.com/desktop/release-notes/ and install the docker on your system
* In the project folder which is a cloned version of this git repository, change the $USER and $UID in .env file. To find out the values `echo $USER` and `echo $UID` from your command terminal
* Mention the paths newly created in the docker-compose.yml file. Mention full path.
* * `<path to neo4j_source_data>:/import`
* * `<path to neo4j_graph_data>:/data`
* The required plugins are already downloaded and is under the folder `neo4j_plugins`. Mention this path in docker-compose.yml
* * `<path to neo4j_plugins>:/var/lib/neo4j/plugins`
* Create a virtual env `python -m venv <env_name>`
* Activate the virtual env `source <env_name>/bin/activate`
* Install required packages `pip install -r requirements.txt`
* Now, standup the docker inside virtual env. Command to stand up the docker container `docker compose up --build`
* Access the notebook and neo4j from ports `https://localhost:8888` and `https://localhost:7474` respectively. 
* Username and password for neo4j is in .env file
* Password for Jupyterlab is in .env file

#### Load Data
* Navigate to `https://localhost:8888` and execute the jupyter notebooks in the following order 
* * diabetes_reasoning.ipynb
* * cooking_methods.ipynb
* * smoke_points.ipynb
* * carcinogen.ipynb
* * glycemic_index.ipynb
* Now navigate to `https://localhost:7474` to explore the data loaded. You can use the sample queries below:


#### Access Neo4j from Python
* Details are in python_neo4j/sample.py



### ERRORS
* if `docker command not found` after the installation, add it to your path. For mac, ` export PATH="$PATH:/Applications/Docker.app/Contents/Resources/bin/" `. Link - https://stackoverflow.com/questions/64009138/docker-command-not-found-when-running-on-mac 

* if `OSError:No space left on deivce` while running docker compose, do `docker system prune -af`. Link - https://stackoverflow.com/questions/44664900/oserror-errno-28-no-space-left-on-device-docker-but-i-have-space 

* `git rm --cached -r <filename or foldername>` to remove large files that are part of git commit
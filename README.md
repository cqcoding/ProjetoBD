# Databases - Practical Assignment

Students:
* Anaísa Castela Rosa uc2023211854@student.uc.pt
* Cecília Ernesto Silva Quaresma uc2024245307@student.uc.pt
* Joana Correia Vilas Boas uc2023223186@student.uc.pt

This repository contains the necessary files for the practical assignment of the Databases course from the Informatics Engineering Department at Univeristy of Coimbra. The base code was already provided by the professor. 
These videos provide a demo of the working project: https://www.loom.com/share/57c2d5aa9cf64cebac39e6fd8f27e481?sid=51cafae1-bcce-411a-a02f-7fc5ffd90cb6

https://www.loom.com/share/ce3d353356674b2f96fff990451f7643

This repository also contains the script used to create the PgAdmin database, some examples of data used to populate the database, the final report and the final ER diagram.


## [Python](python) REST API

To start this demo run the script [`python demo-api.py`](demo-api.py). This will launch a local web server with the coded endpoints. You can then make requests to the endpoints through HTTP (e.g., open your web browser and access http://localhost:8080/departments). To organize the interactions with the web server it is best to use an application; for this assignment you must use [`Postman`](https://www.postman.com/downloads/). Postman supports _collections_, which allows you to group requests (such as those that you will have to develop for the practical assignment). You can also import collections (such as the examples provided).




## Requirements

To execute this project it is required to have installed:

- `python 3.X`
  - `psycopg2/3` (**conda install psycopg2-binary**)
  - `flask` (**conda install flask**)
  - `jwt` (**pip install jwt**)



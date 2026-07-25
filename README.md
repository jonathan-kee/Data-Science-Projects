# Data-Science-Projects

# Project Highlights
[First Profitable Run](./screenshots/FirstProfitableRun.png)

![First Profitable Run](./screenshots/FirstProfitableRun.png)

# Get Excel For free
Link to github repo:
https://github.com/massgravel/Microsoft-Activation-Scripts

Link to website download for Mac Os:
https://massgrave.dev/office_for_mac

# DBT Website crendentials
E4J8NLKAYRZ67GK5XWMDDKBR

# DBT Setup
Link (lastest dbt core has issue, downgrade to 1.8.0 for stable):
https://www.youtube.com/watch?v=ALuYdar1vCc&t=986s

Create schema for current docker postgres called STAGING in datagrip
- create schema staging;

Create virtual environments:
- python3 -m venv dbt-demo

Virtual environment to keep dependencies local to repo
- source dbt-demo/bin/activate

## Incase Installation went wrong
### 1. Deactivate the current environment
- deactivate

### 2. Delete the dbt-demo folder
rm -rf dbt-demo

### 3. Create a fresh virtual environment named dbt-demo
python3 -m venv dbt-demo

### 4. Activate it
source dbt-demo/bin/activate

Check if virtual environment is fresh
- pip freeze

Install dependencies
- pip install -r requirements.txt

Check dependencies
- pip freeze

Initialize dbt project
- dbt init

To check database connection is correct:
- /Users/jonathankee/.dbt/profiles.yml

Change dictory to dbtproject to run dbt commands:
- cd dbtproject

Check if connection is correct:
- dbt debug

Make dbt create table or view inside postgres:
- dbt run

Make dbt run specific model:
- dbt run --select my_first_dbt_model.sql

# DBT column lineage
Change dictory to dbtproject to run dbt commands:
- cd dbtproject

Run dbt to generate the required artifacts:
- dbt compile
- dbt docs generate

Generate lineage report:
- colibri generate

View results: Open dist/index.html in your browser

# Ingestion
## Download CSV from api /csv/prices 
- cd csv
- curl -s -X GET "https://api.fnar.net/csv/prices?include_header=true" -H "accept: text/csv" -o prices.csv
- curl -X 'GET' 'https://api.fnar.net/csv/recipeinputs?include_header=true' -H 'accept: text/csv' -o recipeInputs.csv
- copy over csv file to docker container

## Test Postgres docker connection & location
- docker exec -it postgres-container sh
- docker cp \
    ./csv/prices.csv \
    postgres-container:/tmp/prices.csv
- docker cp \
    ./csv/recipeInputs.csv \
    postgres-container:/tmp/recipeInputs.csv

## Docker Postgres Import CSV File Into PostgreSQL Table
- CREATE TABLE market_depth_raw (
    "Ticker"        VARCHAR(10) PRIMARY KEY,
    "MMBuy"         NUMERIC(15, 2),
    "MMSell"        NUMERIC(15, 2),
    
    "AI1-Average"   NUMERIC(15, 2),
    "AI1-Previous"  NUMERIC(15, 2),
    "AI1-AskAmt"    NUMERIC(15, 4),
    "AI1-AskPrice"  NUMERIC(15, 2),
    "AI1-AskAvail"  INTEGER,
    "AI1-BidAmt"    NUMERIC(15, 4),
    "AI1-BidPrice"  NUMERIC(15, 2),
    "AI1-BidAvail"  INTEGER,

    "CI1-Average"   NUMERIC(15, 2),
    "CI1-Previous"  NUMERIC(15, 2),
    "CI1-AskAmt"    NUMERIC(15, 4),
    "CI1-AskPrice"  NUMERIC(15, 2),
    "CI1-AskAvail"  INTEGER,
    "CI1-BidAmt"    NUMERIC(15, 4),
    "CI1-BidPrice"  NUMERIC(15, 2),
    "CI1-BidAvail"  INTEGER,

    "CI2-Average"   NUMERIC(15, 2),
    "CI2-Previous"  NUMERIC(15, 2),
    "CI2-AskAmt"    NUMERIC(15, 4),
    "CI2-AskPrice"  NUMERIC(15, 2),
    "CI2-AskAvail"  INTEGER,
    "CI2-BidAmt"    NUMERIC(15, 4),
    "CI2-BidPrice"  NUMERIC(15, 2),
    "CI2-BidAvail"  INTEGER,

    "NC1-Average"   NUMERIC(15, 2),
    "NC1-Previous"  NUMERIC(15, 2),
    "NC1-AskAmt"    NUMERIC(15, 4),
    "NC1-AskPrice"  NUMERIC(15, 2),
    "NC1-AskAvail"  INTEGER,
    "NC1-BidAmt"    NUMERIC(15, 4),
    "NC1-BidPrice"  NUMERIC(15, 2),
    "NC1-BidAvail"  INTEGER,

    "NC2-Average"   NUMERIC(15, 2),
    "NC21-Previous" NUMERIC(15, 2),
    "NC2-AskAmt"    NUMERIC(15, 4),
    "NC2-AskPrice"  NUMERIC(15, 2),
    "NC2-AskAvail"  INTEGER,
    "NC2-BidAmt"    NUMERIC(15, 4),
    "NC2-BidPrice"  NUMERIC(15, 2),
    "NC2-BidAvail"  INTEGER,

    "IC1-Average"   NUMERIC(15, 2),
    "IC1-Previous"  NUMERIC(15, 2),
    "IC1-AskAmt"    NUMERIC(15, 4),
    "IC1-AskPrice"  NUMERIC(15, 2),
    "IC1-AskAvail"  INTEGER,
    "IC1-BidAmt"    NUMERIC(15, 4),
    "IC1-BidPrice"  NUMERIC(15, 2),
    "IC1-BidAvail"  INTEGER
);

- COPY market_depth_raw
FROM '/tmp/prices.csv'
WITH (FORMAT csv, HEADER true, NULL '');

- CREATE TABLE recipe_inputs_raw (
    "Key"       VARCHAR(100) NOT NULL,
    "Material"  VARCHAR(20),
    "Amount"    INTEGER NOT NULL
);

- COPY recipe_inputs_raw
FROM '/tmp/recipeInputs.csv'
WITH (FORMAT csv, HEADER true, NULL '');

# Resources to learn DBT:
https://learn.getdbt.com/learn/course/dbt-fundamentals/models-60min/building-your-first-model?page=3

Default materialization is a view in dbt

The below will overide the default materialization, using table instead of view
{{ config(materialized='table') }}

dbt_project.yml will contain global configuration for materialization:
models:
  dbtproject:
    # Config indicated by + and applies to all files under models/example/
    example:
      +materialized: view

example for the above is reffering to models/example folder

Gemini Explanation on Staging:

In Medallion Architecture (Bronze $\rightarrow$ Silver $\rightarrow$ Gold), **Bronze** represents raw data, whereas dbt's **Staging** layer is the *first light transformation* step immediately on top of Bronze.

Here is how the concepts map directly to each other:

| Layer Concept | Medallion Architecture | dbt Layer | What Lives There |
| --- | --- | --- | --- |
| **Raw Ingestion** | **Bronze** | Raw Warehouse / `source()` | Exact copy of source data (JSON, messy schemas, uncast types, duplicates). |
| **Cleaned & Standardized** | **Silver** | **Staging (`stg_`)** & Intermediate | Renamed columns, cast types, light filtering, deduplication, and initial business logic. |
| **Business / Analytics** | **Gold** | **Marts (`fct_`, `dim_`)** | Aggregated data, dimensional models, and star schemas built for BI tools. |

---

### The Fine Print: Bronze vs. Staging

If you want to be precise:

* **Raw Data = Bronze:** The untouched landing table inside your Snowflake, BigQuery, or Databricks instance.
* **dbt Staging = Light Silver (or Bronze+):** The SQL view that reads from Bronze (`{{ source(...) }}`), renames `usr_id` to `user_id`, casts strings to timestamps, and standardizes types.

Because dbt doesn't handle the ingestion step itself (tools like Fivetran, Airbyte, or custom Python pipelines dump data into Bronze), **Staging is dbt’s entry point for Bronze data.**

So while your raw warehouse tables are technically the true Bronze layer, your dbt **Staging models act as the bridge between Bronze and Silver.**

*** DBT does not handle ingestion ***

https://learn.getdbt.com/learn/course/dbt-fundamentals/models-60min/building-your-first-model?page=6

Build customers upstreams objects (build the dependencies table / view first)
dbt run --select +customers

Build customers upstreams & downstreams objects (build the dependencies table / view first)
dbt run --select +customers+

https://learn.getdbt.com/learn/course/dbt-fundamentals/models-60min/building-your-first-model?page=8

Model Naming Conventions
- Source
Tables of raw data that were loaded into your data warehouse

- Staging
Make the data look like what you wished it looked like. This involves things like
renaming columns, casting data types, or currency conversions

- Intermediate
Joins and aggregations will occur. These should not depend directly on sources.
Instead they should depend on the staging models

- Fact
Real-world processes that have occured or are occuring. Usually an immutable event
stream: sessions, transactions, orders, stories, votes

- Dimensions
Each row is a person, place, or thing; Mutable, through slowly changing: customers,
products, candidates, buildings, employees

# Data Engineering With DBT
## Chapter 1
When working with dbt, you will not need to write create table or create view
statements, as dbt will create them for us. It is nevertheless good to get familiar with these
basic SQL commands as these are the commands executed in the database and you will see
them if you look in the logs.

To create the TEST database and the SOME_DATA schema in it, we can use the following commands:
CREATE DATABASE TEST;
CREATE SCHEMA TEST.SOME_DATA;

### Users and roles
The following is an example of a simple setup with one role and a couple of users:
CREATE ROLE DBT_SAMPLE_ROLE;
CREATE USER MY_NAME; -- Personal user
CREATE USER SAMPLE_SERVICE; -- Service user
GRANT ROLE DBT_SAMPLE_ROLE TO USER MY_NAME;
GRANT ROLE DBT_SAMPLE_ROLE TO USER SAMPLE_SERVICE;

A more complex setup could have one role to read and one to write for each source system (represented
by a schema with the data from the system), for the data warehouse (one or more schemata where the
data is processed), and for each data mart (one schema for each data mart).

You could then control in much more detail who can read and write what, at the cost of more effort.

The below syntax is available for postgres:
SELECT * FROM ( VALUES
('IT', 'ITA', 'Italy')
,('US', 'USA', 'United States of America')
,('SF', 'FIN', 'Finland (Suomi)')
);

### Query clause order of evaluation
1) FROM and its JOIN subclause, which are used to identify the source data for the query.
2) The WHERE clause, which is used to filter out the source data that we do not want.
This is probably the most important clause for performance, because the less data a query
works on, the quicker it is. Use WHERE whenever possible to just bring in the data you need.
3) The GROUP BY clause, which groups the source data left after applying the WHERE clause and
calculates the aggregate functions on the grouped data.
4) The HAVING clause, which filters on the results of GROUP BY.
5) Partitioning of the windows and calculation of the window functions.
6) The QUALIFY clause, which filters on the results of the window functions.
7) The DISTINCT keyword, if applied to the SELECT clause, which removes duplicated rows.
8) The ORDER BY clause, which puts the resulting rows in the desired order.
9) The LIMIT clause, which caps the rows returned by the query to the desired amount.

## Chapter 2
### Comparing dbt Core and dbt Cloud workflows
There are two dbt versions that you can decide to use:
- dbt Core: This is open source software created by dbt Labs, developed in Python, that you can
freely download and use locally from the command line on many operating systems, such as
Windows, Mac, and Linux. It provides all the core functionalities of dbt and can also be used
for commercial projects.

- dbt Cloud: This is a commercial software created by dbt Labs that offers a Software-as-a-Service
(SaaS) experience that includes all the functionalities from dbt Core wrapped in a web interface
that makes it easier to use the dbt Core functionalities, adding many features that are useful
when running a real-life data project.

### dbt Core workflows (Long read)

### Exploring the dbt default model
#### Analysis of my_first_dbt_model
Probably the most interesting row is line 1, as it is not SQL code, but an inline configuration that
directs dbt to materialize the result of this query as a table. If you preview the model, you will see the
result of its SQL, in the dbt Cloud IDE, but you will generate nothing on your DB. To affect your DB,
you need to run your model using the dbt run or dbt build command.

Important note
Doing a preview of a model will run the query in the model as it is, while when running a
model, using the dbt run command will wrap the SELECT query with the correct DDL to
materialize the model in the DB in the desired way, such as a table or a view.

#### Analysis of my_first_dbt_model
If you try to preview this model before you have used the dbt run command, you will get an error,
as the first model that you reference does not exist on your DB. Most probably, the schema with your
selected schema name will not exist either.

We will use the dbt run command in the next section, so for the moment, we can just note that
this model just selects everything from your first model that is referenced simply by its name using
the dbt ref function.

The curly brackets symbols, { and }, are used to start and end the blocks of Jinja code in our models.
We will look at Jinja in more detail in the second part of the book. For the moment, note that double
curly brackets symbols, {{, are used to print out values from Jinja expressions.

We then expect that the {{ ref('my_first_dbt_model') SQL name to reference the table or view containing the first model.

#### Analysis of schema.yml

### Using ref and source to connect models
The ref and source functions are the keystones of how dbt works; by using them, we provide dbt
with the information needed to build the graph of dependencies of the whole project, and dbt is then
able to generate the SQL code dynamically, making it simple to write a model once and deploy it to
multiple environments.

### Further Reading
https://docs.getdbt.com/docs/introduction?version=2.0&name=v2
https://docs.getdbt.com/reference/dbt_project.yml?version=2.0&name=v2
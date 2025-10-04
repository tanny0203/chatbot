from sqlcoder_chain import NL2SQLGenerator
from nl2sql.sqlcoder_chain import NL2SQLGenerator
import asyncio

async def test():
    # Mock metadata
    metadata = {
    "file_id": "6171b481-788d-49d9-afb1-9eda7b028db5",
    "filename": "people-1000.csv",
    "table_name": "table_12dc529f_5e08_4de7_99a8_b113e28a1562_people_1000",
    "sql_schema": "CREATE TABLE table_12dc529f_5e08_4de7_99a8_b113e28a1562_people_1000 (\n            id SERIAL PRIMARY KEY,\n                \"index_col\" SMALLINT NOT NULL,\n    \"user_id\" VARCHAR(50) NOT NULL,\n    \"first_name\" VARCHAR(50) NOT NULL,\n    \"last_name\" VARCHAR(50) NOT NULL,\n    \"sex\" VARCHAR(50) NOT NULL,\n    \"email\" VARCHAR(200) NOT NULL,\n    \"phone\" VARCHAR(200) NOT NULL,\n    \"date_of_birth\" VARCHAR(50) NOT NULL,\n    \"job_title\" VARCHAR(200) NOT NULL,\n                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP\n            );",
    "columns_metadata": [
        {
            "id": "c69f7d64-f9e2-4749-a1b1-771bc25d4c5e",
            "file_id": "6171b481-788d-49d9-afb1-9eda7b028db5",
            "column_name": "Index",
            "data_type": "INTEGER",
            "sql_type": "INTEGER",
            "nullable": false,
            "is_category": false,
            "is_boolean": false,
            "is_date": false,
            "unique_count": 1000,
            "null_count": 0,
            "min_value": 1.0,
            "max_value": 1000.0,
            "mean_value": 500.5,
            "median_value": 500.5,
            "std_value": 288.8194360957494,
            "sample_values": [
                508,
                819,
                453,
                369,
                243
            ],
            "top_values": [
                {
                    "count": 1,
                    "value": 1
                },
                {
                    "count": 1,
                    "value": 672
                },
                {
                    "count": 1,
                    "value": 659
                },
                {
                    "count": 1,
                    "value": 660
                },
                {
                    "count": 1,
                    "value": 661
                }
            ],
            "enum_values": null,
            "value_mappings": {},
            "synonym_mappings": {},
            "example_queries": [
                "What is the average Index?",
                "Show records where Index is greater than 500.5",
                "What is the maximum Index?"
            ],
            "description": "Index: Integer column, ranging from 1.0 to 1000.0"
        },
        {
            "id": "8ba6496b-69ae-47b3-8e34-d510b6b6ea5c",
            "file_id": "6171b481-788d-49d9-afb1-9eda7b028db5",
            "column_name": "User Id",
            "data_type": "TEXT",
            "sql_type": "VARCHAR",
            "nullable": false,
            "is_category": false,
            "is_boolean": false,
            "is_date": false,
            "unique_count": 1000,
            "null_count": 0,
            "min_value": null,
            "max_value": null,
            "mean_value": null,
            "median_value": null,
            "std_value": null,
            "sample_values": [
                "6de2B1AcFd9cD19",
                "9dD0fA3FA742F6e",
                "b8EdE8dB06C193A",
                "3Ed2FEE49BF6ae1",
                "C7BC4419E1B81Ef"
            ],
            "top_values": [
                {
                    "count": 1,
                    "value": "8717bbf45cCDbEe"
                },
                {
                    "count": 1,
                    "value": "79fBAFAdA0Cc4c3"
                },
                {
                    "count": 1,
                    "value": "F16A25630bcb0CC"
                },
                {
                    "count": 1,
                    "value": "7D5A42fDBCE5D17"
                },
                {
                    "count": 1,
                    "value": "f11201935b4Aaa6"
                }
            ],
            "enum_values": null,
            "value_mappings": {},
            "synonym_mappings": {},
            "example_queries": [
                "Search for records where User Id contains 'keyword'",
                "Show distinct User Id values",
                "Count records by User Id"
            ],
            "description": "User Id: Text column"
        },
        {
            "id": "4158c4be-dc9c-48e9-8a63-85fbb26d6c98",
            "file_id": "6171b481-788d-49d9-afb1-9eda7b028db5",
            "column_name": "First Name",
            "data_type": "TEXT",
            "sql_type": "VARCHAR",
            "nullable": false,
            "is_category": false,
            "is_boolean": false,
            "is_date": false,
            "unique_count": 526,
            "null_count": 0,
            "min_value": null,
            "max_value": null,
            "mean_value": null,
            "median_value": null,
            "std_value": null,
            "sample_values": [
                "Melinda",
                "Dominic",
                "Clayton",
                "Kara",
                "Curtis"
            ],
            "top_values": [
                {
                    "count": 6,
                    "value": "Lydia"
                },
                {
                    "count": 6,
                    "value": "Heidi"
                },
                {
                    "count": 6,
                    "value": "Jo"
                },
                {
                    "count": 5,
                    "value": "Angel"
                },
                {
                    "count": 5,
                    "value": "Perry"
                }
            ],
            "enum_values": null,
            "value_mappings": {},
            "synonym_mappings": {
                "First Name": [
                    "name",
                    "title",
                    "called",
                    "named"
                ]
            },
            "example_queries": [
                "Search for records where First Name contains 'keyword'",
                "Show distinct First Name values",
                "Count records by First Name"
            ],
            "description": "First Name: Text column"
        },
        {
            "id": "365a5d3e-397d-4657-bc28-a9e47f9f27b5",
            "file_id": "6171b481-788d-49d9-afb1-9eda7b028db5",
            "column_name": "Last Name",
            "data_type": "TEXT",
            "sql_type": "VARCHAR",
            "nullable": false,
            "is_category": false,
            "is_boolean": false,
            "is_date": false,
            "unique_count": 628,
            "null_count": 0,
            "min_value": null,
            "max_value": null,
            "mean_value": null,
            "median_value": null,
            "std_value": null,
            "sample_values": [
                "Ortega",
                "Moran",
                "Hale",
                "Esparza",
                "Flores"
            ],
            "top_values": [
                {
                    "count": 6,
                    "value": "Duke"
                },
                {
                    "count": 5,
                    "value": "Nixon"
                },
                {
                    "count": 5,
                    "value": "Camacho"
                },
                {
                    "count": 5,
                    "value": "Bruce"
                },
                {
                    "count": 4,
                    "value": "Esparza"
                }
            ],
            "enum_values": null,
            "value_mappings": {},
            "synonym_mappings": {
                "Last Name": [
                    "name",
                    "title",
                    "called",
                    "named"
                ]
            },
            "example_queries": [
                "Search for records where Last Name contains 'keyword'",
                "Show distinct Last Name values",
                "Count records by Last Name"
            ],
            "description": "Last Name: Text column"
        },
        {
            "id": "c9a07664-70e8-4631-b4f7-3d04292dddc1",
            "file_id": "6171b481-788d-49d9-afb1-9eda7b028db5",
            "column_name": "Sex",
            "data_type": "TEXT",
            "sql_type": "VARCHAR",
            "nullable": false,
            "is_category": true,
            "is_boolean": false,
            "is_date": false,
            "unique_count": 2,
            "null_count": 0,
            "min_value": null,
            "max_value": null,
            "mean_value": null,
            "median_value": null,
            "std_value": null,
            "sample_values": [
                "Male",
                "Male",
                "Female",
                "Male",
                "Female"
            ],
            "top_values": [
                {
                    "count": 506,
                    "value": "Male"
                },
                {
                    "count": 494,
                    "value": "Female"
                }
            ],
            "enum_values": [
                "Male",
                "Female"
            ],
            "value_mappings": {
                "Male": "Male",
                "Female": "Female"
            },
            "synonym_mappings": {
                "Sex": [
                    "gender",
                    "sex",
                    "male or female"
                ]
            },
            "example_queries": [
                "How many records have Sex = 'Male'?",
                "Show all unique values for Sex",
                "Group by Sex and count"
            ],
            "description": "Sex: Text column, with 2 categories"
        },
        {
            "id": "bb90f74f-e9e6-4162-9620-90aa0fa91eec",
            "file_id": "6171b481-788d-49d9-afb1-9eda7b028db5",
            "column_name": "Email",
            "data_type": "TEXT",
            "sql_type": "VARCHAR",
            "nullable": false,
            "is_category": false,
            "is_boolean": false,
            "is_date": false,
            "unique_count": 1000,
            "null_count": 0,
            "min_value": null,
            "max_value": null,
            "mean_value": null,
            "median_value": null,
            "std_value": null,
            "sample_values": [
                "pweber@example.net",
                "gavinyork@example.org",
                "mitchell97@example.net",
                "cfrancis@example.com",
                "hunter00@example.com"
            ],
            "top_values": [
                {
                    "count": 1,
                    "value": "pwarner@example.org"
                },
                {
                    "count": 1,
                    "value": "jhancock@example.com"
                },
                {
                    "count": 1,
                    "value": "joel78@example.com"
                },
                {
                    "count": 1,
                    "value": "koneal@example.net"
                },
                {
                    "count": 1,
                    "value": "uharrell@example.org"
                }
            ],
            "enum_values": null,
            "value_mappings": {},
            "synonym_mappings": {},
            "example_queries": [
                "Search for records where Email contains 'keyword'",
                "Show distinct Email values",
                "Count records by Email"
            ],
            "description": "Email: Text column"
        },
        {
            "id": "0ab46b6b-9ef9-4cc4-ab27-a31a6a729a85",
            "file_id": "6171b481-788d-49d9-afb1-9eda7b028db5",
            "column_name": "Phone",
            "data_type": "TEXT",
            "sql_type": "VARCHAR",
            "nullable": false,
            "is_category": false,
            "is_boolean": false,
            "is_date": false,
            "unique_count": 1000,
            "null_count": 0,
            "min_value": null,
            "max_value": null,
            "mean_value": null,
            "median_value": null,
            "std_value": null,
            "sample_values": [
                "(037)993-4620x198",
                "001-803-340-4079x76935",
                "432-914-6682",
                "517.501.4960",
                "9626840627"
            ],
            "top_values": [
                {
                    "count": 1,
                    "value": "857.139.8239"
                },
                {
                    "count": 1,
                    "value": "(291)707-9579x2558"
                },
                {
                    "count": 1,
                    "value": "789.800.4253x0894"
                },
                {
                    "count": 1,
                    "value": "5441639643"
                },
                {
                    "count": 1,
                    "value": "010-361-9620x13266"
                }
            ],
            "enum_values": null,
            "value_mappings": {},
            "synonym_mappings": {},
            "example_queries": [
                "Search for records where Phone contains 'keyword'",
                "Show distinct Phone values",
                "Count records by Phone"
            ],
            "description": "Phone: Text column"
        },
        {
            "id": "55d480b3-6f1a-4708-86c8-b2c10202a3fb",
            "file_id": "6171b481-788d-49d9-afb1-9eda7b028db5",
            "column_name": "Date of birth",
            "data_type": "TEXT",
            "sql_type": "VARCHAR",
            "nullable": false,
            "is_category": false,
            "is_boolean": false,
            "is_date": false,
            "unique_count": 991,
            "null_count": 0,
            "min_value": null,
            "max_value": null,
            "mean_value": null,
            "median_value": null,
            "std_value": null,
            "sample_values": [
                "2010-03-13",
                "1952-02-27",
                "1953-12-01",
                "1943-10-14",
                "1973-04-08"
            ],
            "top_values": [
                {
                    "count": 2,
                    "value": "1955-07-31"
                },
                {
                    "count": 2,
                    "value": "1948-04-21"
                },
                {
                    "count": 2,
                    "value": "1983-10-08"
                },
                {
                    "count": 2,
                    "value": "1963-05-09"
                },
                {
                    "count": 2,
                    "value": "1968-01-29"
                }
            ],
            "enum_values": null,
            "value_mappings": {},
            "synonym_mappings": {},
            "example_queries": [
                "Search for records where Date of birth contains 'keyword'",
                "Show distinct Date of birth values",
                "Count records by Date of birth"
            ],
            "description": "Date of birth: Text column"
        },
        {
            "id": "63dc5740-45ff-4354-9a68-7bb35aff5420",
            "file_id": "6171b481-788d-49d9-afb1-9eda7b028db5",
            "column_name": "Job Title",
            "data_type": "TEXT",
            "sql_type": "VARCHAR",
            "nullable": false,
            "is_category": false,
            "is_boolean": false,
            "is_date": false,
            "unique_count": 519,
            "null_count": 0,
            "min_value": null,
            "max_value": null,
            "mean_value": null,
            "median_value": null,
            "std_value": null,
            "sample_values": [
                "Psychologist, counselling",
                "Herpetologist",
                "Research scientist (maths)",
                "Scientist, research (medical)",
                "Clothing/textile technologist"
            ],
            "top_values": [
                {
                    "count": 7,
                    "value": "Paediatric nurse"
                },
                {
                    "count": 7,
                    "value": "Phytotherapist"
                },
                {
                    "count": 6,
                    "value": "Nurse, adult"
                },
                {
                    "count": 6,
                    "value": "Production engineer"
                },
                {
                    "count": 6,
                    "value": "Nurse, mental health"
                }
            ],
            "enum_values": null,
            "value_mappings": {},
            "synonym_mappings": {
                "Job Title": [
                    "name",
                    "title",
                    "called",
                    "named"
                ]
            },
            "example_queries": [
                "Search for records where Job Title contains 'keyword'",
                "Show distinct Job Title values",
                "Count records by Job Title"
            ],
            "description": "Job Title: Text column"
        }
    ]
}

    nl2sql = NL2SQLGenerator("sqlcoder:7b")
    query = await nl2sql.generate_sql(
        table_name=metadata["table_name"],
        metadata=metadata,
        user_query="List the top 5 most common job titles"
    )

    print("Generated SQL:\n", query)


    llamamodel = NL2SQLGenerator("llama3.2")
    query2 = await llamamodel.generate_sql(
        table_name=metadata["table_name"],
        metadata=metadata,
        user_query="List the top 5 most common job titles"
    )
    print("Generated SQL:\n", query2)

asyncio.run(test())



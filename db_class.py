from pymongo import MongoClient


def get_connection(username: str, password: str):
    return MongoClient(
        f"mongodb+srv://{username}:{password}@cosmofeed.0krthzd.mongodb.net/?retryWrites=true&w=majority")


def get_db_connection(con, database_name: str):
    return con[database_name]


def insert_one(db_con, collection, results: dict, *sort_key: str):
    if not db_con[collection].find_one(filter={
        sort_key[0]: results[sort_key[0]],
        sort_key[1]: results[sort_key[1]],
        sort_key[2]: results[sort_key[2]]
    }):
        result_id = db_con[collection].insert_one(results)
        if result_id.inserted_id:
            return f'Document successfully saved into mongodb. ] \n{results[sort_key[0]], results[sort_key[1]], results[sort_key[2]]} {result_id.inserted_id}'
        else:
            return 'No data saved'
    else:
        return f"Record already exists into db.  \n{results[sort_key[0]], results[sort_key[1]], results[sort_key[2]]}"


def close_connection(mongo_db_connection: MongoClient):
    mongo_db_connection.close()


def get_proxy_ip():
    return {
        "http": "http://msuoebwh-rotate:oet3eq1aq6w1@p.webshare.io:80/",
        "https": "http://msuoebwh-rotate:oet3eq1aq6w1@p.webshare.io:80/"
    }

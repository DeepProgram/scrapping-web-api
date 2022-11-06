import json

from sqlalchemy.orm import Session
from db.db_sql_models import Upwork, User, ScrapingStatus
from sqlalchemy import func, exists
from typing import Optional, List
from schemas import SignupInfo
from uuid import uuid4
from logics.bcrypt_process import get_password_hash


def get_search_query_by_group(db: Session) -> List:
    result = db.query(Upwork.search_query, func.count(Upwork.search_query)).group_by(Upwork.search_query).limit(6).all()
    if result:
        search_queries = [i for i, j in result]
        return search_queries
    return []


def get_random_search_result(db: Session, search_query) -> Optional[List]:
    result = db.query(Upwork.search_result).filter(Upwork.search_query == search_query) \
        .order_by(Upwork.add_time.desc()).limit(20).all()
    search_list_dictionary = []
    for search_result, in result:
        search_list_dictionary.append(json.loads(search_result))
    return search_list_dictionary[::-1]


def add_user_in_db(db: Session, signup_info: SignupInfo):
    result = bool(db.query(exists().where(User.email == signup_info.email)).scalar())
    if not result:
        user_table_row = User()
        user_id = str(uuid4())
        user_table_row.user_id = user_id
        user_table_row.email = signup_info.email
        user_table_row.password = get_password_hash(signup_info.password)
        user_table_row.first_name = signup_info.first_name
        user_table_row.last_name = signup_info.last_name
        db.add(user_table_row)
        db.commit()
        return [user_id, signup_info.first_name]
    return [None, None]


def if_email_exist_in_db(db: Session, email: str):
    found_user = bool(db.query(exists().where(User.email == email)).scalar())
    return found_user


def get_password_from_email(db: Session, email: str):
    user_id, password, first_name = db.query(User.user_id, User.password, User.first_name).filter(
        User.email == email).first()
    return [user_id, password, first_name]


def delete_existing_data_using_same_query(db: Session, user_id: str, search_query: str):
    db.query(Upwork).filter(Upwork.user_id == user_id, Upwork.search_query == search_query).delete()
    db.commit()


def get_status_message_from_db(db: Session, user_id: str):
    status_result = db.query(ScrapingStatus.index, ScrapingStatus.status).filter(
        ScrapingStatus.user_id == user_id).first()
    if status_result is not None:
        db.query(ScrapingStatus).filter(ScrapingStatus.index == status_result[0]).delete()
        db.commit()
        return status_result[1]
    return status_result


def get_upwork_data_by_id_and_query(db: Session, user_id: str, search_query: str):
    search_result_list_unprocessed = db.query(Upwork.search_result).filter(Upwork.user_id == user_id,
                                                                           Upwork.search_query == search_query).all()

    search_result_list = []
    for search_result, in search_result_list_unprocessed:
        search_result_list.append(json.loads(search_result))
    return search_result_list


def get_first_name_from_user_id(db: Session, user_id: str):
    query_result = db.query(User.first_name).filter(User.user_id == user_id).first()
    if query_result is not None:
        return query_result[0]
    return query_result

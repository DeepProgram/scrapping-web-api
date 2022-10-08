import redis


def get_upwork_data(str_uuid, redis_db: redis.Redis):
    if redis_db.exists(str_uuid) == 0:
        return -1
    else:
        return redis_db.lpop(str_uuid)


def if_data_exists(str_uuid, redis_db: redis.Redis):
    if redis_db.exists(str_uuid) == 0:
        return [False, -1, ""]
    else:
        returned_data = [True, -1, ""]
        string_data = redis_db.lrange(str_uuid, 0, 0)[0].decode()
        if string_data == "automation_started":
            returned_data[1], returned_data[2] = 1, "automation_started"
        elif string_data == "selenium_started":
            returned_data[1], returned_data[2] = 2, "selenium_started"
        elif string_data == "page_loaded":
            returned_data[1], returned_data[2] = 3, "page_loaded"
        elif string_data == "end":
            returned_data[1], returned_data[2] = 0, "completed"

        else:
            try:
                page_no = int(string_data)
                returned_data[1], returned_data[2] = 4, page_no
            except Exception as e:
                return [True, 5, "available"]
        redis_db.lpop(str_uuid)
        return returned_data

SUCCESS_RESPONSE = {
    "msg": "Амжилттай",
    "status": 200,
    "data": {
        "name": "Test",
        "freeProject": False,
        "cityPayer": True,
        "vatPayer": True,
        "found": True,
        "vatpayerRegisteredDate": "2002-04-09",
        "isGovernment": False,
    },
}

# A non-VAT-payer: the live server returns 200 with a null registration date.
NON_VATPAYER_RESPONSE = {
    "msg": "Амжилттай",
    "status": 200,
    "data": {
        "name": "Test User",
        "freeProject": False,
        "cityPayer": False,
        "vatPayer": False,
        "found": True,
        "vatpayerRegisteredDate": None,
        "isGovernment": False,
    },
}

# A TIN the server doesn't know about: 200 with a null data object.
NOT_FOUND_RESPONSE = {
    "msg": "Амжилттай",
    "status": 200,
    "data": None,
}

# The live server may return a null isGovernment flag; the SDK must tolerate it.
NULL_GOVERNMENT_RESPONSE = {
    "msg": "Амжилттай",
    "status": 200,
    "data": {
        "name": "Test",
        "freeProject": False,
        "cityPayer": True,
        "vatPayer": True,
        "found": True,
        "vatpayerRegisteredDate": "2002-04-09",
        "isGovernment": None,
    },
}

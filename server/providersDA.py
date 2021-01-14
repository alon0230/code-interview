import json
import logging
from datetime import datetime

import settings

logger = logging.getLogger('vim')

__providers = []


def __get_all_providers():
    global __providers

    # this check is done only since the data is not changing, so there's no point in reloading it
    if not __providers:
        try:
            with open(settings.PROVIDERS_DB_LOCATION, 'r') as providers_file:
                __providers = json.load(providers_file)
        except Exception as e:
            logger.exception('Error reaching the providers data')

    return __providers


def get_providers(specialty, min_score, date):
    providers = __get_all_providers()

    for provider in providers:
        if specialty.lower() in map(lambda spec: spec.lower(), provider['specialties']) and \
           provider['score'] >= min_score and \
           is_provider_available(provider, date):
            yield provider


def is_provider_available(provider, date):
    return any(map(lambda availability: datetime.utcfromtimestamp(int(availability['from'])/1000) <= date <= datetime.utcfromtimestamp(int(availability['to'])/1000), provider['availableDates']))


def get_provider_by_name(name):
    return next(filter(lambda provider: provider['name'] == name, __get_all_providers()), None)

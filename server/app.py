import logging
from datetime import datetime

from flask import Flask, render_template, jsonify, request
from flask_expects_json import expects_json

import settings
from providersDA import get_providers, is_provider_available, get_provider_by_name

logger = logging.getLogger('vim')
formatter = logging.Formatter('%(asctime)s | %(name)s | %(levelname)s | %(message)s')
sh = logging.StreamHandler()
sh.setFormatter(formatter)
logger.setLevel(settings.LOG_LEVEL)
logger.addHandler(sh)

app = Flask(__name__)
appointments_post_schema = {
    'type': 'object',
    'properties': {
        'name': {'type': 'string'},
        'date': {'type': 'integer'}
    },
    'required': ['name', 'date']
}


class InvalidParamError(Exception):
    pass


def parse_specialty(specialty):
    if not specialty:
        logger.debug('Invalid request. no speciality')
        raise InvalidParamError

    return specialty


def parse_min_score(min_score):
    try:
        parsed = float(request.args.get('minScore'))
    except ValueError as e:
        logger.debug('Invalid min score {0}'.format(min_score))
        raise InvalidParamError

    return parsed


def parse_date(date):
    try:
        parsed = datetime.utcfromtimestamp(int(date) / 1000)
    except ValueError as e:
        logger.debug('Invalid date. {0}'.format(date))
        raise InvalidParamError()

    return parsed


@app.route('/appointments', methods=['GET', 'POST'])
def appointments():
    if request.method == 'GET':
        return appointments_get()
    elif request.method == 'POST':
        return appointments_post()
    else:
        return '', 400


def appointments_get():
    try:
        specialty = parse_specialty(request.args.get('specialty'))
        min_score = parse_min_score(request.args.get('min_score'))
        date = parse_date(request.args.get('date'))
    except InvalidParamError as e:
        logger.error('Invalid param | request args: {0}'.format(request.args))
        return 'Invalid request', 400

    providers = get_providers(specialty=specialty, min_score=min_score, date=date)
    providers = sorted(providers, key=lambda provider: provider['score'], reverse=True)
    return jsonify([provider['name'] for provider in providers])


@expects_json(appointments_post_schema)
def appointments_post():
    params = request.get_json()
    try:
        name = params['name']
        date = parse_date(params['date'])
    except InvalidParamError:
        return '', 400

    provider = get_provider_by_name(name)
    if not provider:
        logger.info('Invalid appointment: Provider does not exist | name: {0}'.format(name))
        return 'Invalid appointment: Provider does not exist ', 400

    if not is_provider_available(provider, date):
        logger.info('Invalid appointment: Provider is not available in the specified date | provider: {0} | date: {1}'.format(name, date))
        return 'Invalid appointment: Provider is not available in the specified date', 400

    logger.info('Appointment scheduled successfully | provider: {0} | date: {1}'.format(name, date))
    return name, 200


if __name__ == '__main__':
    app.run(debug=True, port=settings.PORT)

#! /usr/bin/env python

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import sys
import getopt
import boto3
import pandas as pd
import json
from datetime import datetime

personalize_runtime = None

from shared import (
    load_movies,
    load_interactions,
    get_random_movie_ids,
    get_random_user_ids
)

JOB_TYPES = ['user-personalization', 'similar-items', 'personalized-ranking']

def create_user_personalization_input_file(num_records_to_generate):
    user_ids = get_random_user_ids(num_records_to_generate)

    ts = datetime.now().strftime('%Y%m%d-%H%M%S')
    input_filename = f'batch-input-{JOB_TYPES[0]}-{ts}.json'

    with open(input_filename, 'w') as json_input:
        for user_id in user_ids:
            json_input.write(json.dumps({'userId': str(user_id)}) + '\n')

    return input_filename

def create_similar_items_input_file(num_records_to_generate):
    item_ids = get_random_movie_ids(num_records_to_generate)
    
    ts = datetime.now().strftime('%Y%m%d-%H%M%S')
    input_filename = f'batch-input-{JOB_TYPES[1]}-{ts}.json'

    with open(input_filename, 'w') as json_input:
        for item_id in item_ids:
            json_input.write(json.dumps({'itemId': str(item_id)}) + '\n')

    return input_filename

def create_personalized_ranking_input_file(num_records_to_generate, num_items_per_rank):
    user_ids = get_random_user_ids(num_records_to_generate)
    
    ts = datetime.now().strftime('%Y%m%d-%H%M%S')
    input_filename = f'batch-input-{JOB_TYPES[2]}-{ts}.json'

    with open(input_filename, 'w') as json_input:
        for user_id in user_ids:
            item_ids = get_random_movie_ids(num_items_per_rank)
            item_list = [str(id) for id in item_ids]
            json_input.write(json.dumps({'userId': str(user_id), 'itemList': item_list}) + '\n')

    return input_filename

def usage_and_exit(code = None, message = None):
    if message:
        print(message)
    print(f'Usage: {sys.argv[0]} -j job-type [-b bucket-name] [-r region]')
    print(f'\twhere job-type is one of {JOB_TYPES}')
    sys.exit(code)

if __name__=="__main__":
    job_type = None
    bucket_name = None
    region = None

    num_records_to_generate = 50
    num_items_per_rank = 20

    try:
        opts, args = getopt.getopt(sys.argv[1:], 'hj:b:r:', ['job-type=', 'bucket-name=', 'region='])
    except getopt.GetoptError:
        usage_and_exit(2)

    for opt, arg in opts:
        if opt == '-h':
            usage_and_exit()
            sys.exit()
        elif opt in ('-j', '--job-type'):
            job_type = arg
        elif opt in ('-b', '--bucket-name'):
            bucket_name = arg
        elif opt in ('-r', '--region'):
            region = arg

    if not job_type:
        usage_and_exit(1, f'job-type is required ({JOB_TYPES})')
    elif job_type not in JOB_TYPES:
        usage_and_exit(1, f'job-type is invalid; must be one of {JOB_TYPES}')

    load_movies()
    load_interactions()

    print()
    print('Generating input file...')

    if job_type == JOB_TYPES[0]:
        input_filename = create_user_personalization_input_file(num_records_to_generate)
    elif job_type == JOB_TYPES[1]:
        input_filename = create_similar_items_input_file(num_records_to_generate)
    elif job_type == JOB_TYPES[2]:
        input_filename = create_personalized_ranking_input_file(num_records_to_generate, num_items_per_rank)
    else:
        usage_and_exit(1, 'Unexpected job-type')

    upload_filename = f'input/{input_filename}'

    if bucket_name:
        print()
        print(f'Uploading input file {input_filename} to s3://{bucket_name}/{upload_filename}')

        s3_client = boto3.client(service_name = 's3', region_name = region)
        response = s3_client.upload_file(input_filename, bucket_name, upload_filename)
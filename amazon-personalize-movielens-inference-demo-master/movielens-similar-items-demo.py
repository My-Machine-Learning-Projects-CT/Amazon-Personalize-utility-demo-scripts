#! /usr/bin/env python

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import sys
import getopt
import boto3
import pandas as pd
from datetime import datetime
from tabulate import tabulate
import locale

locale.setlocale(locale.LC_ALL, '')

personalize_runtime = None

from shared import (
    load_interactions,
    load_movies,
    lookup_movie_title_and_genres,
    get_random_movie_ids,
    get_interactions_for_user,
    get_popular_genres
)

def get_recommendations_for_item(campaign_arn, item_id, num_results = 20):
    response = personalize_runtime.get_recommendations(
            campaignArn = campaign_arn, 
            itemId = str(item_id),
            numResults = num_results
    )

    recommendations = []

    for item in response['itemList']:
        title_and_genres = lookup_movie_title_and_genres(item['itemId'])
        recommendations.append([item['itemId'], title_and_genres[0], title_and_genres[1]])

    df = pd.DataFrame(recommendations)
    df.columns = ['ITEM_ID', 'TITLE', 'GENRES']
    return df

if __name__=="__main__": 
    region = None
    campaign_arn = None
    item_id = None

    try:
        opts, args = getopt.getopt(sys.argv[1:], 'hc:i:r:', ['campaign-arn=', 'item-id=', 'region='])
    except getopt.GetoptError:
        print(f'Usage: {sys.argv[0]} -c campaign-arn [-i item-id] [-r region]')
        sys.exit(2)

    for opt, arg in opts:
        if opt == '-h':
            print(f'Usage: {sys.argv[0]} -c campaign-arn [-i item-id] [-r region]')
            sys.exit()
        elif opt in ('-c', '--campaign-arn'):
            campaign_arn = arg
        elif opt in ('-i', '--item-id'):
            item_id = arg
        elif opt in ('-r', '--region'):
            region = arg

    if not campaign_arn:
        print('campaign-arn is required')
        print(f'Usage: {sys.argv[0]} -c campaign-arn [-i item-id] [-r region]')
        sys.exit(1)

    load_movies()
    load_interactions()

    personalize_runtime = boto3.client(service_name = 'personalize-runtime', region_name = region)

    print()
    print('************ ITEM INFO ***************')
    if not item_id:
        print('No item_id provided so randomly selecting a user from the interactions dataset')
        item_id = int(get_random_movie_ids()[0])
    print(f'item_id: {item_id}')

    movie = lookup_movie_title_and_genres(item_id)
    print(f'Title: {movie[0]}')
    print(f'Genres: {movie[1]}')

    print()

    print('************ ITEM RECOMMENDATIONS ***************')
    recs_df = get_recommendations_for_item(campaign_arn, item_id, 50)
    print(tabulate(recs_df.head(20), headers=list(recs_df.columns), showindex = False, tablefmt="pretty"))
    print()

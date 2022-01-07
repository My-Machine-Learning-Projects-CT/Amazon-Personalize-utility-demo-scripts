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

from shared import (
    load_interactions,
    load_movies,
    lookup_movie_title_and_genres,
    get_random_user_ids,
    get_random_movie_ids,
    get_interactions_for_user,
    get_popular_genres
)

personalize_runtime = None

def get_reranked_items_for_user(campaign_arn, user_id, item_ids):
    response = personalize_runtime.get_personalized_ranking(
            campaignArn = campaign_arn, 
            userId = str(user_id),
            inputList = [str(id) for id in item_ids]
    )

    recommendations = []

    for item in response['personalizedRanking']:
        title_and_genres = lookup_movie_title_and_genres(item['itemId'])
        recommendations.append([item['itemId'], title_and_genres[0], title_and_genres[1], item.get('score')])

    df = pd.DataFrame(recommendations)
    df.columns = ['ITEM_ID', 'TITLE', 'GENRES', 'SCORE']
    return df

if __name__=="__main__": 
    region = None
    campaign_arn = None
    user_id = None
    item_ids = None

    try:
        opts, args = getopt.getopt(sys.argv[1:], 'hc:u:i:r:', ['campaign-arn=', 'user-id=', 'item-ids=', 'region='])
    except getopt.GetoptError:
        print(f'Usage: {sys.argv[0]} -c campaign-arn [-u user-id] [-i item-ids] [-r region]')
        sys.exit(2)

    for opt, arg in opts:
        if opt == '-h':
            print(f'Usage: {sys.argv[0]} -c campaign-arn [-u user-id] [-i item-ids] [-r region]')
            sys.exit()
        elif opt in ('-c', '--campaign-arn'):
            campaign_arn = arg
        elif opt in ('-u', '--user-id'):
            user_id = arg
        elif opt in ('-i', '--item-ids'):
            item_ids = arg.split(',')
        elif opt in ('-r', '--region'):
            region = arg

    if not campaign_arn:
        print('campaign-arn is required')
        print(f'Usage: {sys.argv[0]} -c campaign-arn [-u user-id] [-i item-ids] [-r region]')
        sys.exit(1)

    load_movies()
    load_interactions()

    personalize_runtime = boto3.client(service_name = 'personalize-runtime', region_name = region)

    print()
    print('************ USER INFO ***************')
    if not user_id:
        print('No user_id provided so randomly selecting a user from the interactions dataset')
        user_id = int(get_random_user_ids(1)[0])
    print(f'user_id: {user_id}')
    print()

    print()
    print('************ ITEM IDS INFO ***************')
    if not item_ids:
        print('No item_ids provided so randomly selecting 20 movies from the movies dataset')
        item_ids = get_random_movie_ids(20)
    print(f'item_ids: {item_ids}')
    print()

    unranked_list = []
    for item_id in item_ids:
        unranked_list.append(lookup_movie_title_and_genres(item_id))

    unranked_df = pd.DataFrame(unranked_list, columns = ['TITLE', 'GENRES'])
    print(tabulate(unranked_df, headers=list(unranked_df.columns), showindex = False, tablefmt="pretty"))
    print()

    print('************ RECENT USER INTERACTIONS ***************')
    user_interactions_df = get_interactions_for_user(user_id)
    print(tabulate(user_interactions_df.head(20), headers=list(user_interactions_df.columns), showindex = False, tablefmt="pretty"))
    print()

    print('************ USER TOP GENRES ***************')
    user_top_genres = get_popular_genres(user_interactions_df)
    print(tabulate(user_top_genres, headers=['GENRE', 'COUNT'], showindex = False, tablefmt="pretty"))
    print()

    print('************ RERANKED ITEMS ***************')
    recs_df = get_reranked_items_for_user(campaign_arn, user_id, item_ids)
    print(tabulate(recs_df.head(20), headers=list(recs_df.columns), showindex = False, tablefmt="pretty"))
    print()

    print('************ UNRANKED vs RANKED ITEMS ***************')
    top_compare_df = pd.concat([unranked_df['TITLE'], recs_df['TITLE']], axis=1)
    top_compare_df.columns = ['Unranked', 'Reranked']
    print(tabulate(top_compare_df, headers=['Unranked Movies', 'Reranked Movies'], showindex = False, tablefmt="pretty"))
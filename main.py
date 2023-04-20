#!/usr/bin/env python
__author__ = "Nova Kwok"
__license__ = "GPLv3"
import graphene
import csv
import datetime
import requests
import argparse
import random
import time

parser = argparse.ArgumentParser()
parser.add_argument('-t','--token',required=True,help="The GitHub Token.")
parser.add_argument('-r','--repos',nargs='+',required=True,help="List of repositories, in the form like 'user/repo user2/repo2 user3/repo3'.")
args = parser.parse_args()

headers = {"Authorization": "token "+args.token}

fields = ["repo_name", "username", "name", "email", "twitter_username", "repo_count", "blog", "company", "bio", "avatar_url", "hireable", "num_followers", "num_following","created_at", "updated_at","star_time"]

min_sleep_time = 0.25 # in seconds
max_sleep_time = 3.0 # in seconds

def run_query(query):
    request = requests.post('https://api.github.com/graphql', json={'query': query}, headers=headers)
    if request.status_code == 200:
        return request.json()
    else:
        raise Exception("Query failed to run by returning code of {}. {}".format(request.status_code, query))

query_template = """
{{
  repository(owner: "{0}", name: "{1}") {{
    stargazers(first: 100 {2}) {{
      pageInfo {{
        endCursor
        hasNextPage
        hasPreviousPage
        startCursor
      }}
      edges {{
        starredAt
        node {{
          login
          email
          name
          bio
          company
          repositories(first:100, isFork: false) {{
            totalCount
          }}
          isHireable
          avatarUrl
          createdAt
          updatedAt
          twitterUsername
          websiteUrl
          followers(first: 0) {{
            totalCount
          }}
          following(first: 0) {{
            totalCount
          }}
        }}
      }}
    }}
  }}
}}
"""

for repo in args.repos:
    owner = repo.split('/')[0]
    repo_name = repo.split('/')[1]

    star_list = []
    hasNextPage = True
    endCursor = "" # Start from begining
    count = 0

    user_filename = f"{owner}__{repo_name}_stargazers.csv"
    with open(user_filename, "w", newline="", encoding="utf-8") as stars:
        stars_writer = csv.writer(stars)
        stars_writer.writerow(fields)
        while hasNextPage:
            this_query = query_template.format(owner, repo_name, endCursor)
            result = run_query(this_query) # Execute the query
            hasNextPage = result['data']['repository']['stargazers']['pageInfo']['hasNextPage']
            endCursor = result['data']['repository']['stargazers']['pageInfo']['endCursor']
            endCursor = ', after: "' + endCursor + '"'
            data = result['data']['repository']['stargazers']['edges']

            for item in data:
                username = item['node']['login']
                name = item['node']['name']
                email = item['node']['email']
                twitter_username = item['node']['twitterUsername']
                num_followers = item['node']['followers']['totalCount']
                num_following = item['node']['following']['totalCount']
                hireable = item['node']['isHireable']
                company = item['node']['company']
                bio = item['node']['bio']
                avatar_url = item['node']['avatarUrl']
                blog = item['node']['websiteUrl']
                repo_count = item['node']['repositories']['totalCount']
                created_at = item['node']['createdAt']
                created_at = datetime.datetime.strptime(created_at,'%Y-%m-%dT%H:%M:%SZ')
                created_at = created_at.strftime('%Y-%m-%d %H:%M:%S')
                updated_at = item['node']['updatedAt']
                updated_at = datetime.datetime.strptime(updated_at,'%Y-%m-%dT%H:%M:%SZ')
                updated_at = updated_at.strftime('%Y-%m-%d %H:%M:%S')
                star_time = datetime.datetime.strptime(item['starredAt'],'%Y-%m-%dT%H:%M:%SZ')
                star_time = star_time.strftime('%Y-%m-%d %H:%M:%S')
                star_list.append((username,star_time))
                stars_writer.writerow([repo_name,username,name,email,twitter_username,repo_count,blog,company,bio,avatar_url,hireable,num_followers,num_following,created_at,updated_at,star_time])

            count += 100
            print(f"{count} users processed.")

            # Sleep for a random time between min_sleep_time and max_sleep_time
            sleep_time = random.uniform(min_sleep_time, max_sleep_time)
            time.sleep(sleep_time)

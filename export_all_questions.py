import re
import sys, os
import requests
import json
from types import SimpleNamespace
import markdown
from joblib import Memory
import mdformat

html_content = """
<!DOCTYPE html>  
<html>
    <body>BODY_CONTENT</body>
</html>"""

body_content = ""

graphQLEndpoint = "https://leetcode.com/graphql"
questionGQL = open("graphql/question.gql").read()
officialSolutionGQL = open("graphql/official_solution.gql").read()
solutionGQL = open("graphql/solution.gql").read()
playgroundGQL = open("graphql/playground.gql").read()

# Define the cache directory
cache_dir = ".cache"
os.makedirs(cache_dir, exist_ok=True)

# Create a Memory object to manage caching
memory = Memory(location=cache_dir, verbose=0)


@memory.cache
def fetch_question(question_slug: str):
    baseJSON = {
        "operationName": "questionData",
        "variables": {"titleSlug": question_slug},
        "query": questionGQL,
    }

    resp = requests.get(graphQLEndpoint, json=baseJSON)
    x = json.loads(resp.text, object_hook=lambda d: SimpleNamespace(**d))
    return x


@memory.cache
def fetch_official_solution(question_slug: str):
    baseJSON = {
        "operationName": "ugcArticleOfficialSolutionArticle",
        "variables": {"questionSlug": question_slug},
        "query": officialSolutionGQL,
    }

    resp = requests.get(graphQLEndpoint, json=baseJSON)
    x = json.loads(resp.text, object_hook=lambda d: SimpleNamespace(**d))
    return x


@memory.cache
def fetch_playground(uuid: str):
    baseJSON = {
        "operationName": "fetchPlayground",
        "variables": {"uuid": uuid},
        "query": playgroundGQL,
    }

    resp = requests.get(graphQLEndpoint, json=baseJSON)
    x = json.loads(resp.text, object_hook=lambda d: SimpleNamespace(**d))
    return x


@memory.cache
def fetch_solution(topicId: str):
    baseJSON = {
        "variables": {"topicId": topicId},
        "query": solutionGQL,
    }

    resp = requests.get(graphQLEndpoint, json=baseJSON)
    x = json.loads(resp.text, object_hook=lambda d: SimpleNamespace(**d))
    return x


def get_question(question_link):
    slug = re.search(r"(?<=problems/)[^/]+", question_link)
    if slug:
        slug = slug.group(0)
    else:
        print(f"Invalid link: {question_link}", file=sys.stderr)
        return

    topicId = re.search(r"(?<=solutions/)[^/]+", question_link)
    if topicId:
        topicId = topicId.group(0)

    x = fetch_question(slug).data.question

    global body_content
    body_content += f"\n<h2>{x.title}</h2>\n\n"
    body_content += f"<h3>Statement</h3>\n\n"
    body_content += x.content

    # Add tags
    if x.topicTags:
        tags = ", ".join([topic.name for topic in x.topicTags])
        body_content += f"\n<strong>Tags:</strong> {tags}\n\n"

    sol = ""
    if x.hints:
        sol += "\n<h3>Hints</h3>\n\n"
        sol += "<ul>\n"
        for hint in x.hints:
            sol += f"<li>{hint}</li>\n"
        sol += "</ul>\n"

    y = None
    if x.solution.canSeeDetail:
        y = fetch_official_solution(slug).data.ugcArticleOfficialSolutionArticle
    elif topicId:
        y = fetch_solution(topicId).data.ugcArticleSolutionArticle

    if y:
        if y.summary:
            sol += "\n<h3>Solution Summary</h3>\n\n"
            summary = y.summary
            if y.isSerialized:
                summary = bytes(summary, "utf-8").decode("unicode_escape")
            sol += summary
        content = y.content
        truncate_with = "## Solution Article"
        if truncate_with in content:
            i = content.index(truncate_with) + len(truncate_with)
            content = content[i:]
        if y.isSerialized:
            # replace all escaped characters with unescaped one
            content = bytes(content, "utf-8").decode("unicode_escape")
        content = mdformat.text(content)
        content = markdown.markdown(content)
        # Replace relative links with absolute links
        content = content.replace(
            "../Figures", f"https://leetcode.com/problems/{slug}/Figures"
        )
        # Increase the level of the headings
        content = re.sub(
            r"<h([1-5])>",
            lambda m: "<h" + str(len(m.group(0)) + 1) + ">",
            content,
        )
        sol += "\n<h3>Solution</h3>\n\n"
        sol += content

    if sol:
        body_content += sol


def replace_iframes_with_code(markdown_content):
    """
    Replace all <iframe> elements in the markdown content with C++ code
    fetched using the fetch_playground function.
    """

    def iframe_replacer(match):
        iframe_tag = match.group(0)
        uuid_match = re.search(r'src="([^"]+)"', iframe_tag)
        if not uuid_match:
            return iframe_tag  # Return the original iframe if no UUID is found
        playground_link = uuid_match.group(1)
        uuid = re.search(r"playground/([^/]+)", playground_link)
        if not uuid:
            print("No UUID found in playground link:", playground_link, file=sys.stderr)
            return iframe_tag
        uuid = uuid.group(1)
        try:
            playground_data = fetch_playground(uuid).data
            for x in playground_data.allPlaygroundCodes:
                if x.langSlug == "cpp":
                    return f"<pre>\n{x.code}</pre>"
            if playground_data.allPlaygroundCodes:
                playground_data.allPlaygroundCodes[0]
                return f"<pre>{x.langSlug}\n{x.code}</pre>"
        except Exception as e:
            print(f"Error fetching playground for UUID {uuid}: {e}", file=sys.stderr)
        return iframe_tag  # Return the original iframe if an error occurs

    # Replace all iframe tags with the corresponding C++ code
    return re.sub(r"<iframe[^>]*></iframe>", iframe_replacer, markdown_content)


def main():
    global html_content, body_content

    with open("question_links.txt") as f:
        links = f.read()
    question_links = links.split("\n")

    for line in question_links:
        if not line:
            continue
        try:
            if line[0] == "~":
                body_content += f"\n<h1>{line[1:]}</h1>\n\n"
            else:
                print(f"Fetching the problem: {line}")
                get_question(line)
            print("------------------------------")
        except Exception as e:
            print(f"Error processing line {line}: {e}", file=sys.stderr)
            continue

    # Replace all $$expr$$ into $expr$
    body_content = re.sub(r"\$\$(.*?)\$\$", r"$\1$", body_content)
    # Replace iframes with C++ code
    body_content = replace_iframes_with_code(body_content)

    html_content = html_content.replace("BODY_CONTENT", body_content)
    with open("blind_75.html", "w") as f:
        f.write(html_content)


if __name__ == "__main__":
    print("\n")
    main()

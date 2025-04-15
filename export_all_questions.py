import re
import sys, os
import requests
import json
from types import SimpleNamespace
import html2text
from joblib import Memory
import mdformat


markdown_content = ""

graphQLEndpoint = "https://leetcode.com/graphql"
questionGQL = open("graphql/question.gql").read()
officialSolutionGQL = open("graphql/official_solution.gql").read()
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


def get_section(section_text):
    global markdown_content
    markdown_content += f"\n# {section_text[1:]}\n\n"


def get_question(question_link):
    slug = question_link.split("https://leetcode.com/problems/", 1)[1]
    if not slug:
        print(f"Invalid link: {question_link}", file=sys.stderr)
        return

    x = fetch_question(slug).data.question

    global markdown_content
    markdown_content += f"\n## {x.title}\n\n"
    markdown_content += f"### Statement\n\n"
    # replace <sub> with \textsuperscript and also <sup>
    content = re.sub(r"<sub>(.*?)</sub>", r"\\textsuperscript{\1}", x.content)
    content = re.sub(r"<sup>(.*?)</sup>", r"\\textsuperscript{\1}", content)
    markdown_content += html2text.html2text(content)

    # Add tags
    if x.topicTags:
        tags = ", ".join([topic.name for topic in x.topicTags])
        markdown_content += f"\n**Tags:** {tags}\n\n"

    sol = ""
    if x.hints:
        sol += "\n### Hints\n\n"
        for hint in x.hints:
            sol += f"- {hint}\n"

    if x.solution.canSeeDetail:
        y = fetch_official_solution(slug).data.ugcArticleOfficialSolutionArticle
        if y.summary:
            sol += "\n### Solution Summary\n\n"
            sol += html2text.html2text(y.summary)
        content = y.content
        # increase the level of the headings
        content = re.sub(
            r"^(#+)", lambda m: "#" * (len(m.group(0)) + 1), content, flags=re.M
        )
        sol += content[content.index("### Solution Article") :]

    if sol:
        markdown_content += sol


def replace_iframes_with_code(markdown_content):
    """
    Replace all <iframe> elements in the markdown content with C++ code
    fetched using the fetch_playground function.
    """

    def iframe_replacer(match):
        iframe_tag = match.group(0)
        uuid_match = re.search(r'name="([^"]+)"', iframe_tag)
        if not uuid_match:
            return iframe_tag  # Return the original iframe if no UUID is found
        uuid = uuid_match.group(1)
        try:
            playground_data = fetch_playground(uuid).data
            for x in playground_data.allPlaygroundCodes:
                if x.langSlug == "cpp":
                    return f"```cpp\n{x.code}\n```"
            if playground_data.allPlaygroundCodes:
                playground_data.allPlaygroundCodes[0]
                return f"```{x.langSlug}\n{x.code}\n```"
        except Exception as e:
            print(f"Error fetching playground for UUID {uuid}: {e}", file=sys.stderr)
        return iframe_tag  # Return the original iframe if an error occurs

    # Replace all iframe tags with the corresponding C++ code
    return re.sub(
        r'<iframe[^>]*name="[^"]+"[^>]*></iframe>', iframe_replacer, markdown_content
    )


def main():
    with open("question_links.txt") as f:
        links = f.read()
    question_links = links.split("\n")

    for line in question_links:
        if not line:
            continue
        try:
            if line[0] == "~":
                get_section(line)
            else:
                print(f"Fetching the problem: {line}")
                get_question(line)
            print("------------------------------")
        except Exception as e:
            print(f"Error processing line {line}: {e}", file=sys.stderr)
            continue

    global markdown_content
    # Replace all $$expr$$ into $expr$
    markdown_content = re.sub(r"\$\$(.*?)\$\$", r"$\1$", markdown_content)
    # Replace iframes with C++ code
    markdown_content = replace_iframes_with_code(markdown_content)
    # Save the final markdown content to a file
    markdown_content = mdformat.text(markdown_content)
    with open("blind_75.md", "w") as f:
        f.write(markdown_content)

    # Use pandoc to generate a pdf
    print("Generating a PDF file...")
    os.system("make")


if __name__ == "__main__":
    print("\n")
    main()

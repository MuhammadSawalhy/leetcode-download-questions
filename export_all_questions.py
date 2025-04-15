import re
import sys
import os
import requests
import json
import argparse
from types import SimpleNamespace
import markdown
from joblib import Memory
import mdformat

# Define the cache directory
cache_dir = ".cache"
os.makedirs(cache_dir, exist_ok=True)

# Create a Memory object to manage caching
memory = Memory(location=cache_dir, verbose=0)

# Define output directory for individual problem files
output_dir = "problems"
os.makedirs(output_dir, exist_ok=True)

html_wrapper = """
<!DOCTYPE html>  
<html>
    <body>BODY_CONTENT</body>
</html>"""

graphQLEndpoint = "https://leetcode.com/graphql"
questionGQL = open("graphql/question.gql").read()
officialSolutionGQL = open("graphql/official_solution.gql").read()
solutionGQL = open("graphql/solution.gql").read()
playgroundGQL = open("graphql/playground.gql").read()


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
                    code = x.code.replace("&", "&amp;").replace("<", "&lt;")
                    return f"<pre>\n{code}</pre>"
            if playground_data.allPlaygroundCodes:
                x = playground_data.allPlaygroundCodes[0]
                code = x.code.replace("&", "&amp;").replace("<", "&lt;")
                return f"<pre>{x.langSlug}\n{code}</pre>"
        except Exception as e:
            print(f"Error fetching playground for UUID {uuid}: {e}", file=sys.stderr)
        return iframe_tag  # Return the original iframe if an error occurs

    # Replace all iframe tags with the corresponding C++ code
    return re.sub(r"<iframe[^>]*></iframe>", iframe_replacer, markdown_content)


def process_content(content):
    """Apply common processing to content"""
    # Replace all $$expr$$ into $expr$
    content = re.sub(r"\$\$(.*?)\$\$", r"$\1$", content)
    # Replace iframes with C++ code
    content = replace_iframes_with_code(content)
    return content


def parse_problem_link(link: str):
    """Parse a problem link and return the slug and topicId"""
    slug = re.search(r"(?<=problems/)[^/]+", link)
    if slug:
        slug = slug.group(0)
    topicId = re.search(r"(?<=solutions/)[^/]+", link)
    if topicId:
        topicId = topicId.group(0)
    return slug, topicId


def get_problem_content(problem_link):
    """Process a question link and return the content without modifying global variables"""
    body_content = ""
    slug, topicId = parse_problem_link(problem_link)
    if not slug:
        print(f"Invalid link: {problem_link}", file=sys.stderr)
        return None, None, None

    x = fetch_question(slug).data.question

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
        truncate_with = "Solution Article"
        if truncate_with in content:
            i = content.index(truncate_with) + len(truncate_with)
            content = content[i:]
        if y.isSerialized:
            # replace all escaped characters with unescaped one
            content = bytes(content, "utf-8").decode("unicode_escape")
        content = mdformat.text(content)
        # Escape html characters that are in code blocks like ```
        content = markdown.markdown(content)
        # Replace relative links with absolute links
        content = content.replace(
            "../Figures", f"https://leetcode.com/problems/{slug}/Figures"
        )
        # Increase the level of the headings
        content = re.sub(
            r"<h([1-5])>(.*?)</h\1>",
            lambda m: f"<h{str(int(m.group(1)) + 1)}>{m.group(2)}</h{str(int(m.group(1)) + 1)}>",
            content,
        )
        sol += "\n<h3>Solution</h3>\n\n"
        sol += content

    if sol:
        body_content += sol

    return body_content, x.title, slug


def save_problem_to_file(problem_content, title, slug):
    """Save problem content to an individual file"""
    if not problem_content:
        return False

    # Create a safe filename from the title
    safe_filename = f"{slug}.html"
    filepath = os.path.join(output_dir, safe_filename)

    with open(filepath, "w") as f:
        f.write(problem_content)

    print(f"Saved problem '{title}' to {filepath}")
    return True


def concatenate_problem_files(output_file="blind_75.html", include_sections=True):
    """Concatenate all HTML problem files into a single file"""
    combined_content = ""

    # If we need to include sections, read the original file to get section headers
    section_headers = {}
    if include_sections:
        try:
            with open("question_links.txt") as filename:
                links = filename.read().strip().split("\n")

            current_section = None
            for line in links:
                if not line:
                    continue
                if line[0] == "~":
                    current_section = line[1:].strip()
                    section_headers[current_section] = []
                elif current_section is not None and "/" in line:
                    slug = re.search(r"(?<=problems/)[^/]+", line)
                    if slug:
                        section_headers[current_section].append(slug.group(0))
        except FileNotFoundError:
            print(
                "Warning: question_links.txt not found, sections will not be included."
            )
            include_sections = False

    # Get all HTML files in the problems directory
    problem_files = set([f for f in os.listdir(output_dir) if f.endswith(".html")])

    if not problem_files:
        print("No problem files found to concatenate.")
        return False

    # If including sections, organize by section
    if include_sections and section_headers:
        # Track which files have been added
        added_files = set()

        for section, slugs in section_headers.items():
            # Add section header
            combined_content += f"\n<h1>{section}</h1>\n\n"

            # Add all problems in this section
            for slug in slugs:
                filename = f"{slug}.html"
                if filename not in problem_files:
                    continue
                filename = os.path.join(output_dir, filename)
                with open(filename, "r") as f:
                    combined_content += f.read() + "\n\n"

        # Add any remaining files that weren't part of a section
        remaining_files = [f for f in problem_files if f not in added_files]
        if remaining_files:
            combined_content += "\n<h1>Other Problems</h1>\n\n"
            for file in remaining_files:
                filepath = os.path.join(output_dir, file)
                with open(filepath, "r") as f:
                    content = f.read()

                # Extract just the body content
                body_match = re.search(r"<body>(.*?)</body>", content, re.DOTALL)
                if body_match:
                    combined_content += body_match.group(1) + "\n\n"

    else:
        # Just add all files in sorted order
        for filename in sorted(problem_files):
            filepath = os.path.join(output_dir, filename)
            with open(filepath, "r") as f:
                content = f.read()
                combined_content += content + "\n\n"

    # Wrap the combined content in HTML
    html_content = html_wrapper.replace("BODY_CONTENT", combined_content)

    with open(output_file, "w") as filename:
        filename.write(html_content)

    print(f"Successfully concatenated {len(problem_files)} problems into {output_file}")
    return True


def process_section_line(line):
    """Process section headers (lines starting with ~)"""
    return f"\n<h1>{line[1:]}</h1>\n\n"


def main():
    parser = argparse.ArgumentParser(description="LeetCode problem fetcher")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--link", help="Fetch a specific problem by providing its link")
    group.add_argument(
        "--all",
        action="store_true",
        help="Generate all ungenerated problems from question_links.txt unless --force is enabled",
    )
    group.add_argument(
        "--concatenate",
        action="store_true",
        help="Concatenate all problem files into one HTML file",
    )
    parser.add_argument(
        "--output",
        default="blind_75.html",
        help="Output file for concatenation (default: blind_75.html)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force generation of all the problems even previous genereted ones",
    )

    args = parser.parse_args()

    if args.link:
        # Process a single problem link
        print(f"Fetching the problem: {args.link}")
        content, title, slug = get_problem_content(args.link)
        if content:
            content = process_content(content)
            save_problem_to_file(content, title, slug)
        else:
            print("Failed to fetch problem content.")

    elif args.all:
        # Process all problems from question_links.txt
        try:
            with open("question_links.txt") as f:
                links = f.read().strip()
            question_links = links.split("\n")

            for line in question_links:
                if not line:
                    continue
                try:
                    if line[0] == "~":
                        # This is a section header - we'll just print it but not save it
                        print(f"Found section: {line[1:].strip()}")
                    else:
                        slug, _ = parse_problem_link(line)
                        filepath = os.path.join(output_dir, f"{slug}.html")
                        if os.path.exists(filepath):
                            if not args.force:
                                continue
                            print("Overriding existing problem:", slug)
                        else:
                            print("Generating problem:", slug)
                        content, title, slug = get_problem_content(line)
                        if content:
                            content = process_content(content)
                            save_problem_to_file(content, title, slug)
                    print("------------------------------")
                except Exception as e:
                    print(f"Error processing line {line}: {e}", file=sys.stderr)
                    continue

        except FileNotFoundError:
            print("Error: question_links.txt not found.")
            sys.exit(1)

    elif args.concatenate:
        # Concatenate all problem files
        concatenate_problem_files(args.output)


if __name__ == "__main__":
    main()

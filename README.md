This repo uses LeetCode's GraphQL API and only includes the [Blind 75](https://www.teamblind.com/post/New-Year-Gift---Curated-List-of-Top-75-LeetCode-Questions-to-Save-Your-Time-OaM1orEU). The problems are extracted to HTML files that can be later converted to PDF files or a single file containing all the problems.

Feel free to submit a PR to include other lists e.g topic specific lists.

### Usage

This is how to use the script `export_questions.py`:

```
usage: export_questions.py [-h] (--link LINK | --all | --concatenate) [--output OUTPUT] [--force] [--llm LLM]

LeetCode problem fetcher

options:
  -h, --help         show this help message and exit
  --link LINK        Fetch a specific problem by providing its link
  --all              Generate all ungenerated problems from question_links.txt unless --force is enabled
  --concatenate      Concatenate all problem files into one HTML file
  --output OUTPUT    Output file for concatenation (default: output.html)
  --force            Force generation of all the problems even previous genereted ones
  --llm=<true/false> Use LLMs to finetune the result? (true/false)
```

### Building PDF

The main goal for this repo is to generate a well structured form then you can use any tool to convert it to a PDF. Each problem is extracted to a separate HTML file in the directory `problems/` and an LLM (i.e. Gemini Flash 2.0) is used to finetune the result and add a solution if it doesn't exist.

Use a virtual Python environment and install the requirements:

```python
virtualenv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Now you can use one of the Makefile scripts:

- `make all` to generate an HTML file for all the problems that doesn't have an HTML in `problems/` directory.
  - If you want to overwrite an existing HTML you can use `python export-problems.py --link <problem-linl>`
- `make output.html` to generate a single HTML file for all the problems.
- `make` or `make output.pdf` to generate a single PDF file for all the problems.
  - You need to install `pandoc` and `weasyprint` tools first if you want to generate the PDF.

### Updating questions

Add the new question link in the file `question_links.txt` and run `export_questions.py` python script.

To get all questions in a LeetCode list, visit a LeetCode URL with problem links visible on the page e.g `https://leetcode.com/list/xi4ci4ig/`. Open up the dev console and run the following code. Make sure all problem links are visible e.g extend list view > 50 to show all problem links if needed.

```
var links = document.getElementsByTagName('a');
var all_links = Array.prototype.slice.call(links);
var problems_str = "";
all_links.forEach(function(val) {
    if (val.href.includes('/problems/') && !val.href.includes('/solution')) {
        problems_str = problems_str.concat(`${val.href}\n`)
    }
});
console.log(problems_str)
```

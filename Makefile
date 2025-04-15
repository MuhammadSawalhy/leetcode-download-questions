output.pdf: output.html
	pandoc output.html -o output.pdf --pdf-engine=weasyprint --toc

output.html: all
	python export_questions.py --concatenate --output output.html

all: question_links.txt export_questions.py
	python export_questions.py --all
